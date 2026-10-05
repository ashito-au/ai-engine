from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from .database import get_connection, init_db
from .models import KnowledgeCreate, SearchRequest, GenerateRequest
from .engine import extract_topics, search_items, openai_generate

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND = BASE_DIR / "frontend"

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield

app = FastAPI(title="AI Engine", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def row_to_dict(row):
    item = dict(row)
    item["topics"] = [x for x in item["topics"].split(",") if x]
    return item

@app.get("/")
def home():
    return FileResponse(FRONTEND / "index.html")

@app.get("/health")
def health():
    return {"status": "ok", "name": "AI Engine"}

@app.post("/api/knowledge")
def create_knowledge(payload: KnowledgeCreate):
    topics = ",".join(extract_topics(f"{payload.title} {payload.content}"))
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO knowledge(title, content, source, topics) VALUES (?, ?, ?, ?)",
            (payload.title, payload.content, payload.source or "", topics)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM knowledge WHERE id=?", (cur.lastrowid,)).fetchone()
    return row_to_dict(row)

@app.get("/api/knowledge")
def list_knowledge():
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM knowledge ORDER BY id DESC").fetchall()
    return [row_to_dict(x) for x in rows]

@app.post("/api/search")
def search(payload: SearchRequest):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM knowledge").fetchall()
    return search_items([row_to_dict(x) for x in rows], payload.query, payload.limit)

@app.post("/api/generate")
def generate(payload: GenerateRequest):
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM knowledge").fetchall()
    items = [row_to_dict(x) for x in rows]
    sources = search_items(items, payload.query, payload.limit)
    if not sources:
        raise HTTPException(status_code=400, detail="No relevant knowledge found. Save some information first.")
    return openai_generate(payload.query, sources)

@app.delete("/api/knowledge/{knowledge_id}")
def delete_knowledge(knowledge_id: int):
    with get_connection() as conn:
        cur = conn.execute("DELETE FROM knowledge WHERE id=?", (knowledge_id,))
        conn.commit()
    if cur.rowcount == 0:
        raise HTTPException(status_code=404, detail="Knowledge not found")
    return {"deleted": knowledge_id}
