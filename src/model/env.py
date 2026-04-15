from pydantic_settings import BaseSettings


class EnvVariables(BaseSettings):
    gemini_api_key: str
    groq_api_key: str
    database_url: str

    model_config = {"env_file": ".env"}


env = EnvVariables()
