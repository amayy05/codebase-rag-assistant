
import requests
import chromadb

OLLAMA_URL = "http://localhost:11434"
EMBEDDING_MODEL = "embeddinggemma"

client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="intellicharge_codebase_v2"
)

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


def main():
    print("=== IntelliCharge Codebase Search ===\n")

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
        print("Index is empty. Run ingest.py first.")
        return

    try:
        question_embedding = get_embedding(question)

        options = {
            "query_embeddings": [question_embedding],
            "n_results": min(5, collection.count()),
        }

        if scope == "backend":
            options["where"] = {
                "source": {
                    "$in": BACKEND_FILES
                }
            }

        results = collection.query(**options)

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]
        distances = results["distances"][0]

        print("\nRelevant source code:\n")

        if not documents:
            print("No matching code chunks found.")
            return

        for index, (document, metadata, distance) in enumerate(
            zip(documents, metadatas, distances),
            start=1,
        ):
            print("=" * 65)
            print(f"Result {index}")
            print("File:", metadata["source"])
            print(
                f"Lines: {metadata['start_line']}"
                f"-{metadata['end_line']}"
            )
            print("Distance:", round(distance, 4))
            print("\nCode:\n")
            print(document)
            print()

    except requests.RequestException as error:
        print("Ollama request failed:", error)

    except Exception as error:
        print("Search failed:", error)


if __name__ == "__main__":
    main()
