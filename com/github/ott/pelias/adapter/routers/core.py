from fastapi import APIRouter
from pydantic import BaseModel

from com.github.ott.pelias.adapter.core.config import settings

router = APIRouter()


class HealthCheck(BaseModel):
    status: str
    message: str


@router.get("/health", response_model=HealthCheck)
def health_check():
    """
    Health check endpoint that tests database connectivity
    """
    return HealthCheck(status="ok", message="Service is healthy")


@router.get("/info")
async def info():
    """
    Application information endpoint
    """
    return {
        "app_name": settings.app_name,
        "version": "1.0.0",
    }


@router.get("/")
async def root():
    """
    Root endpoint
    """
    return {
        "message": f"Welcome to {settings.app_name}",
        "description": "FastAPI Pelias Wrapper",
        "docs": "/docs",
        "redoc": "/redoc",
    }
