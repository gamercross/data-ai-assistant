import json
from functools import lru_cache

import firebase_admin
from fastapi import HTTPException
from firebase_admin import credentials, firestore

from app.config import settings


@lru_cache
def get_firestore_client():
    """Lazily initialize and return the Firestore client.

    Raises a clear 500 error instead of crashing app startup, so /docs still
    works locally even before FIREBASE_SERVICE_ACCOUNT_JSON is configured.
    """
    if not firebase_admin._apps:
        if not settings.firebase_service_account_json:
            raise HTTPException(
                status_code=500,
                detail="FIREBASE_SERVICE_ACCOUNT_JSON 환경 변수가 설정되어 있지 않습니다.",
            )
        try:
            cred_info = json.loads(settings.firebase_service_account_json)
        except json.JSONDecodeError as exc:
            raise HTTPException(
                status_code=500,
                detail=f"FIREBASE_SERVICE_ACCOUNT_JSON 파싱에 실패했습니다: {exc}",
            ) from exc
        cred = credentials.Certificate(cred_info)
        firebase_admin.initialize_app(cred)

    return firestore.client()
