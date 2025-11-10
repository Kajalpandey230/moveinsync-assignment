"""
Background job service for managing job execution records.

This module provides functions to create, update, and query background job records
in MongoDB for tracking scheduled task executions.
"""

import logging
import secrets
from datetime import datetime
from typing import List, Optional

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import BackgroundJobModel

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def generate_job_id() -> str:
    """
    Generate a unique job ID.
    
    Format: JOB-{timestamp}-{random_hex}
    
    Returns:
        str: Unique job identifier
    """
    timestamp = datetime.utcnow().strftime("%Y%m%d-%H%M%S")
    random_hex = secrets.token_hex(4)
    return f"JOB-{timestamp}-{random_hex}"


async def create_job_record(
    job_type: str, db: AsyncIOMotorDatabase
) -> BackgroundJobModel:
    """
    Create a new background job record.
    
    Creates a job record with status="running" and started_at=now.
    Inserts the record into the background_jobs collection.
    
    Args:
        job_type: Type of job (e.g., "auto_close_scanner", "rule_evaluator")
        db: MongoDB database instance
        
    Returns:
        BackgroundJobModel: Created job record
        
    Raises:
        RuntimeError: If job creation fails
    """
    try:
        job_id = generate_job_id()
        started_at = datetime.utcnow()
        
        job_data = BackgroundJobModel(
            job_id=job_id,
            job_type=job_type,
            status="running",
            started_at=started_at,
            alerts_processed=0,
            alerts_closed=0,
            alerts_escalated=0,
            errors=[],
        )
        
        # Convert to dict for MongoDB insertion
        job_dict = job_data.model_dump(by_alias=True, exclude={"id"})
        
        # Insert into database
        jobs_collection = db["background_jobs"]
        result = await jobs_collection.insert_one(job_dict)
        
        # Set the MongoDB _id
        job_data.id = result.inserted_id
        
        logger.info(
            f"Created job record: {job_id} (type: {job_type})"
        )
        
        return job_data
        
    except PyMongoError as e:
        logger.error(f"Database error creating job record: {str(e)}")
        raise RuntimeError(f"Failed to create job record: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error creating job record: {str(e)}")
        raise RuntimeError(f"Failed to create job record: {str(e)}") from e


async def update_job_record(
    job_id: str,
    stats: dict,
    status: str,
    errors: List[str],
    db: AsyncIOMotorDatabase,
) -> None:
    """
    Update a background job record with completion information.
    
    Updates the job record with:
    - alerts_processed, alerts_closed, alerts_escalated from stats
    - status ("completed" or "failed")
    - completed_at = now
    - execution_time_ms = (completed_at - started_at) in milliseconds
    - errors list
    
    Args:
        job_id: Job identifier to update
        stats: Dictionary with keys: alerts_processed, alerts_closed, alerts_escalated
        status: Job status ("completed" or "failed")
        errors: List of error messages
        db: MongoDB database instance
        
    Raises:
        RuntimeError: If job update fails
        ValueError: If job_id not found
    """
    try:
        jobs_collection = db["background_jobs"]
        
        # Find the job to get started_at
        job_doc = await jobs_collection.find_one({"job_id": job_id})
        
        if not job_doc:
            raise ValueError(f"Job with ID {job_id} not found")
        
        # Calculate execution time
        started_at = job_doc.get("started_at")
        completed_at = datetime.utcnow()
        
        execution_time_ms = None
        if started_at:
            # Motor returns datetime objects, but handle edge cases
            if isinstance(started_at, datetime):
                delta = completed_at - started_at
            else:
                # Handle case where started_at might be stored as string or other format
                try:
                    if isinstance(started_at, str):
                        # Try parsing ISO format string
                        started_dt = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                    else:
                        # Assume it's already a datetime-like object
                        started_dt = started_at
                    delta = completed_at - started_dt
                except (ValueError, TypeError) as e:
                    logger.warning(f"Could not parse started_at for job {job_id}: {e}")
                    delta = None
            
            if delta is not None:
                execution_time_ms = delta.total_seconds() * 1000  # Convert to milliseconds
        
        # Build update document
        update_doc = {
            "$set": {
                "status": status,
                "completed_at": completed_at,
                "execution_time_ms": execution_time_ms,
                "alerts_processed": stats.get("alerts_processed", 0),
                "alerts_closed": stats.get("alerts_closed", 0),
                "alerts_escalated": stats.get("alerts_escalated", 0),
                "errors": errors,
            }
        }
        
        # Update the job record
        result = await jobs_collection.update_one(
            {"job_id": job_id},
            update_doc
        )
        
        if result.matched_count == 0:
            raise ValueError(f"Job with ID {job_id} not found for update")
        
        logger.info(
            f"Updated job record: {job_id} - Status: {status}, "
            f"Processed: {stats.get('alerts_processed', 0)}, "
            f"Closed: {stats.get('alerts_closed', 0)}, "
            f"Time: {execution_time_ms:.2f}ms"
        )
        
    except ValueError:
        raise
    except PyMongoError as e:
        logger.error(f"Database error updating job record {job_id}: {str(e)}")
        raise RuntimeError(f"Failed to update job record: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error updating job record {job_id}: {str(e)}")
        raise RuntimeError(f"Failed to update job record: {str(e)}") from e


async def get_recent_jobs(
    limit: int, db: AsyncIOMotorDatabase
) -> List[BackgroundJobModel]:
    """
    Get recent job records.
    
    Queries the last N jobs, sorted by started_at descending.
    
    Args:
        limit: Maximum number of jobs to return
        db: MongoDB database instance
        
    Returns:
        List[BackgroundJobModel]: List of job records, most recent first
        
    Raises:
        RuntimeError: If query fails
    """
    try:
        jobs_collection = db["background_jobs"]
        
        # Query and sort by started_at descending
        cursor = jobs_collection.find().sort("started_at", -1).limit(limit)
        job_docs = await cursor.to_list(length=limit)
        
        # Convert to BackgroundJobModel
        jobs = [BackgroundJobModel(**doc) for doc in job_docs]
        
        logger.debug(f"Retrieved {len(jobs)} recent job records")
        
        return jobs
        
    except PyMongoError as e:
        logger.error(f"Database error retrieving recent jobs: {str(e)}")
        raise RuntimeError(f"Failed to retrieve recent jobs: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error retrieving recent jobs: {str(e)}")
        raise RuntimeError(f"Failed to retrieve recent jobs: {str(e)}") from e

