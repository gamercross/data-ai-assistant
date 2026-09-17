from fastapi import APIRouter, HTTPException

from app.models import DataPointCreate, DataPointOut, DataPointUpdate, DataSummary
from app.services.analysis import build_summary
from app.services.firestore_client import get_firestore_client

router = APIRouter()
COLLECTION = "data"


@router.post("", response_model=DataPointOut, status_code=201)
def create_data_point(payload: DataPointCreate):
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION).document()
    doc_ref.set({
        "date": payload.date.isoformat(),
        "value": payload.value,
        "memo": payload.memo,
    })
    return DataPointOut(id=doc_ref.id, **payload.model_dump())


@router.get("", response_model=list[DataPointOut])
def list_data_points():
    db = get_firestore_client()
    result = [
        DataPointOut(id=doc.id, date=doc.to_dict()["date"], value=doc.to_dict()["value"], memo=doc.to_dict().get("memo"))
        for doc in db.collection(COLLECTION).stream()
    ]
    result.sort(key=lambda p: p.date)
    return result


@router.get("/summary", response_model=DataSummary)
def get_summary():
    db = get_firestore_client()
    points = [{"date": doc.to_dict()["date"], "value": doc.to_dict()["value"]} for doc in db.collection(COLLECTION).stream()]
    return build_summary(points)


@router.put("/{data_id}", response_model=DataPointOut)
def update_data_point(data_id: str, payload: DataPointUpdate):
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION).document(data_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Data point not found")

    updates = {}
    if payload.date is not None:
        updates["date"] = payload.date.isoformat()
    if payload.value is not None:
        updates["value"] = payload.value
    if payload.memo is not None:
        updates["memo"] = payload.memo
    if updates:
        doc_ref.update(updates)

    d = doc_ref.get().to_dict()
    return DataPointOut(id=data_id, date=d["date"], value=d["value"], memo=d.get("memo"))


@router.delete("/{data_id}", status_code=204)
def delete_data_point(data_id: str):
    db = get_firestore_client()
    doc_ref = db.collection(COLLECTION).document(data_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="Data point not found")
    doc_ref.delete()
