from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException

from app.models import ChatRequest, ChatResponse
from app.services.analysis import build_summary
from app.services.firestore_client import get_firestore_client
from app.services.gemini_service import build_system_prompt, get_chat_reply

router = APIRouter()
DATA_COLLECTION = "data"
CONV_COLLECTION = "conversations"


@router.post("", response_model=ChatResponse)
def chat(payload: ChatRequest):
    db = get_firestore_client()

    # 1) 데이터 요약 조회
    points = [{"date": doc.to_dict()["date"], "value": doc.to_dict()["value"]} for doc in db.collection(DATA_COLLECTION).stream()]
    summary = build_summary(points)

    # 2) 요약을 시스템 프롬프트에 삽입
    system_prompt = build_system_prompt(summary)

    now = datetime.now(timezone.utc)
    conv_ref = None
    existing_messages: list[dict] = []
    title = payload.message[:30]

    if payload.conversation_id:
        conv_ref = db.collection(CONV_COLLECTION).document(payload.conversation_id)
        snapshot = conv_ref.get()
        if not snapshot.exists:
            raise HTTPException(status_code=404, detail="Conversation not found")
        existing = snapshot.to_dict()
        existing_messages = existing.get("messages", [])
        title = existing.get("title", title)

    history = [{"role": m["role"], "content": m["content"]} for m in existing_messages]

    # 3) Gemini API 호출
    reply = get_chat_reply(system_prompt, history, payload.message)

    # 4) 대화 내용을 conversations에 자동 저장
    new_messages = existing_messages + [
        {"role": "user", "content": payload.message},
        {"role": "assistant", "content": reply},
    ]

    if conv_ref is None:
        conv_ref = db.collection(CONV_COLLECTION).document()
        conv_ref.set({"title": title, "messages": new_messages, "created_at": now, "updated_at": now})
    else:
        conv_ref.update({"messages": new_messages, "updated_at": now})

    return ChatResponse(reply=reply, conversation_id=conv_ref.id)
