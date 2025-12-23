"""
FastAPI application entrypoint.

Initializes the FastAPI app and registers routes.
Health endpoint and irrigation plan endpoints will be added here.
"""

from fastapi import FastAPI

app = FastAPI(title="Irrigation Copilot API")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

