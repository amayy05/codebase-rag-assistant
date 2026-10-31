
import requests
import chromadb

# Connect to the vector database
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


question = input("Ask a question about IntelliCharge: ")

# Retrieve relevant chunks
question_embedding = get_embedding(question)

results = collection.query(
    query_embeddings=[question_embedding],
    n_results=2
)

context = "\n".join(results["documents"][0])

# Ask the local LLM to answer using the retrieved context



prompt = f"""
You are a codebase question-answering assistant.

Answer using only the information in the provided context.

Rules:
1. Every factual claim must be supported by the context.
2. Do not assume how the system works based on common practices.
3. Do not invent features, algorithms, business rules, or benefits.
4. If the context does not contain enough information, say so.
5. Clearly separate confirmed facts from missing information.

Context:
{context}

Question:
{question}

Answer:
"""



response = requests.post(
    "http://localhost:11434/api/generate",
    json={
        "model": "llama3.2",
        "prompt": prompt,
        "stream": False
    },
    timeout=120
)

response.raise_for_status()
answer = response.json()["response"]

print("\nAnswer:", answer)
print("\nRetrieved context:\n", context)
