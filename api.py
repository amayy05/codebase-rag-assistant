
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from ask_codebase import (
    client,
    get_collection,
    retrieve_code,
    generate_answer,
)

app = FastAPI(
    title="RepoMind API",
    description="Local-first Codebase RAG Assistant",
    version="1.0.0",
)


class AskRequest(BaseModel):
    repo_name: str = "intellicharge"
    question: str
    scope: str = "all"


class AskResponse(BaseModel):
    repository: str
    question: str
    answer: str


@app.get("/")
def root():
    return {
        "message": "RepoMind API is running",
        "status": "healthy",
    }


@app.get("/repositories")
def list_repositories():
    collections = client.list_collections()

    repositories = [
        collection.name
        if hasattr(collection, "name")
        else collection
        for collection in collections
    ]

    return {
        "repositories": repositories,
        "count": len(repositories),
    }


@app.post("/ask", response_model=AskResponse)
def ask_codebase(request: AskRequest):
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty.",
        )

    if request.scope not in {"all", "backend"}:
        raise HTTPException(
            status_code=400,
            detail="Scope must be 'all' or 'backend'.",
        )

    collection = get_collection(request.repo_name)

    if collection is None:
        raise HTTPException(
            status_code=404,
            detail=f"Repository '{request.repo_name}' not found.",
        )

    if collection.count() == 0:
        raise HTTPException(
            status_code=400,
            detail="Repository index is empty.",
        )

    try:
        context = retrieve_code(
            question=question,
            scope=request.scope,
            collection=collection,
            repo_name=request.repo_name,
        )

        if not context:
            raise HTTPException(
                status_code=404,
                detail="No relevant source code found.",
            )

        answer = generate_answer(
            question=question,
            context=context,
            repo_name=request.repo_name,
        )

        return AskResponse(
            repository=request.repo_name,
            question=question,
            answer=answer,
        )

    except HTTPException:
        raise

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=str(error),
        )
