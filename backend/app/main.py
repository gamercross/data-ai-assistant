from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers import chat, conversations, data

app = FastAPI(
    title="Data-Aware AI Assistant API",
    description="시계열 데이터를 이해하고 맞춤형으로 답변하는 AI 비서 API",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router, prefix="/api/data", tags=["data"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])
app.include_router(chat.router, prefix="/api/chat", tags=["chat"])


@app.get("/")
def root():
    return {"status": "ok", "service": "data-ai-assistant-api", "docs": "/docs"}


@app.get("/health")
def health():
    return {"status": "healthy"}
