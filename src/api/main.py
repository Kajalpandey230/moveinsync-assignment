"""FastAPI application main module."""

import uvicorn
from contextlib import asynccontextmanager
from fastapi import FastAPI

from src.database.connection import Database


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.

    Handles database connection on startup and disconnection on shutdown.
    """
    # Startup: Connect to database
    await Database.connect()
    yield
    # Shutdown: Disconnect from database
    await Database.disconnect()


app = FastAPI(
    title="MoveInSync Assignment API",
    description="API with MongoDB database connection",
    version="0.1.0",
    lifespan=lifespan,
)


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
    uvicorn.run("src.api.main:app", host="127.0.0.1", port=6000, reload=True)