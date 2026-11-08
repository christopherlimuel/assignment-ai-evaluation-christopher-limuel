"""
Entry point aplikasi FastAPI — IT Helpdesk Assistant.

Alur endpoint utama:
  1. Menerima pertanyaan/permintaan dari user
  2. Meneruskan ke router (router.py) untuk menentukan intent
  3. Router memanggil RAG (rag.py) atau tool (tools.py) sesuai intent
  4. Mengembalikan response terstruktur ke client
"""

import os

from fastapi import FastAPI
from pydantic import BaseModel

from app.router import handle_query
from app.rag import build_index, load_index

def lifespan_event(app: FastAPI):
    """
    Event lifespan FastAPI untuk membangun index FAISS saat startup. Load index jika sudah ada di local storage.
    """
    KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"
    INDEX_PATH = "data/index_it_helpdesk_knowledge_base.index"
    DOCUMENTS_PATH = "data/documents_it_helpdesk_knowledge_base.pkl"
    if not (os.path.exists(INDEX_PATH) and os.path.exists(DOCUMENTS_PATH)):
        build_index(KNOWLEDGE_BASE_PATH)
    else:
        load_index()
    yield

app = FastAPI(title="IT Helpdesk Assistant API", lifespan=lifespan_event)


class AskRequest(BaseModel):
    query: str


class AskResponse(BaseModel):
    intent: dict
    data: str


@app.get("/health")
async def health():
    """Endpoint sederhana untuk memastikan service berjalan."""
    return {"status": "ok"}


@app.post("/ask", response_model=AskResponse)
async def ask(request: AskRequest):
    """
    Endpoint utama. Menerima pertanyaan bebas dari user (bisa berupa
    pertanyaan informasi/kebijakan ATAU permintaan cek status tiket),
    lalu meneruskannya ke router untuk diproses.
    """
    result = await handle_query(request.query)
    return AskResponse(**result)
