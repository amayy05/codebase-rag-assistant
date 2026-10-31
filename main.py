
def chunk_text(text, chunk_size=15, overlap=3):
    words = text.split()
    chunks = []
    start = 0

    while start < len(words):
        end = min(start + chunk_size, len(words))
        chunk = " ".join(words[start:end])
        chunks.append(chunk)

        if end == len(words):
            break

        start = end - overlap

    return chunks


sample_text = (
    "IntelliCharge helps EV drivers find charging stations. "
    "Drivers can join a virtual queue at a station. "
    "The system estimates waiting time from queue information. "
    "The backend stores station and queue details."
)

chunks = chunk_text(sample_text)

for i, chunk in enumerate(chunks, start=1):
    print(f"\nChunk {i}:")
    print(chunk)
