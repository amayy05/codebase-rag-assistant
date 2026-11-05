
from pathlib import Path
from urllib.parse import urlparse
import hashlib
import subprocess
import sys

import chromadb
import requests


# ---------------- CONFIGURATION ----------------

PROJECT_DIR = Path(__file__).resolve().parent

DEFAULT_REPO_PATH = Path(
    r"C:\Users\amayn\OneDrive\Desktop\intillichargee"
)

REPOS_DIR = PROJECT_DIR / "repos"
DB_PATH = str(PROJECT_DIR / "chroma_db")

DEFAULT_COLLECTION_NAME = "intellicharge_codebase_v2"

OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "embeddinggemma"

BATCH_SIZE = 16
CHUNK_LINES = 50
OVERLAP_LINES = 8

ALLOWED_EXTENSIONS = {
    ".py", ".js", ".jsx", ".ts", ".tsx",
    ".html", ".css", ".json", ".md"
}

IGNORED_DIRS = {
    ".git", "node_modules", ".venv",
    "__pycache__", ".pytest_cache",
    "dist", "build"
}


# ---------------- GITHUB REPOSITORY SETUP ----------------

def prepare_repository():

    # No URL means use the existing IntelliCharge repository.
    if len(sys.argv) < 2:
        print("Using default IntelliCharge repository.")
        return DEFAULT_REPO_PATH, DEFAULT_COLLECTION_NAME

    repo_url = sys.argv[1].strip()

    parsed_url = urlparse(repo_url)

    if parsed_url.netloc.lower() != "github.com":
        raise ValueError("Please provide a valid GitHub HTTPS URL.")

    if parsed_url.scheme != "https":
        raise ValueError("Use an HTTPS GitHub URL.")

    # Extract owner and repository name from the URL.
    parts = parsed_url.path.strip("/").split("/")

    if len(parts) < 2:
        raise ValueError("GitHub URL must contain owner and repository.")

    owner = parts[0]
    repo_name = parts[1].removesuffix(".git")

    # Hash the URL so different repositories don't collide.
    repo_hash = hashlib.sha1(
        repo_url.encode("utf-8")
    ).hexdigest()[:8]

    repo_folder_name = f"{owner}_{repo_name}_{repo_hash}"

    repo_path = REPOS_DIR / repo_folder_name

    # Create repos/ if it doesn't exist.
    REPOS_DIR.mkdir(parents=True, exist_ok=True)

    # Clone the GitHub repository if not already cloned.
    if not repo_path.exists():

        print(f"\nCloning GitHub repository: {repo_url}")

        subprocess.run(
            [
                "git",
                "clone",
                "--depth",
                "1",
                repo_url,
                str(repo_path),
            ],
            check=True,
        )

    else:
        print("\nRepository already cloned locally.")
        print("Using:", repo_path)

    # Create a separate Chroma collection for this repository.
    collection_name = (
        f"repomind_{repo_name[:35]}_{repo_hash}"
    ).lower()

    collection_name = collection_name.replace("-", "_")

    return repo_path, collection_name


# ---------------- FIND SOURCE FILES ----------------

def find_source_files():

    source_files = []

    for path in REPO_PATH.rglob("*"):

        if not path.is_file():
            continue

        relative_parts = path.relative_to(REPO_PATH).parts

        if any(
            part in IGNORED_DIRS
            for part in relative_parts
        ):
            continue

        if path.suffix.lower() not in ALLOWED_EXTENSIONS:
            continue

        if path.stat().st_size > 1_000_000:
            print("Skipping large file:", path.name)
            continue

        source_files.append(path)

    return sorted(source_files)


# ---------------- SPLIT CODE INTO LINE CHUNKS ----------------

def chunk_code(content):

    lines = content.splitlines()

    if not lines:
        return []

    chunks = []
    start = 0

    while start < len(lines):

        end = min(start + CHUNK_LINES, len(lines))

        chunk_text = "\n".join(lines[start:end])

        chunks.append({
            "text": chunk_text,
            "start_line": start + 1,
            "end_line": end,
        })

        if end == len(lines):
            break

        start = end - OVERLAP_LINES

    return chunks


# ---------------- CREATE EMBEDDINGS ----------------

def get_embeddings(texts):

    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": texts,
        },
        timeout=180,
    )

    response.raise_for_status()

    return response.json()["embeddings"]


# ---------------- CONNECT TO CHROMADB ----------------

client = chromadb.PersistentClient(path=DB_PATH)


# ---------------- INDEX SOURCE CODE ----------------

def main():

    global REPO_PATH
    global COLLECTION_NAME
    global collection

    REPO_PATH, COLLECTION_NAME = prepare_repository()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    print("\nRepository:", REPO_PATH)
    print("Collection:", COLLECTION_NAME)

    source_files = find_source_files()

    batch = []
    processed_chunks = 0

    def save_batch(items):

        if not items:
            return 0

        texts = [
            item["text"]
            for item in items
        ]

        embeddings = get_embeddings(texts)

        collection.upsert(
            ids=[
                item["id"]
                for item in items
            ],
            documents=texts,
            embeddings=embeddings,
            metadatas=[
                {
                    "source": item["source"],
                    "chunk": item["chunk"],
                    "start_line": item["start_line"],
                    "end_line": item["end_line"],
                }
                for item in items
            ],
        )

        return len(items)

    print("\nFiles found:", len(source_files))
    print("Starting code-aware indexing...\n")

    for file_path in source_files:

        try:
            content = file_path.read_text(
                encoding="utf-8",
                errors="replace",
            )

        except OSError as error:
            print(
                "Skipping unreadable file:",
                file_path,
                error,
            )
            continue

        relative_path = str(
            file_path.relative_to(REPO_PATH)
        ).replace("\\", "/")

        for chunk_number, chunk in enumerate(
            chunk_code(content)
        ):

            batch.append({
                "id": f"{relative_path}::chunk_{chunk_number}",
                "source": relative_path,
                "chunk": chunk_number,
                "start_line": chunk["start_line"],
                "end_line": chunk["end_line"],
                "text": chunk["text"],
            })

            if len(batch) >= BATCH_SIZE:

                processed_chunks += save_batch(batch)

                batch.clear()

                print(
                    "Chunks indexed:",
                    processed_chunks,
                )

    if batch:
        processed_chunks += save_batch(batch)

    print("\nIndexing complete!")
    print("Chunks processed this run:", processed_chunks)
    print("Chunks in collection:", collection.count())
    print("Collection:", COLLECTION_NAME)


if __name__ == "__main__":
    main()
