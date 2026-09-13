from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Central app config. Values are loaded from environment variables / .env.
    Never commit a real .env with a live API key.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Corpus API"
    environment: str = "development"
    port: int = 8003

    # LLM provider config (Google Gemini)
    gemini_api_key: str = ""
    google_api_key: str = ""  # fallback if standard GOOGLE_API_KEY is used
    verification_model: str = "gemini-3.6-flash"
    concierge_model: str = "gemini-3.6-flash"

    # CORS configuration (comma-separated or list)
    cors_origins: list[str] = ["*"]

    # Database. Defaults to local SQLite for zero-setup dev; point this at a
    # real Postgres instance (async driver) for anything beyond local testing —
    # e.g. postgresql+asyncpg://user:pass@host:5432/corpus
    database_url: str = "sqlite+aiosqlite:///./corpus.db"

    # Feature flags
    enable_verification: bool = True
    enable_concierge: bool = True

    @property
    def api_key(self) -> str:
        return self.gemini_api_key or self.google_api_key


settings = Settings()

