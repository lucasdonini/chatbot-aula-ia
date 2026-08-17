from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict

_DUMMY_API_KEY = "No key provided"


class Settings(BaseSettings):
    gemini_api_key: SecretStr = SecretStr(_DUMMY_API_KEY)
    groq_api_key: SecretStr = SecretStr(_DUMMY_API_KEY)

    postgres_url: SecretStr = SecretStr("postgresql://localhost:5432/acessoriadb")

    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongodb_dbname: SecretStr = SecretStr("assessoria")

    log_level: Literal["INFO", "DEBUG"] = "INFO"
    log_to_file: bool = False
    log_file: str = "logs/app.log"
    app_timezone: str = "America/Sao_Paulo"

    model_config = SettingsConfigDict(env_file=".env", extra="forbid")

    def validate_llm_api_keys(self) -> None:
        missing_keys = [
            key
            for key, value in (
                ("GEMINI_API_KEY", self.gemini_api_key),
                ("GROQ_API_KEY", self.groq_api_key),
            )
            if value.get_secret_value() == _DUMMY_API_KEY
        ]
        if missing_keys:
            variables = ", ".join(missing_keys)
            raise ValueError(f"Configure as chaves de API: {variables}.")


settings = Settings()
