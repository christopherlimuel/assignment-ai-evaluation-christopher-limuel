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
import pickle
from google import genai  # sesuaikan dengan library Gemini API yang digunakan
from dotenv import load_dotenv
from langsmith import traceable
from langsmith.wrappers import wrap_gemini

# Client Gemini untuk get_embedding dan answer_from_knowledge_base
load_dotenv()
_client_raw = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
_client = wrap_gemini(_client_raw)

KNOWLEDGE_BASE_PATH = "data/it_helpdesk_knowledge_base.csv"
INDEX_PATH = "data/index_it_helpdesk_knowledge_base.index"
DOCUMENTS_PATH = "data/documents_it_helpdesk_knowledge_base.pkl"

@traceable(name="Gemini get_embedding", project=os.environ.get("LANGSMITH_PROJECT"))
def _get_embedding(text: str):
    result = _client.models.embed_content(
        model="gemini-embedding-2",  # sesuaikan versi model embedding
        contents=text,
    )
    return result.embeddings[0].values

# Membangun index FAISS dan menyimpan ke local storage
@traceable(name="Gemini build_index", project=os.environ.get("LANGSMITH_PROJECT"))
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
    faiss.write_index(_index, INDEX_PATH)
    with open(DOCUMENTS_PATH, "wb") as f:
        pickle.dump(_documents, f)

# Load index FAISS dan documents dari local storage
def load_index():
    global _index, _documents, _df
    _index = faiss.read_index(INDEX_PATH)
    with open(DOCUMENTS_PATH, "rb") as f:
        _documents = pickle.load(f)
    _df = pd.read_csv(KNOWLEDGE_BASE_PATH)

# Prompt builder untuk answer_from_knowledge_base
def _build_prompt(query:str, context:str) -> str:
    prompt = f"""
        [Persona]
        Anda adalah asisten IT Helpdesk yang ramah, profesional, dan membantu.
        
        [Task]
        1. Jawab [Question] HANYA berdasarkan [Context] yang tersedia dengan jelas, ringkas, one-line response.
        2. Jika [Context] berisi **Data Tiket**: Sebutkan kode ID tiket dan subjek, sampaikan status dan pembaruan terakhir tiket tersebut dengan jelas kepada user.
        3. Jika [Context] berisi **Data FAQ**: Jelaskan jawabannya secara ringkas dan terstruktur.
        4. Jika [Context] berisi pesan **[System Notice]**: Ikuti instruksi dan sampaikan pesan tersebut dengan bahasa yang ramah dan humanis.
        5. Jika ada sebagian [Question] yang tidak dapat dijawab dari [Context], sampaikan dengan jujur bahwa anda tidak memiliki informasi tersebut, dan sarankan user untuk menghubungi IT support.
        6. Jawab terlebih dahulu [Question] sesuai [Context] yang tersedia, sebelum menyampaikan [System Notice] atau bagian [Question] yang tidak dapat dijawab.
        
        [Context]
        {context}
        
        [Question]
        {query}
        """
    return prompt

# Embed query dan semantic search di index FAISS, mengembalikan top_k hasil teratas
def semantic_search(query: str, top_k: int = 3) -> list[dict]:
    global _index, _df

    if _index is None:
        load_index()
    
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

@traceable(name="Gemini answer_from_knowledge_base", project=os.environ.get("LANGSMITH_PROJECT"))
async def answer_from_knowledge_base(query: str, context:str) -> str:
    """
    Fungsi yang dipanggil router.py ketika intent = 'faq'.
    Menjalankan semantic search, menyusun prompt dengan context hasil retrieval,
    lalu memanggil LLM untuk menghasilkan jawaban.
    """
    prompt = _build_prompt(query, context)
    response_str = _client.models.generate_content(
        model='gemini-3.1-flash-lite',  # sesuaikan versi model
        contents=prompt,
        config=genai.types.GenerateContentConfig(
            temperature=0.3)
    ).text
    return response_str

# TODO: Tambahkan dynamic top_k selection
# TODO: Tambahkan reranking pada hasil semantic search sebelum diteruskan ke LLM 