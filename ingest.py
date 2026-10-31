
from pathlib import Path

import chromadb
import requests

# ---------------- CONFIGURATION ----------------

REPO_PATH = Path(
    r"C:\Users\amayn\OneDrive\Desktop\intillichargee"
)

DB_PATH = "./chroma_db"
COLLECTION_NAME = "intellicharge_codebase_v2"

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


# ---------------- FIND SOURCE FILES ----------------

def find_source_files():
    source_files = []

    for path in REPO_PATH.rglob("*"):
        if not path.is_file():
            continue

        relative_parts = path.relative_to(REPO_PATH).parts

        if any(part in IGNORED_DIRS for part in relative_parts):
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

        # Preserve indentation and line breaks.
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

# New collection: existing index remains unchanged.
collection = client.get_or_create_collection(
    name=COLLECTION_NAME
)


# ---------------- INDEX SOURCE CODE ----------------

source_files = find_source_files()
batch = []
processed_chunks = 0


def save_batch(items):
    if not items:
        return 0

    texts = [item["text"] for item in items]
    embeddings = get_embeddings(texts)

    collection.upsert(
        ids=[item["id"] for item in items],
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


print("Files found:", len(source_files))
print("Starting code-aware indexing...\n")

for file_path in source_files:
    try:
        content = file_path.read_text(
            encoding="utf-8",
            errors="replace",
        )
    except OSError as error:
        print("Skipping unreadable file:", file_path, error)
        continue

    relative_path = str(file_path.relative_to(REPO_PATH))

    for chunk_number, chunk in enumerate(chunk_code(content)):
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

            print("Chunks indexed:", processed_chunks)

if batch:
    processed_chunks += save_batch(batch)

print("\nIndexing complete!")
print("Chunks processed this run:", processed_chunks)
print("Chunks in new collection:", collection.count())
print("Collection:", COLLECTION_NAME)
