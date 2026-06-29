from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: SecretStr = SecretStr("No key provided")
    groq_api_key: SecretStr = SecretStr("No key provided")

    postgres_url: SecretStr = SecretStr(
        "postgresql://postgres:postgres@localhost:5432/acessoriadb"
    )

    mongodb_uri: SecretStr = SecretStr("mongodb://localhost:27017")
    mongodb_dbname: SecretStr = SecretStr("assessoria")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
