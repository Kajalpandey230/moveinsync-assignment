"""
Background scheduler setup using APScheduler.

This module configures and manages the APScheduler instance for running
periodic background jobs, specifically the auto-close scanner.
"""

import asyncio
import logging
from typing import Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from motor.motor_asyncio import AsyncIOMotorDatabase

from app.jobs.auto_close_job import auto_close_scanner

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Global scheduler instance
scheduler: Optional[BackgroundScheduler] = None


def _run_async_job(db: AsyncIOMotorDatabase) -> None:
    """
    Wrapper function to run async job in scheduler.
    
    APScheduler runs jobs in threads, so we need to create a new event loop
    for each execution of the async function.
    
    Args:
        db: MongoDB database instance
    """
    try:
        # Create new event loop for this thread
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        # Run the async function
        loop.run_until_complete(auto_close_scanner(db))
        
    except Exception as e:
        logger.error(f"Error running async job in scheduler: {str(e)}", exc_info=True)
    finally:
        # Clean up event loop
        try:
            loop.close()
        except Exception:
            pass


def start_scheduler(db: AsyncIOMotorDatabase) -> None:
    """
    Start the background scheduler.
    
    Initializes APScheduler and adds the auto-close scanner job
    that runs every 5 minutes.
    
    Args:
        db: MongoDB database instance
        
    Raises:
        RuntimeError: If scheduler fails to start
    """
    global scheduler
    
    if scheduler is not None and scheduler.running:
        logger.warning("Scheduler already running - skipping start")
        return
    
    try:
        # Create new scheduler instance
        scheduler = BackgroundScheduler()
        
        # Add auto-close job - runs every 5 minutes
        scheduler.add_job(
            func=lambda: _run_async_job(db),
            trigger=IntervalTrigger(minutes=5),
            id='auto_close_scanner',
            name='Auto-close alert scanner',
            replace_existing=True,
            max_instances=1,  # Prevent overlapping executions
            coalesce=True,    # Combine multiple pending executions
        )
        
        # Start the scheduler
        scheduler.start()
        
        logger.info("✅ Background scheduler started - auto-close runs every 5 mins")
        
        # Log next run time
        job = scheduler.get_job('auto_close_scanner')
        if job:
            next_run = job.next_run_time
            logger.info(f"Next auto-close scan scheduled for: {next_run}")
        
    except Exception as e:
        logger.error(f"Failed to start scheduler: {str(e)}", exc_info=True)
        scheduler = None
        raise RuntimeError(f"Failed to start scheduler: {str(e)}") from e


def shutdown_scheduler() -> None:
    """
    Gracefully shutdown the scheduler.
    
    Stops all scheduled jobs and shuts down the scheduler instance.
    """
    global scheduler
    
    if scheduler is None:
        logger.debug("Scheduler not running - nothing to shutdown")
        return
    
    try:
        if scheduler.running:
            scheduler.shutdown(wait=True)
            logger.info("Background scheduler shut down gracefully")
        else:
            logger.debug("Scheduler was not running")
        
        scheduler = None
        
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {str(e)}", exc_info=True)
        scheduler = None


def is_scheduler_running() -> bool:
    """
    Check if scheduler is currently running.
    
    Returns:
        bool: True if scheduler is running, False otherwise
    """
    return scheduler is not None and scheduler.running


def get_scheduler_status() -> dict:
    """
    Get current scheduler status information.
    
    Returns:
        dict: Status information including:
            - running: Whether scheduler is running
            - jobs: List of scheduled jobs with next run times
    """
    if scheduler is None or not scheduler.running:
        return {
            "running": False,
            "jobs": [],
        }
    
    jobs = []
    for job in scheduler.get_jobs():
        jobs.append({
            "id": job.id,
            "name": job.name,
            "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        })
    
    return {
        "running": True,
        "jobs": jobs,
    }

