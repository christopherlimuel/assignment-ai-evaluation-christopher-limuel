"""
Modul RAG — mengubah knowledge base menjadi embedding, menyimpannya ke FAISS,
melakukan semantic search, lalu menghasilkan jawaban menggunakan LLM.

Alur ini serupa dengan yang sudah dibangun di Assignment 3 (Semantic Search &
LLM Application) dan Sesi 11 (Building a Simple RAG System) — di assignment ini,
alur tersebut dibungkus menjadi fungsi yang dipanggil oleh router.py.
"""

import os
import pandas as pd
import numpy as np
import faiss
from google import genai  # sesuaikan dengan library Gemini API yang digunakan
from pydantic import BaseModel, Field
from dotenv import load_dotenv
import json

load_dotenv()
_client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"

_index = None
_documents = None
_df = None

class RAGResponse(BaseModel):
    is_relevant:bool = Field(description="true jika jawaban ditemukan di context yang disediakan, atau false jika tidak ditemukan")
    answer:str = Field(description="Jawaban berdasarkan context yang disediakan, atau bilang anda tidak memiliki informasi tersebut dan sarankan menghubungi IT Support")

def _get_embedding(text: str):
    result = _client.models.embed_content(
        model="gemini-embedding-2",  # sesuaikan versi model embedding
        contents=text,
    )
    return result.embeddings[0].values

def _build_prompt(query, context):
    prompt = f"""
        [Persona]
        Anda adalah asisten IT Helpdesk yang ramah, profesional, dan membantu.
        
        [Task]
        1. Analisis apakah informasi yang relevan untuk menjawab pertanyaan pengguna tersedia di dalam [Context] di bawah.
        2. Tentukan nilai 'is_relevant':
            - Bernilai 'true' jika informasi yang dicari ditemukan dan relevan di dalam context.
            - Bernilai 'false' jika informasi tidak ditemukan atau tidak relevan.
        3. Buat isi 'answer':
            - Jika relevan ('true'), berikan jawaban langsung ke intinya dan terstruktur berdasarkan context.
            - Jika tidak relevan ('false'), katakan dengan jujur bahwa anda belum memiliki informasi tersebut dan sarankan untuk menghubungi IT support.
        
        [Context]
        {context}
        
        [Question]
        {query}
        """
    return prompt


def build_index(csv_path):
    global _index, _documents, _df
    _df = pd.read_csv(csv_path)
    _df['content'] = "Q: " + _df["question"] + " A: " + _df["answer"]
    _documents = _df["content"].tolist()

    embeddings = [_get_embedding(unit) for unit in _documents]
    embeddings = np.array(embeddings, dtype=np.float32)

    faiss_dimensions = embeddings.shape[1]          # embeddings.shape = (number of embedding, vector size of each embedding)
    _index = faiss.IndexFlatL2(faiss_dimensions)
    _index.add(embeddings)


def semantic_search(query: str, top_k: int = 3):
    global _index, _df

    if _index is None:
        build_index(KNOWLEDGE_BASE_PATH)
    
    query_embedding =[_get_embedding(query)]
    query_embedding = np.array(query_embedding, dtype=np.float32)

    distances, indices = _index.search(query_embedding, top_k)
    results = []
    for rank, idx in enumerate(indices[0]):
        results.append({
            'rank': rank + 1,
            'distance': distances[0][rank],
            'question': _df.iloc[idx]['question'],
            'answer': _df.iloc[idx]['answer'],
            'category': _df.iloc[idx]['category'] 
        })

    return results


async def answer_from_knowledge_base(query: str) -> dict:
    """
    Fungsi yang dipanggil router.py ketika intent = 'faq'.
    Menjalankan semantic search, menyusun prompt dengan context hasil retrieval,
    lalu memanggil LLM untuk menghasilkan jawaban.
    """
    search_result = semantic_search(query, top_k=3)
    prompt = _build_prompt(query, search_result)
    response_json = _client.models.generate_content(
        model='gemini-3.1-flash-lite',  # sesuaikan versi model
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.3, 
            response_mime_type="application/json",
            response_schema=RAGResponse)
    )
    response = json.loads(response_json.text)
    if response["is_relevant"] == True:
        response_status = "success"
    else:
        response_status = "error"
    return {"status":response_status, "data":response["answer"]}