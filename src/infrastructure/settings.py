from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str

    postgres_url: str

    mongodb_uri: str = "mongodb://localhost:27017"
    mongodb_dbname: str = "assessoria"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
