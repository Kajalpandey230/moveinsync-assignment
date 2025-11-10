"""
Dashboard routes for analytics and statistics endpoints.

This module provides API endpoints for dashboard data including summaries,
trends, top offenders, and activity feeds.
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.database.connection import Database
from src.database.models import (
    AlertModel,
    AlertSummary,
    RecentActivity,
    TopOffender,
    TrendDataPoint,
)
from app.auth.dependencies import require_viewer
from app.services import dashboard_service

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


# ============================================================================
# DEPENDENCIES
# ============================================================================


async def get_database():
    """
    Dependency function to get database instance.
    
    Returns:
        AsyncIOMotorDatabase: MongoDB database instance
        
    Raises:
        HTTPException: If database is not connected
    """
    try:
        return Database.get_database()
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Database not available: {str(e)}",
        )


# ============================================================================
# DASHBOARD ENDPOINTS
# ============================================================================


@router.get(
    "/summary",
    response_model=AlertSummary,
    status_code=status.HTTP_200_OK,
    summary="Get alert summary",
    description="Get overall alert summary statistics including counts by severity and status.",
)
async def get_summary(
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get overall alert summary statistics.
    
    Returns aggregated counts for:
    - Total alerts
    - Alerts by severity (CRITICAL, WARNING, INFO)
    - Alerts by status (OPEN, ESCALATED, AUTO_CLOSED, RESOLVED)
    
    Args:
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        AlertSummary: Summary statistics
        
    Raises:
        HTTPException: 500 if aggregation fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_alert_summary(db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get alert summary: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting alert summary: {str(e)}",
        )


@router.get(
    "/top-offenders",
    response_model=List[TopOffender],
    status_code=status.HTTP_200_OK,
    summary="Get top offenders",
    description="Get top N drivers with most active alerts (OPEN or ESCALATED).",
)
async def get_top_offenders(
    limit: int = Query(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of offenders to return",
    ),
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get top N drivers with most active alerts.
    
    Returns drivers sorted by:
    1. Number of escalated alerts (descending)
    2. Number of open alerts (descending)
    
    Only includes alerts with status OPEN or ESCALATED.
    
    Args:
        limit: Maximum number of offenders to return (1-20)
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        List[TopOffender]: List of top offenders with alert counts
        
    Raises:
        HTTPException: 500 if aggregation fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_top_offenders(limit, db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get top offenders: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting top offenders: {str(e)}",
        )


@router.get(
    "/recent-activities",
    response_model=List[RecentActivity],
    status_code=status.HTTP_200_OK,
    summary="Get recent activities",
    description="Get recent alert lifecycle events and state transitions.",
)
async def get_recent_activities(
    limit: int = Query(
        default=20,
        ge=1,
        le=100,
        description="Maximum number of activities to return",
    ),
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get recent alert lifecycle events.
    
    Returns the most recent state transitions from all alerts,
    including creation, escalation, auto-closure, and resolution events.
    
    Args:
        limit: Maximum number of activities to return (1-100)
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        List[RecentActivity]: List of recent state transitions
        
    Raises:
        HTTPException: 500 if aggregation fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_recent_activities(limit, db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get recent activities: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting recent activities: {str(e)}",
        )


@router.get(
    "/auto-closed",
    response_model=List[AlertModel],
    status_code=status.HTTP_200_OK,
    summary="Get auto-closed alerts",
    description="Get recently auto-closed alerts within the specified time window.",
)
async def get_auto_closed(
    hours: int = Query(
        default=24,
        ge=1,
        le=168,
        description="Number of hours to look back (1-168, default: 24)",
    ),
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get recently auto-closed alerts.
    
    Returns alerts that were automatically closed within the specified
    number of hours, sorted by closed_at timestamp (most recent first).
    
    Args:
        hours: Number of hours to look back (1-168, default: 24)
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        List[AlertModel]: List of auto-closed alerts
        
    Raises:
        HTTPException: 500 if query fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_auto_closed_alerts(hours, db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get auto-closed alerts: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting auto-closed alerts: {str(e)}",
        )


@router.get(
    "/trends",
    response_model=List[TrendDataPoint],
    status_code=status.HTTP_200_OK,
    summary="Get alert trends",
    description="Get daily alert trend data for the specified number of days.",
)
async def get_trends(
    days: int = Query(
        default=7,
        ge=1,
        le=90,
        description="Number of days to look back (1-90, default: 7)",
    ),
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get daily alert trend data.
    
    Returns daily aggregated statistics including:
    - Total alerts per day
    - Escalated alerts per day
    - Auto-closed alerts per day
    - Resolved alerts per day
    
    Args:
        days: Number of days to look back (1-90, default: 7)
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        List[TrendDataPoint]: List of daily trend data points
        
    Raises:
        HTTPException: 500 if aggregation fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_trend_data(days, db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get trend data: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting trend data: {str(e)}",
        )


@router.get(
    "/source-distribution",
    status_code=status.HTTP_200_OK,
    summary="Get source distribution",
    description="Get alert counts grouped by source type.",
)
async def get_source_distribution(
    db=Depends(get_database),
    current_user=Depends(require_viewer),
):
    """
    Get alert distribution by source type.
    
    Returns a dictionary mapping each source type to the count of alerts
    of that type.
    
    Args:
        db: MongoDB database instance (from dependency)
        current_user: Current authenticated user (from dependency)
        
    Returns:
        Dict[str, int]: Dictionary mapping source_type to count
        
    Raises:
        HTTPException: 500 if aggregation fails, 503 if database unavailable
    """
    try:
        return await dashboard_service.get_source_distribution(db)
    except RuntimeError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get source distribution: {str(e)}",
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error getting source distribution: {str(e)}",
        )

