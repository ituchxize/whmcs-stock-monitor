from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.persistence.database import get_db
from src.core.config import settings

router = APIRouter(tags=["Health"])


@router.get("/health")
async def health_check(db: AsyncSession = Depends(get_db)):
    try:
        await db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")

    return {
        "status": "healthy",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "database": db_status
    }


@router.get("/")
async def root():
    return {
        "message": f"Welcome to {settings.app_name}",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health"
    }
