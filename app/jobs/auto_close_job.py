"""
Auto-close scanner job for periodic alert evaluation.

This module implements the background job that scans all pending alerts
and automatically closes those that meet auto-close conditions.
"""

import logging
import traceback
from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase

from app.services.job_service import create_job_record, update_job_record
from app.services.rule_engine import evaluate_all_pending_alerts

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def auto_close_scanner(db: AsyncIOMotorDatabase) -> Dict[str, int]:
    """
    Periodic job to scan and auto-close eligible alerts.
    
    This function:
    1. Creates a job record at start
    2. Calls rule_engine.evaluate_all_pending_alerts() to process alerts
    3. Updates job record with statistics
    4. Handles errors gracefully and logs all operations
    
    The function is idempotent - safe to run multiple times without side effects.
    Individual alert processing failures are logged but don't stop the job.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        Dict[str, int]: Statistics dictionary with:
            - total_checked: Number of alerts checked
            - auto_closed: Number of alerts auto-closed
            - alerts_processed: Same as total_checked (for job record)
            - alerts_closed: Same as auto_closed (for job record)
            - alerts_escalated: Always 0 (escalation happens in real-time)
    """
    job_record = None
    stats = {
        "total_checked": 0,
        "auto_closed": 0,
        "alerts_processed": 0,
        "alerts_closed": 0,
        "alerts_escalated": 0,
    }
    errors: List[str] = []
    
    try:
        # Create job record at start
        logger.info("Starting auto-close scanner job...")
        job_record = await create_job_record("auto_close_scanner", db)
        job_id = job_record.job_id
        
        logger.info(f"Job {job_id} started - scanning for auto-close eligible alerts")
        
        # Call rule engine to evaluate all pending alerts
        try:
            evaluation_stats = await evaluate_all_pending_alerts(db)
            
            # Update stats from evaluation results
            stats["total_checked"] = evaluation_stats.get("total_checked", 0)
            stats["auto_closed"] = evaluation_stats.get("auto_closed", 0)
            stats["alerts_processed"] = stats["total_checked"]
            stats["alerts_closed"] = stats["auto_closed"]
            
            # Log summary
            logger.info(
                f"Auto-close job {job_id}: "
                f"checked {stats['total_checked']}, "
                f"closed {stats['auto_closed']}"
            )
            
        except Exception as e:
            # Log error with stack trace
            error_msg = f"Error evaluating pending alerts: {str(e)}"
            logger.error(error_msg, exc_info=True)
            errors.append(error_msg)
            
            # Log full traceback for debugging
            traceback_str = traceback.format_exc()
            logger.debug(f"Full traceback:\n{traceback_str}")
            errors.append(f"Traceback: {traceback_str[:500]}")  # Limit traceback length
            
            # Set job status to failed
            status = "failed"
            
    except Exception as e:
        # Error creating job record or other critical error
        error_msg = f"Critical error in auto-close scanner: {str(e)}"
        logger.error(error_msg, exc_info=True)
        errors.append(error_msg)
        status = "failed"
        
    finally:
        # Update job record with final statistics
        if job_record:
            try:
                # Determine final status
                if not errors:
                    status = "completed"
                
                await update_job_record(
                    job_id=job_record.job_id,
                    stats=stats,
                    status=status,
                    errors=errors,
                    db=db,
                )
                
                logger.info(
                    f"Job {job_record.job_id} completed with status: {status}"
                )
                
            except Exception as e:
                # Log error updating job record, but don't fail the function
                logger.error(
                    f"Failed to update job record {job_record.job_id}: {str(e)}",
                    exc_info=True
                )
    
    return stats

