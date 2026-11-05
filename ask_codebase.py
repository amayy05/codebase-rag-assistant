import sys
import requests
import chromadb

OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "embeddinggemma"
CHAT_MODEL = "llama3.2"

client = chromadb.PersistentClient(path="./chroma_db")

DEFAULT_COLLECTION = "intellicharge_codebase_v2"

BACKEND_FILES = [
    r"backend\app\api\queue.py",
    r"backend\app\services\queue_engine.py",
    r"backend\app\models\queue_entry.py",
    r"backend\app\schemas\queue.py",
]


def get_collection(repo_name=None):
    """Select the Chroma collection for the requested repository."""

    if not repo_name:
        return client.get_collection(name=DEFAULT_COLLECTION)

    repo_name = repo_name.lower().replace("-", "_")

    collections = client.list_collections()

    collection_names = [
        item.name if hasattr(item, "name") else item
        for item in collections
    ]

    matching_collections = [
        name
        for name in collection_names
        if name.startswith(f"repomind_{repo_name}_")
    ]

    if not matching_collections:
        print(f"No indexed repository found for: {repo_name}")
        print("\nAvailable collections:")

        for name in collection_names:
            print(f" - {name}")

        return None

    if len(matching_collections) > 1:
        print("Multiple matching repositories found:")

        for name in matching_collections:
            print(f" - {name}")

        print("Please use a more specific repository name.")
        return None

    return client.get_collection(name=matching_collections[0])


def get_embedding(text):
    """Convert the user's question into a vector embedding."""

    response = requests.post(
        f"{OLLAMA_URL}/api/embed",
        json={
            "model": EMBEDDING_MODEL,
            "input": text,
        },
        timeout=120,
    )

    response.raise_for_status()

    return response.json()["embeddings"][0]


def retrieve_code(question, scope, collection, repo_name):
    """Retrieve relevant source-code chunks from Chroma."""

    if collection.count() == 0:
        return ""

    options = {
        "query_embeddings": [get_embedding(question)],
        "n_results": min(8, collection.count()),
    }

    # Backend filtering is currently specific to IntelliCharge.
    if scope == "backend" and repo_name.lower() in {
        "intellicharge",
        "intillichargee",
    }:
        options["where"] = {
            "source": {"$in": BACKEND_FILES}
        }

    results = collection.query(**options)

    context_parts = []

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]

    for document, metadata in zip(documents, metadatas):
        if not document or not metadata:
            continue

        source = metadata.get("source", "Unknown source")
        start = metadata.get("start_line", "Unknown")
        end = metadata.get("end_line", "Unknown")

        context_parts.append(
            f"FILE: {source}\n"
            f"LINES: {start}-{end}\n"
            f"CODE:\n{document}"
        )

    return "\n\n--- SOURCE CHUNK ---\n\n".join(context_parts)


def generate_answer(question, context, repo_name):
    """Generate a source-grounded answer using the local LLM."""

    prompt = f"""
You are RepoMind, a codebase analysis assistant.

Repository: {repo_name}

Answer the user's question using ONLY the retrieved source code.

STRICT RULES:
1. Do not invent functions, files, classes, or behavior.
2. Every implementation claim must be supported by retrieved code.
3. Cite evidence using the exact FILE and LINES metadata provided.
4. Never invent file paths or line numbers.
5. If evidence is insufficient, explicitly say:
   "The retrieved source code does not provide enough information."
6. Distinguish confirmed behavior from reasonable inference.
7. Explain code in beginner-friendly language.
8. Do not claim to have analyzed files that were not retrieved.
9. Do not cite example code as actual repository implementation.
10. Do not claim that a method or feature exists unless shown in context.

CITATION FORMAT:
[File: exact/path/from/context.py, lines 10-25]

USER QUESTION:
{question}

RETRIEVED SOURCE CODE:
{context}

ANSWER:
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": CHAT_MODEL,
            "prompt": prompt,
            "stream": False,
        },
        timeout=180,
    )

    response.raise_for_status()

    return response.json()["response"].strip()


def main():
    repo_name = sys.argv[1] if len(sys.argv) > 1 else None

    if not repo_name:
        repo_name = "intellicharge"

    collection = get_collection(repo_name)

    if collection is None:
        return

    print("=" * 65)
    print("RepoMind Codebase RAG Assistant")
    print("=" * 65)

    print(f"Repository: {repo_name}")
    print(f"Collection: {collection.name}")
    print(f"Indexed chunks: {collection.count()}")
    print()

    question = input("Ask a question: ").strip()

    if not question:
        print("Please enter a question.")
        return

    scope = input(
        "Search scope ('backend' or 'all'): "
    ).strip().lower()

    if scope not in {"backend", "all"}:
        print("Please enter 'backend' or 'all'.")
        return

    if collection.count() == 0:
        print("The index is empty. Run ingest.py first.")
        return

    try:
        print("\nSearching the codebase...")

        context = retrieve_code(
            question=question,
            scope=scope,
            collection=collection,
            repo_name=repo_name,
        )

        if not context:
            print("No relevant source code was found.")
            return

        print("\nRetrieved source code:")
        print("-" * 65)
        print(context)
        print("-" * 65)

        print("\nGenerating an answer with the local LLM...\n")

        answer = generate_answer(
            question=question,
            context=context,
            repo_name=repo_name,
        )

        print("=" * 65)
        print("ANSWER")
        print("=" * 65)

        print(answer)

    except requests.RequestException as error:
        print("\nOllama request failed:", error)
        print("Check that Ollama is running and the required models exist.")

    except Exception as error:
        print("\nSomething went wrong:", error)


if __name__ == "__main__":
    main()