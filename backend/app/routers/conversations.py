from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException
from firebase_admin import firestore

from app.models import ChatMessage, ConversationCreate, ConversationDetail, ConversationSummary
from app.services.firestore_client import get_firestore_client

router = APIRouter()
COLLECTION = "conversations"


def _title_from_messages(messages: list[ChatMessage]) -> str:
    for message in messages:
        if message.role == "user":
            return message.content[:30]
    return "새 대화"


@router.post("", response_model=ConversationDetail, status_code=201)
def create_conversation(payload: ConversationCreate):
    db = get_firestore_client()
    now = datetime.now(timezone.utc)
    title = payload.title or _title_from_messages(payload.messages)

    doc_ref = db.collection(COLLECTION).document()
    doc_ref.set({
        "title": title,
        "messages": [m.model_dump() for m in payload.messages],
        "created_at": now,
        "updated_at": now,
    })

    return ConversationDetail(
        id=doc_ref.id,
        title=title,
        message_count=len(payload.messages),
        created_at=now,
        updated_at=now,
        messages=payload.messages,
    )


@router.get("", response_model=list[ConversationSummary])
def list_conversations():
    """대화 목록 조회. 응답에는 메시지 본문은 포함하지 않고 요약 정보만 담는다.
    전체 메시지가 필요하면 GET /api/conversations/{id}를 사용한다.
    """
    db = get_firestore_client()
    docs = db.collection(COLLECTION).order_by("updated_at", direction=firestore.Query.DESCENDING).stream()
    return [
        ConversationSummary(
            id=doc.id,
            title=doc.to_dict().get("title", "새 대화"),
            message_count=len(doc.to_dict().get("messages", [])),
            created_at=doc.to_dict()["created_at"],
            updated_at=doc.to_dict()["updated_at"],
        )
        for doc in docs
    ]


@router.get("/{conversation_id}", response_model=ConversationDetail)
def get_conversation(conversation_id: str):
    db = get_firestore_client()
    doc = db.collection(COLLECTION).document(conversation_id).get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="Conversation not found")

    d = doc.to_dict()
    return ConversationDetail(
        id=doc.id,
        title=d.get("title", "새 대화"),
        message_count=len(d.get("messages", [])),
        created_at=d["created_at"],
        updated_at=d["updated_at"],
        messages=[ChatMessage(**m) for m in d.get("messages", [])],
    )


@router.delete("/{conversation_id}", status_code=204)
def delete_conversation(conversation_id: str):
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Conversation not found")
    doc_ref.delete()
