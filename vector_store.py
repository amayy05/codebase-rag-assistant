
import requests
import chromadb

# Connect to Ollama
OLLAMA_URL = "http://localhost:11434/api/embed"
EMBEDDING_MODEL = "embeddinggemma"

# Create a persistent ChromaDB database
client = chromadb.PersistentClient(path="./chroma_db")

collection = client.get_or_create_collection(
    name="intellicharge_knowledge_gemma"
)

chunks = [
    "IntelliCharge helps EV drivers find charging stations. Drivers can join a virtual queue at a",
    "queue at a station. The system estimates waiting time from queue information. The backend stores",
    "The backend stores station and queue details."
]

ids = ["chunk_1", "chunk_2", "chunk_3"]


def get_embeddings(texts):
    response = requests.post(
        OLLAMA_URL,
        json={
            "model": EMBEDDING_MODEL,
            "input": texts
        },
        timeout=120
    )

    response.raise_for_status()
    return response.json()["embeddings"]


embeddings = get_embeddings(chunks)

collection.upsert(
    ids=ids,
    documents=chunks,
    embeddings=embeddings
)

print("Chunks stored:", collection.count())
print("Embedding dimensions:", len(embeddings[0]))
print("Embedding model:", EMBEDDING_MODEL)
