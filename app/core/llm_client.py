from google import genai

from app.core.config import settings

_client: genai.Client | None = None


def get_client() -> genai.Client:
    global _client
    api_key = settings.api_key
    if not api_key:
        raise RuntimeError(
            "No GEMINI_API_KEY (or GOOGLE_API_KEY) configured. Set it in the environment/.env before calling this endpoint."
        )
    if _client is None:
        _client = genai.Client(api_key=api_key)
    return _client

