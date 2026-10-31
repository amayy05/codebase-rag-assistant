
import requests

chunks = [
    "IntelliCharge helps EV drivers find charging stations. Drivers can join a virtual queue at a",
    "queue at a station. The system estimates waiting time from queue information. The backend stores",
    "The backend stores station and queue details."
]

response = requests.post(
    "http://localhost:11434/api/embed",
    json={
        "model": "embeddinggemma",
        "input": chunks
    },
    timeout=120
)

response.raise_for_status()

data = response.json()
embeddings = data["embeddings"]

print("Number of chunks:", len(chunks))
print("Number of embeddings:", len(embeddings))

for i, embedding in enumerate(embeddings, start=1):
    print(f"Chunk {i}: {len(embedding)} numbers")
