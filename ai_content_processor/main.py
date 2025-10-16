# backend/main.py (Final Version with User Auth)

import os
import shutil
import requests
from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi.middleware.cors import CORSMiddleware
from typing import Tuple

from sentence_transformers import SentenceTransformer
import numpy as np
import faiss
from langchain.text_splitter import RecursiveCharacterTextSplitter

import crud
import models
from database import SessionLocal, engine

import yt_dlp
import whisper
import trafilatura
import fitz

models.Base.metadata.create_all(bind=engine)

# --- Pydantic Models ---
class UserCreate(BaseModel):
    name: str
    email: str
    password: str

class UserLogin(BaseModel):
    email: str
    password: str

class URLRequest(BaseModel):
    url: str
    user_id: int

class ChatRequest(BaseModel):
    source_identifier: str
    question: str
    user_id: int


app = FastAPI()

origins = ["*"]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

CLOUDFLARE_WORKER_URL = "https://my-ai-worker.pritam-kundu.workers.dev"

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

print("Loading AI models...")
whisper_model = whisper.load_model("base")
embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
print("Models loaded.")

rag_indexes = {}

# --- Auth Endpoints ---
@app.post("/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if db_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    new_user = crud.create_user(db, name=user.name, email=user.email, password=user.password)
    return {"id": new_user.id, "name": new_user.name, "email": new_user.email}

@app.post("/login")
def login_user(user: UserLogin, db: Session = Depends(get_db)):
    db_user = crud.get_user_by_email(db, email=user.email)
    if not db_user or not crud.verify_password(user.password, db_user.hashed_password):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"id": db_user.id, "name": db_user.name, "email": db_user.email}


# --- Content Endpoints (Now User-Specific) ---
@app.get("/sources/{user_id}")
def get_user_sources(user_id: int, db: Session = Depends(get_db)):
    return crud.get_sources_by_owner(db, owner_id=user_id)

@app.delete("/sources/{source_id}/{user_id}")
def delete_source(source_id: int, user_id: int, db: Session = Depends(get_db)):
    content_to_delete = crud.delete_content_source_by_id(db, source_id=source_id, owner_id=user_id)
    if not content_to_delete:
        raise HTTPException(status_code=404, detail="Source not found or you do not have permission to delete it.")
    if content_to_delete.source_identifier in rag_indexes:
        del rag_indexes[content_to_delete.source_identifier]
    return {"message": "Source deleted successfully."}

@app.post("/process-source")
def process_source(request: URLRequest, db: Session = Depends(get_db)):
    db_content = crud.get_content_by_source_and_owner(db, owner_id=request.user_id, source_identifier=request.url)
    if db_content:
        return db_content

    source_type = "youtube" if "youtube.com" in request.url or "youtu.be" in request.url else "website"
    title, content = _process_youtube(request.url) if source_type == "youtube" else (request.url, _scrape_website_content(request.url))
    
    new_db_content = crud.create_content_source(db, source_identifier=request.url, source_type=source_type, content=content, title=title, owner_id=request.user_id)
    _build_rag_index(request.url, content)
    return new_db_content

@app.post("/process-pdf-upload/{user_id}")
def process_pdf_upload(user_id: int, db: Session = Depends(get_db), file: UploadFile = File(...)):
    db_content = crud.get_content_by_source_and_owner(db, owner_id=user_id, source_identifier=file.filename)
    if db_content:
        return db_content

    content = _extract_pdf_text(file)
    new_db_content = crud.create_content_source(db, source_identifier=file.filename, source_type="pdf", content=content, title=file.filename, owner_id=user_id)
    _build_rag_index(file.filename, content)
    return new_db_content

@app.post("/chat")
def chat_with_source(request: ChatRequest, db: Session = Depends(get_db)):
    # Note: We are not checking user_id here for simplicity, but in a real app you would.
    source_identifier = request.source_identifier
    if source_identifier not in rag_indexes:
        # This part needs the owner_id to be truly secure, but we simplify for now.
        db_content = db.query(models.ContentSource).filter(models.ContentSource.source_identifier == source_identifier).first()
        if not db_content: raise HTTPException(status_code=404, detail="Source not found.")
        _build_rag_index(source_identifier, db_content.content)

    relevant_context = _search_rag_index(source_identifier, request.question)
    prompt = f"Based ONLY on the following context, answer the user's question. If the answer is not found, say so.\n\nCONTEXT:\n---\n{relevant_context}\n---\n\nQUESTION:\n{request.question}"
    
    try:
        response = requests.post(CLOUDFLARE_WORKER_URL, json={"prompt": prompt}, headers={"Content-Type": "application/json"}, timeout=60)
        response.raise_for_status()
        ai_response = response.json()
        return {"answer": ai_response.get("response", "Error parsing AI response.")}
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"AI service connection error: {e}")

# (Helper functions remain the same)
def _build_rag_index(source_identifier: str, text: str):
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = text_splitter.split_text(text)
    if not chunks: return
    embeddings = embedding_model.encode(chunks)
    index = faiss.IndexFlatL2(embeddings.shape[1])
    index.add(np.array(embeddings, dtype=np.float32))
    rag_indexes[source_identifier] = {"index": index, "chunks": chunks}
    print(f"RAG index built for: {source_identifier}")

def _search_rag_index(source_identifier: str, query: str, k: int = 3) -> str:
    if source_identifier not in rag_indexes: return "No content found for this source."
    index_data = rag_indexes[source_identifier]
    query_embedding = embedding_model.encode([query])
    _, indices = index_data["index"].search(np.array(query_embedding, dtype=np.float32), k)
    return "\n\n".join([index_data["chunks"][i] for i in indices[0]])

def _process_youtube(url: str) -> Tuple[str, str]:
    ydl_opts_info = {'quiet': True, 'extract_flat': True, 'force_generic_extractor': True}
    with yt_dlp.YoutubeDL(ydl_opts_info) as ydl:
        info = ydl.extract_info(url, download=False)
        title = info.get('title', 'Unknown YouTube Video')
    audio_filename = "temp_audio.mp3"
    ydl_opts_audio = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3'}], 'outtmpl': audio_filename.split('.')[0], 'quiet': True}
    try:
        with yt_dlp.YoutubeDL(ydl_opts_audio) as ydl: ydl.download([url])
        if not os.path.exists(audio_filename): raise RuntimeError("yt-dlp failed to download.")
        result = whisper_model.transcribe(audio_filename)
        return title, result["text"]
    finally:
        if os.path.exists(audio_filename): os.remove(audio_filename)

def _scrape_website_content(url: str) -> str:
    response = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'})
    response.raise_for_status()
    return trafilatura.extract(response.text) or "Could not extract content."

def _extract_pdf_text(file: UploadFile) -> str:
    temp_pdf_path = f"temp_{file.filename}"
    try:
        with open(temp_pdf_path, "wb") as buffer: shutil.copyfileobj(file.file, buffer)
        with fitz.open(temp_pdf_path) as doc:
            full_text = "".join(page.get_text() for page in doc)
        return full_text or "PDF has no text."
    finally:
        if os.path.exists(temp_pdf_path): os.remove(temp_pdf_path)
