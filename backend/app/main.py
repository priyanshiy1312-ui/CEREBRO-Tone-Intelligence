from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .parser.chat_parser import parse_chat
from .services.context_engine import analyze_conversation
from .nlp import models

app = FastAPI(title="CEREBRO Tone Intelligence")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])
PRIVACY = "Conversation data is processed for analysis and is not stored by default."

class AnalyzeIn(BaseModel):
    text: str

def _run(raw):
    msgs, fmt = parse_chat(raw)
    if len(msgs) < 2: raise HTTPException(400, "Could not parse at least 2 messages. Use 'Name: message' lines.")
    if len(msgs) > 500: raise HTTPException(400, "Limit is 500 messages.")
    out = analyze_conversation(msgs)
    return {**out, "format": fmt, "privacy": PRIVACY}

@app.get("/api/health")
def health(): return {"status": "ok", "engine": models.engine()}

@app.post("/api/analyze")
def analyze(body: AnalyzeIn): return _run(body.text)

@app.post("/api/upload")
async def upload(file: UploadFile = File(...)):
    raw = (await file.read()).decode("utf-8", errors="ignore")  # held in memory only, never written to disk
    return _run(raw)
