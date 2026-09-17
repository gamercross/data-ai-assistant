import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    openai_api_key: str | None = os.getenv("OPENAI_API_KEY")
    openai_model: str = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
    chat_max_tokens: int = int(os.getenv("CHAT_MAX_TOKENS", "500"))
    firebase_service_account_json: str | None = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")
    allowed_origins_raw: str = os.getenv("ALLOWED_ORIGINS", "*")

    @property
    def allowed_origins(self) -> list[str]:
        raw = self.allowed_origins_raw.strip()
        if raw == "*" or not raw:
            return ["*"]
        return [origin.strip() for origin in raw.split(",") if origin.strip()]


settings = Settings()
