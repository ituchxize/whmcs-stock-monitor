import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session

from .config import settings
from .database import get_db, init_db
from .scheduler import MonitorScheduler
from .monitoring_engine import MonitoringEngine

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

monitoring_engine = MonitoringEngine()
scheduler = MonitorScheduler(monitoring_engine=monitoring_engine)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting WHMCS Stock Monitor application")
    
    try:
        init_db()
        logger.info("Database initialized")
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise
    
    try:
        scheduler.start()
        logger.info("Monitoring scheduler started")
    except Exception as e:
        logger.error(f"Failed to start scheduler: {e}")
        raise
    
    yield
    
    logger.info("Shutting down WHMCS Stock Monitor application")
    
    try:
        scheduler.shutdown(wait=True)
        logger.info("Monitoring scheduler stopped")
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")


app = FastAPI(
    title="WHMCS Stock Monitor",
    description="A monitoring system for WHMCS product inventory with real-time notifications",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/")
async def root():
    return {
        "name": "WHMCS Stock Monitor",
        "status": "running",
        "scheduler_running": scheduler.is_running()
    }


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "scheduler_running": scheduler.is_running(),
        "jobs": [
            {
                "id": job.id,
                "name": job.name,
                "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None
            }
            for job in scheduler.get_jobs()
        ]
    }


@app.post("/monitoring/run-now")
async def trigger_monitoring(db: Session = Depends(get_db)):
    logger.info("Manual monitoring cycle triggered")
    results = monitoring_engine.run_monitoring_cycle()
    return {
        "status": "completed",
        "results": results
    }


@app.post("/scheduler/pause")
async def pause_scheduler():
    scheduler.pause()
    return {"status": "paused"}


@app.post("/scheduler/resume")
async def resume_scheduler():
    scheduler.resume()
    return {"status": "resumed"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
