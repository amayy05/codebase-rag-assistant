
import requests
import chromadb

# Connect to the same local database
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_collection(
    name="intellicharge_knowledge_gemma"
)


def get_embedding(text):
    response = requests.post(
        "http://localhost:11434/api/embed",
        json={
            "model": "embeddinggemma",
            "input": text
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["embeddings"][0]


# Ask a question
question = "How does IntelliCharge manage waiting lines?"

# Convert the question into a vector
question_embedding = get_embedding(question)

# Find the most similar stored chunks
results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

print("\nQuestion:", question)
print("\nRelevant chunks:")

for document in results["documents"][0]:
    print("-", document)
