"""ONEAD Assistant IA — Backend API (FastAPI) pour le frontend React + TypeScript.

Lance :  uvicorn api:app --host 0.0.0.0 --port 8000 --reload
Le frontend Vite proxifie /api et /files vers ce serveur en dev.

Endpoints :
  GET  /api/health
  GET  /api/manifest
  GET  /api/documents
  GET  /api/drh
  POST /api/chat            -> JSON { answer, sources, refusal, meta }
  POST /api/chat/stream     -> SSE (event: token / event: done)
  GET  /files/docs/{nom}   -> PDF (servi depuis data/raw)
"""
from functools import lru_cache
from pathlib import Path
from typing import Any, Optional
from urllib.parse import quote

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

BASE_DIR = Path(__file__).resolve().parent
RAW_DIR = BASE_DIR / "data" / "raw"

app = FastAPI(title="ONEAD Assistant IA — API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    top_k: Optional[int] = None


class Source(BaseModel):
    name: str
    page: str
    url: str
    label: str
    excerpt: str = ""


class ChatResponse(BaseModel):
    answer: str
    sources: list[Source]
    refusal: bool
    meta: dict[str, Any] = {}


@lru_cache(maxsize=1)
def _rag():
    """Singleton LLM + ChromaDB (chargement paresseux pour un /health rapide)."""
    from chat_context import init_rag

    return init_rag()


def _answer_sync(question: str, top_k: Optional[int] = None) -> ChatResponse:
    from chat_context import (
        build_context,
        build_prompt,
        is_refusal,
        log_unanswered,
        search_with_scores,
    )
    from src.config import DRH_CONTACT, MAX_SOURCES, REFUSAL_MESSAGE, TOP_K

    try:
        llm, vectordb = _rag()
    except Exception as exc:  # credentials / réseau Azure indisponibles
        raise HTTPException(status_code=503, detail=f"Base RAG indisponible : {exc}")

    k = top_k or TOP_K
    results, scored = search_with_scores(vectordb, question, k=k)
    context = build_context(results)
    prompt = build_prompt(context, question)

    # Réponse complète non-streamée (le streaming passe par /api/chat/stream)
    text_parts: list[str] = []
    for chunk in llm.stream(prompt):
        content = getattr(chunk, "content", "") or ""
        if content:
            text_parts.append(content)
    answer = "".join(text_parts).strip()

    refusal = (not results) or is_refusal(answer)
    if refusal and not is_refusal(answer):
        answer = REFUSAL_MESSAGE
    if refusal:
        log_unanswered(question, scored)

    sources: list[Source] = []
    if not refusal:
        seen: set[tuple[str, str]] = set()
        for doc in results:
            name = str(doc.metadata.get("source") or "")
            page = str(doc.metadata.get("page") or "?")
            if not name or (name, page) in seen:
                continue
            seen.add((name, page))
            if page != "?":
                url = f"/files/docs/{quote(name)}#page={page}"
                label = f"{name} — page {page}"
            else:
                url = f"/files/docs/{quote(name)}"
                label = name
            excerpt = str(getattr(doc, "page_content", "") or "").strip()[:280]
            sources.append(Source(name=name, page=page, url=url, label=label, excerpt=excerpt))
            if len(sources) >= MAX_SOURCES:
                break

    meta: dict[str, Any] = {"nb_passages": len(results)}
    if refusal:
        from src.config import DRH_CONTACT as _DRH

        meta["drh"] = _DRH
    return ChatResponse(answer=answer, sources=sources, refusal=refusal, meta=meta)


@app.get("/api/health")
def health():
    try:
        _rag()
        loaded = True
    except Exception:
        loaded = False
    return {"status": "ok", "rag_loaded": loaded}


@app.get("/api/manifest")
def manifest():
    from chat_context import get_manifest_info

    info = get_manifest_info()
    return info or {}


@app.get("/api/drh")
def drh():
    from src.config import DRH_CONTACT

    return DRH_CONTACT


@app.get("/api/documents")
def documents():
    if not RAW_DIR.exists():
        return {"documents": [], "total": 0}
    docs = []
    for pdf in sorted(RAW_DIR.glob("*.pdf")):
        docs.append({"name": pdf.name, "size": pdf.stat().st_size, "url": f"/files/docs/{quote(pdf.name)}"})
    return {"documents": docs, "total": len(docs)}


@app.get("/files/docs/{filename}")
def serve_doc(filename: str):
    # Sécurise le path (pas de traversal)
    candidate = (RAW_DIR / filename).resolve()
    if RAW_DIR.resolve() not in candidate.parents and candidate != RAW_DIR.resolve():
        raise HTTPException(status_code=400, detail="Nom de fichier invalide")
    if not candidate.is_file():
        raise HTTPException(status_code=404, detail="Document introuvable")
    # "inline" (et non "attachment") : le navigateur ouvre le PDF dans un
    # onglet au lieu de le télécharger. filename* RFC 5987 pour les accents.
    disp = f"inline; filename*=UTF-8''{quote(candidate.name)}"
    return FileResponse(
        str(candidate),
        media_type="application/pdf",
        headers={"Content-Disposition": disp, "Accept-Ranges": "bytes"},
    )


@app.post("/api/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")
    return _answer_sync(question, top_k=req.top_k)


@app.post("/api/chat/stream")
def chat_stream(req: ChatRequest):
    """SSE : events `token` (delta texte) puis `done` (JSON ChatResponse sérialisé)."""
    import json

    question = req.question.strip()
    if not question:
        raise HTTPException(status_code=400, detail="Question vide")

    def gen():
        from chat_context import (
            build_context,
            build_prompt,
            is_refusal,
            log_unanswered,
            search_with_scores,
        )
        from src.config import MAX_SOURCES, REFUSAL_MESSAGE, TOP_K

        try:
            llm, vectordb = _rag()
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            return

        k = req.top_k or TOP_K
        results, scored = search_with_scores(vectordb, question, k=k)
        context = build_context(results)
        prompt = build_prompt(context, question)

        full = ""
        try:
            for chunk in llm.stream(prompt):
                delta = getattr(chunk, "content", "") or ""
                if delta:
                    full += delta
                    yield f"event: token\ndata: {json.dumps({'delta': delta})}\n\n"
        except Exception as exc:
            yield f"event: error\ndata: {json.dumps({'detail': str(exc)})}\n\n"
            return

        refusal = (not results) or is_refusal(full)
        answer = full.strip()
        if refusal and not is_refusal(answer):
            answer = REFUSAL_MESSAGE
        if refusal:
            log_unanswered(question, scored)

        sources = []
        if not refusal:
            seen = set()
            for doc in results:
                name = str(doc.metadata.get("source") or "")
                page = str(doc.metadata.get("page") or "?")
                if not name or (name, page) in seen:
                    continue
                seen.add((name, page))
                url = f"/files/docs/{quote(name)}#page={page}" if page != "?" else f"/files/docs/{quote(name)}"
                excerpt = str(getattr(doc, "page_content", "") or "").strip()[:280]
                sources.append({"name": name, "page": page, "url": url,
                                "label": f"{name} — page {page}" if page != "?" else name,
                                "excerpt": excerpt})
                if len(sources) >= MAX_SOURCES:
                    break

        payload = {"answer": answer, "sources": sources, "refusal": refusal,
                   "meta": {"nb_passages": len(results)}}
        yield f"event: done\ndata: {json.dumps(payload)}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream")
