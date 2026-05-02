from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    gemini_api_key: str
    groq_api_key: str

    db_port: str
    pguser: str
    postgres_password: str
    postgres_db: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def database_url(self):
        return f"postgresql://{self.pguser}:{self.postgres_password}@localhost:{self.db_port}/{self.postgres_db}"


settings = Settings()
