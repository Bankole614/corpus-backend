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

    # Auth & Security
    jwt_secret_key: str = "corpus-jwt-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 60 * 24 * 7  # 7 days
    password_reset_token_expire_minutes: int = 15
    google_client_id: str = ""
    admin_api_key: str = ""

    # Email & Brevo
    brevo_api_key: str = ""
    emails_from_email: str = "noreply@mail.bankole.xyz"
    brevo_sender_email: str = ""
    emails_from_name: str = "Corpus"
    brevo_sender_name: str = ""
    frontend_url: str = "http://localhost:3000"

    # Rate Limiting
    rate_limit_enabled: bool = True
    rate_limit_storage_url: str = "memory://"
    rate_limit_auth: str = "10/minute"
    rate_limit_forgot_password: str = "3/minute"
    rate_limit_verify: str = "15/minute"
    rate_limit_concierge_chat: str = "20/minute"
    rate_limit_concierge_brief: str = "5/minute"
    rate_limit_default: str = "100/minute"

    @property
    def sender_email(self) -> str:
        return self.brevo_sender_email or self.emails_from_email

    @property
    def sender_name(self) -> str:
        return self.brevo_sender_name or self.emails_from_name

    @property
    def api_key(self) -> str:
        return self.gemini_api_key or self.google_api_key


settings = Settings()

