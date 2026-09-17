from fastapi import HTTPException
from openai import OpenAI

from app.config import settings
from app.models import DataSummary

_client: OpenAI | None = None


def get_openai_client() -> OpenAI:
    global _client
    if _client is None:
        if not settings.openai_api_key:
            raise HTTPException(
                status_code=500,
                detail="OPENAI_API_KEY 환경 변수가 설정되어 있지 않습니다.",
            )
        _client = OpenAI(api_key=settings.openai_api_key)
    return _client


def build_system_prompt(summary: DataSummary) -> str:
    return (
        "당신은 사용자의 시계열 데이터를 알고 있는 데이터 분석 비서입니다.\n\n"
        "[사용자 데이터 요약]\n"
        f"- 데이터 기간: {summary.period}\n"
        f"- 총 레코드: {summary.count}개\n"
        f"- 주요 지표: 합계 {summary.metrics.total}, 평균 {summary.metrics.average}, "
        f"최대 {summary.metrics.max}, 최소 {summary.metrics.min}\n"
        f"- 최근 트렌드: {summary.trend}\n\n"
        "위 데이터를 기반으로 구체적인 수치를 인용하며 맞춤형 답변을 제공하세요. "
        "데이터에 없는 내용은 추측하지 말고 모른다고 답하세요."
    )


def get_chat_reply(system_prompt: str, history: list[dict], user_message: str) -> str:
    client = get_openai_client()
    messages = [{"role": "system", "content": system_prompt}, *history, {"role": "user", "content": user_message}]

    response = client.chat.completions.create(
        model=settings.openai_model,
        messages=messages,
        max_tokens=settings.chat_max_tokens,
        temperature=0.7,
    )
    return response.choices[0].message.content
