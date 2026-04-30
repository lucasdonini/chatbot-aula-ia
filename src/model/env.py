from pydantic_settings import BaseSettings, SettingsConfigDict


class EnvVariables(BaseSettings):
    gemini_api_key: str
    groq_api_key: str
    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


env = EnvVariables()
