import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.core.config import settings
from app.core.db import init_db
from app.core.limiter import limiter, rate_limit_exceeded_handler
from app.routers import admin, artists, auth, concierge, early_access, taste_profile, verify


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(
    title=settings.app_name,
    description="Backend for Corpus — the tattoo art decision layer.",
    version="0.1.0",
    lifespan=lifespan,
)

# Rate limiting state & exception handler
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

os.makedirs("app/static/deck", exist_ok=True)
os.makedirs("app/static/avatars", exist_ok=True)
os.makedirs("app/static/concierge", exist_ok=True)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(admin.router)
app.include_router(verify.router)
app.include_router(concierge.router)
app.include_router(taste_profile.router)
app.include_router(artists.router)
app.include_router(early_access.router)


@app.get("/health")
@limiter.exempt
def health(request: Request):
    return {"status": "ok", "environment": settings.environment}


