
import requests
import chromadb

OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "embeddinggemma"
CHAT_MODEL = "llama3.2"

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(name="intellicharge_codebase_v2")

BACKEND_FILES = [
    r"backend\app\api\queue.py",
    r"backend\app\services\queue_engine.py",
    r"backend\app\models\queue_entry.py",
    r"backend\app\schemas\queue.py",
]


def get_embedding(text):
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


def retrieve_code(question, scope):
    options = {
        "query_embeddings": [get_embedding(question)],
        "n_results": min(8, collection.count()),
    }

    if scope == "backend":
        options["where"] = {"source": {"$in": BACKEND_FILES}}

    results = collection.query(**options)

    context_parts = []

    for document, metadata in zip(
        results["documents"][0],
        results["metadatas"][0],
    ):
        source = metadata["source"]
        start = metadata["start_line"]
        end = metadata["end_line"]

        context_parts.append(
            f"FILE: {source}\n"
            f"LINES: {start}-{end}\n"
            f"CODE:\n{document}"
        )

    return "\n\n--- SOURCE CHUNK ---\n\n".join(context_parts)


def generate_answer(question, context):
    prompt = f"""
You are a helpful coding assistant explaining the IntelliCharge project.

Answer the user's question using ONLY the source code provided below.

Rules:
1. Explain in simple language.
2. Do not invent functions, files, algorithms, or behavior.
3. If the provided code does not contain enough information, say so.
4. Cite relevant evidence using this format:
   [File: path/to/file.py, lines 10-25]
5. Clearly distinguish confirmed implementation details from assumptions.
6. Explain the flow step by step when appropriate.

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
    print("=== IntelliCharge Codebase RAG Assistant ===\n")

    question = input("Ask a question: ").strip()

    if not question:
        print("Please enter a question.")
        return

    scope = input("Search scope ('backend' or 'all'): ").strip().lower()

    if scope not in {"backend", "all"}:
        print("Please enter 'backend' or 'all'.")
        return

    if collection.count() == 0:
        print("The index is empty. Run ingest.py first.")
        return

    try:
        print("\nSearching the codebase...")

        context = retrieve_code(question, scope)

        if not context:
            print("No relevant source code was found.")
            return

        print("Generating an answer with the local LLM...\n")

        answer = generate_answer(question, context)

        print("=" * 65)
        print("ANSWER")
        print("=" * 65)
        print(answer)

    except requests.RequestException as error:
        print("Ollama request failed:", error)
        print("Check that Ollama is running and the required models exist.")

    except Exception as error:
        print("Something went wrong:", error)


if __name__ == "__main__":
    main()
