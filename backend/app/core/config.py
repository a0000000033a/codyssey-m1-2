from typing import Literal
from pydantic import Field, SecretStr, HttpUrl
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=(".env", "backend/.env"), extra="ignore")
    openai_api_key: SecretStr = SecretStr("")
    openai_model: str = ""
    openai_base_url: HttpUrl = HttpUrl("https://api.openai.com/v1")
    openai_api_mode: Literal["responses", "chat_completions"] = "responses"
    openai_chat_token_field: Literal["max_completion_tokens", "max_tokens"] = "max_completion_tokens"
    openai_max_output_tokens: int = Field(default=800, ge=100, le=4000)
    openai_timeout_seconds: int = Field(default=45, ge=5, le=60)
    chat_lock_seconds: int = Field(default=90, ge=90, le=300)
    chat_input_max_chars: int = Field(default=24000, ge=5000, le=50000)
    firebase_service_account_json: SecretStr = SecretStr("")
    google_application_credentials: str = ""
    allowed_user_uid: str = ""
    allowed_origins: list[str] = ["http://localhost:5500", "http://127.0.0.1:5500"]
