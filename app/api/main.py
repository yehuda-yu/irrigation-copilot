"""
FastAPI application entrypoint.

Initializes the FastAPI app and registers routes.
Health endpoint and irrigation plan endpoints will be added here.
"""

from pathlib import Path

from dotenv import load_dotenv

# Load .env file before anything else (must be before other imports)
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)

from fastapi import Depends, FastAPI, HTTPException, Request, status  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse, RedirectResponse  # noqa: E402
from fastapi.security import APIKeyHeader  # noqa: E402

from app.api.routes import agent, irrigation  # noqa: E402
from app.utils.config import settings  # noqa: E402

app = FastAPI(title="Irrigation Copilot API")

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Restrict this in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Key Auth
api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

async def verify_api_key(api_key: str = Depends(api_key_header)):
    """Verify the API key if API_AUTH_KEY is set."""
    if settings.api_auth_key and api_key != settings.api_auth_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": "Invalid or missing API Key",
                }
            }
        )
    return api_key

@app.exception_handler(HTTPException)
async def custom_http_exception_handler(request: Request, exc: HTTPException):
    """Flatten the error response if it contains 'error' key."""
    if isinstance(exc.detail, dict) and "error" in exc.detail:
        return JSONResponse(
            status_code=exc.status_code,
            content=exc.detail,
        )
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
    )

app.include_router(
    irrigation.router,
    prefix="/irrigation",
    tags=["irrigation"],
    dependencies=[Depends(verify_api_key)]
)
app.include_router(
    agent.router,
    prefix="/agent",
    tags=["agent"],
    dependencies=[Depends(verify_api_key)]
)


@app.get("/")
async def root():
    """Root endpoint - redirects to API documentation."""
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}
