# Codebase RAG Assistant

A local, privacy-first Codebase Retrieval-Augmented Generation (RAG) assistant that indexes repository code into ChromaDB using local embedding models and answers architectural and implementation questions via Ollama LLMs.

---

## 🚀 Features

- **100% Local & Private**: Runs completely offline using Ollama (`embeddinggemma` & `llama3.2`) with no external API keys required.
- **Codebase Ingestion**: Automatically scans repositories, chunks source code with line tracking, and generates vector embeddings.
- **Semantic Code Search**: Search code semantically using natural language queries with optional scope filtering (e.g., backend, full project).
- **RAG-Powered Q&A**: Asks grounded technical questions to local LLMs with context citations directly from indexed code chunks.
- **Vector Storage**: Persistent local vector storage powered by ChromaDB.

---

## 🛠️ Tech Stack

- **Python** (>= 3.12)
- **ChromaDB**: Local persistent vector database
- **Ollama**: Local LLM and embedding server
  - Embedding Model: `embeddinggemma`
  - Generation Model: `llama3.2`
- **uv**: Fast Python package manager

---

## 📋 Prerequisites

1. Install [Ollama](https://ollama.com/) and ensure it is running:
   ```bash
   ollama serve
   ```
2. Pull the required models:
   ```bash
   ollama pull embeddinggemma
   ollama pull llama3.2
   ```

---

## ⚙️ Setup & Installation

Clone the repository and install dependencies using `uv` or `pip`:

```bash
# Using uv (recommended)
uv sync

# Or using pip in a virtual environment
python -m venv .venv
# On Windows:
.venv\Scripts\activate
# On Linux/macOS:
# source .venv/bin/activate
pip install chromadb requests
```

---

## 📖 Usage

### 1. Ingest Codebase
Configure the target repository path in `ingest.py` and run:
```bash
python ingest.py
```

### 2. Search Codebase Semantically
Perform vector searches across indexed files:
```bash
python search_codebase.py
```

### 3. Ask Questions with Local RAG
Query the codebase with strict grounded prompt templates:
```bash
python ask_codebase.py
```

---

## 📄 License

MIT License.
