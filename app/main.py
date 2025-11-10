"""FastAPI application main module."""

import logging
import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.database.connection import Database
from app.routes import auth_routes, alert_routes, rule_routes, dashboard_routes
from app.jobs.scheduler import start_scheduler, shutdown_scheduler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Handles database connection on startup and disconnection on shutdown.
    Also starts and stops the background job scheduler.
    """
    # Startup: Connect to database
    logging.info("🔄 Connecting to database...")
    await Database.connect()
    logging.info("✅ Database connected successfully")
    
    # Start background scheduler for auto-close jobs
    db = Database.get_database()
    start_scheduler(db)
    
    # Log startup completion
    logging.info("🚀 Application started successfully")
    logging.info("📊 Dashboard API available at /api/dashboard")
    logging.info("⏰ Background scheduler running (auto-close every 5 mins)")
    
    yield
    
    # Shutdown: Stop scheduler and disconnect from database
    logging.info("🔄 Shutting down application...")
    shutdown_scheduler()
    await Database.disconnect()
    logging.info("👋 Application shutdown complete")


app = FastAPI(
    title="MoveInSync Assignment API",
    description="API with MongoDB database connection",
    version="0.1.0",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(auth_routes.router, prefix="/auth", tags=["Authentication"])
app.include_router(alert_routes.router, tags=["Alerts"])
app.include_router(rule_routes.router, tags=["Rules"])
app.include_router(dashboard_routes.router, tags=["Dashboard"])


@app.get("/dummy")
async def dummy_endpoint():
    """Dummy endpoint for testing."""
    return {"message": "Dummy endpoint"}


@app.get("/health")
async def health_check():
    """
    Health check endpoint that verifies database connection.

    Returns:
        dict: Health status of the application and database
    """
    try:
        # Verify database connection
        Database.get_database()
        # Ping the database to check connection
        await Database.get_client().admin.command("ping")
        return {
            "status": "healthy",
            "database": "connected",
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }


if __name__ == "__main__":
    uvicorn.run("app.main:app", host="127.0.0.1", port=6000, reload=True)

