
import chromadb

client = chromadb.PersistentClient(path="./chroma_db")
collection = client.get_collection(
    name="intellicharge_codebase"
)

# Find a known backend file directly from stored metadata.
data = collection.get(include=["metadatas"])

backend_sources = sorted({
    metadata["source"]
    for metadata in data["metadatas"]
    if metadata
    and metadata.get("source", "").replace("\\", "/").startswith("backend/")
})

print("Backend source paths found:", len(backend_sources))

print("\nFirst 10 backend paths:")
for source in backend_sources[:10]:
    print(repr(source))

if backend_sources:
    known_source = backend_sources[0]

    print("\nTesting exact metadata match:", repr(known_source))

    exact_match = collection.get(
        where={"source": known_source},
        limit=3,
        include=["metadatas"]
    )
    print("Exact-match results:", len(exact_match["metadatas"]))

    print("\nTesting backend contains filter:")
    try:
        filtered = collection.get(
            where={"source": {"$contains": "backend"}},
            limit=3,
            include=["metadatas"]
        )
        print("Contains results:", len(filtered["metadatas"]))
    except Exception as error:
        print("Filter error:", error)
