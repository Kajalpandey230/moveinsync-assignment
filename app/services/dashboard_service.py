"""
Dashboard service for aggregating alert analytics and statistics.

This module provides efficient MongoDB aggregation pipelines for dashboard data,
including summaries, trends, top offenders, and activity feeds.
"""

import logging
import time
from datetime import datetime, timedelta
from typing import Dict, List

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import (
    AlertModel,
    AlertSeverity,
    AlertStatus,
    AlertSummary,
    RecentActivity,
    SourceType,
    TopOffender,
    TrendDataPoint,
)

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Performance threshold for logging slow queries (in seconds)
SLOW_QUERY_THRESHOLD = 1.0


def _log_query_performance(query_name: str, start_time: float) -> None:
    """Log query execution time if it exceeds threshold."""
    execution_time = time.time() - start_time
    if execution_time > SLOW_QUERY_THRESHOLD:
        logger.warning(
            f"Slow query detected: {query_name} took {execution_time:.2f}s "
            f"(threshold: {SLOW_QUERY_THRESHOLD}s)"
        )
    else:
        logger.debug(f"Query {query_name} completed in {execution_time:.2f}s")


async def get_alert_summary(db: AsyncIOMotorDatabase) -> AlertSummary:
    """
    Get overall alert statistics using efficient aggregation.
    
    Uses MongoDB $facet stage to get all counts in a single query for performance.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        AlertSummary: Summary statistics with all counts
        
    Raises:
        RuntimeError: If aggregation fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        # Use $facet to get all counts in one query
        pipeline = [
            {
                "$facet": {
                    "total": [{"$count": "count"}],
                    "by_severity": [
                        {
                            "$group": {
                                "_id": "$severity",
                                "count": {"$sum": 1}
                            }
                        }
                    ],
                    "by_status": [
                        {
                            "$group": {
                                "_id": "$status",
                                "count": {"$sum": 1}
                            }
                        }
                    ]
                }
            }
        ]
        
        cursor = alerts_collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        
        if not result or not result[0]:
            return AlertSummary()
        
        data = result[0]
        
        # Extract total count
        total_alerts = data["total"][0]["count"] if data["total"] else 0
        
        # Extract severity counts
        severity_counts = {item["_id"]: item["count"] for item in data["by_severity"]}
        critical_count = severity_counts.get(AlertSeverity.CRITICAL.value, 0)
        warning_count = severity_counts.get(AlertSeverity.WARNING.value, 0)
        info_count = severity_counts.get(AlertSeverity.INFO.value, 0)
        
        # Extract status counts
        status_counts = {item["_id"]: item["count"] for item in data["by_status"]}
        open_count = status_counts.get(AlertStatus.OPEN.value, 0)
        escalated_count = status_counts.get(AlertStatus.ESCALATED.value, 0)
        auto_closed_count = status_counts.get(AlertStatus.AUTO_CLOSED.value, 0)
        resolved_count = status_counts.get(AlertStatus.RESOLVED.value, 0)
        
        summary = AlertSummary(
            total_alerts=total_alerts,
            critical_count=critical_count,
            warning_count=warning_count,
            info_count=info_count,
            open_count=open_count,
            escalated_count=escalated_count,
            auto_closed_count=auto_closed_count,
            resolved_count=resolved_count,
        )
        
        _log_query_performance("get_alert_summary", start_time)
        return summary
        
    except PyMongoError as e:
        logger.error(f"Database error getting alert summary: {str(e)}")
        raise RuntimeError(f"Failed to get alert summary: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting alert summary: {str(e)}")
        raise RuntimeError(f"Failed to get alert summary: {str(e)}") from e


async def get_top_offenders(
    limit: int, db: AsyncIOMotorDatabase
) -> List[TopOffender]:
    """
    Get top N drivers with most active alerts.
    
    Aggregates alerts by driver_id, counting open and escalated alerts,
    and returns drivers sorted by escalated alerts first, then open alerts.
    
    Args:
        limit: Maximum number of offenders to return
        db: MongoDB database instance
        
    Returns:
        List[TopOffender]: List of top offenders sorted by alert counts
        
    Raises:
        RuntimeError: If aggregation fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        pipeline = [
            # Match only active alerts
            {
                "$match": {
                    "status": {"$in": [AlertStatus.OPEN.value, AlertStatus.ESCALATED.value]},
                    "metadata.driver_id": {"$exists": True, "$ne": None}
                }
            },
            # Group by driver_id
            {
                "$group": {
                    "_id": "$metadata.driver_id",
                    "open_alerts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", AlertStatus.OPEN.value]}, 1, 0]
                        }
                    },
                    "escalated_alerts": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", AlertStatus.ESCALATED.value]}, 1, 0]
                        }
                    },
                    "total_alerts": {"$sum": 1},
                    "last_alert_time": {"$max": "$timestamp"}
                }
            },
            # Calculate total alerts
            {
                "$addFields": {
                    "total_alerts": {
                        "$add": ["$open_alerts", "$escalated_alerts"]
                    }
                }
            },
            # Sort by escalated first, then open
            {
                "$sort": {
                    "escalated_alerts": -1,
                    "open_alerts": -1
                }
            },
            # Limit results
            {"$limit": limit}
        ]
        
        cursor = alerts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        
        offenders = []
        for doc in results:
            driver_id = doc["_id"]
            if not driver_id:  # Filter out null driver_ids
                continue
                
            offender = TopOffender(
                driver_id=driver_id,
                driver_name=None,  # TODO: Join with drivers collection if available
                open_alerts=doc.get("open_alerts", 0),
                escalated_alerts=doc.get("escalated_alerts", 0),
                total_alerts=doc.get("total_alerts", 0),
                last_alert_time=doc.get("last_alert_time", datetime.utcnow())
            )
            offenders.append(offender)
        
        _log_query_performance("get_top_offenders", start_time)
        return offenders
        
    except PyMongoError as e:
        logger.error(f"Database error getting top offenders: {str(e)}")
        raise RuntimeError(f"Failed to get top offenders: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting top offenders: {str(e)}")
        raise RuntimeError(f"Failed to get top offenders: {str(e)}") from e


async def get_recent_activities(
    limit: int, db: AsyncIOMotorDatabase
) -> List[RecentActivity]:
    """
    Get recent alert state transitions.
    
    Unwinds the state_history array and returns the most recent transitions
    across all alerts.
    
    Args:
        limit: Maximum number of activities to return
        db: MongoDB database instance
        
    Returns:
        List[RecentActivity]: List of recent state transitions
        
    Raises:
        RuntimeError: If aggregation fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        # Map status transitions to action names
        def map_action(to_status: str) -> str:
            """Map status to action name."""
            status_map = {
                AlertStatus.OPEN.value: "created",
                AlertStatus.ESCALATED.value: "escalated",
                AlertStatus.AUTO_CLOSED.value: "auto_closed",
                AlertStatus.RESOLVED.value: "resolved",
            }
            return status_map.get(to_status, to_status.lower())
        
        pipeline = [
            # Match alerts with state history
            {
                "$match": {
                    "state_history": {"$exists": True, "$ne": []}
                }
            },
            # Unwind state_history array
            {"$unwind": "$state_history"},
            # Project required fields
            {
                "$project": {
                    "alert_id": 1,
                    "source_type": 1,
                    "severity": 1,
                    "status": 1,
                    "driver_id": "$metadata.driver_id",
                    "timestamp": "$state_history.timestamp",
                    "to_status": "$state_history.to_status",
                    "reason": "$state_history.reason"
                }
            },
            # Sort by timestamp descending
            {"$sort": {"timestamp": -1}},
            # Limit results
            {"$limit": limit}
        ]
        
        cursor = alerts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=limit)
        
        activities = []
        for doc in results:
            to_status = doc.get("to_status", "")
            action = map_action(to_status)
            
            # Parse enums safely
            source_type_str = doc.get("source_type", "")
            try:
                source_type = SourceType(source_type_str)
            except ValueError:
                source_type = SourceType.OVERSPEEDING  # Default fallback
            
            severity_str = doc.get("severity", AlertSeverity.INFO.value)
            try:
                severity = AlertSeverity(severity_str)
            except ValueError:
                severity = AlertSeverity.INFO  # Default fallback
            
            status_str = doc.get("status", AlertStatus.OPEN.value)
            try:
                status = AlertStatus(status_str)
            except ValueError:
                status = AlertStatus.OPEN  # Default fallback
            
            activity = RecentActivity(
                alert_id=doc.get("alert_id", ""),
                source_type=source_type,
                severity=severity,
                status=status,
                driver_id=doc.get("driver_id"),
                timestamp=doc.get("timestamp", datetime.utcnow()),
                action=action,
                reason=doc.get("reason")
            )
            activities.append(activity)
        
        _log_query_performance("get_recent_activities", start_time)
        return activities
        
    except PyMongoError as e:
        logger.error(f"Database error getting recent activities: {str(e)}")
        raise RuntimeError(f"Failed to get recent activities: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting recent activities: {str(e)}")
        raise RuntimeError(f"Failed to get recent activities: {str(e)}") from e


async def get_auto_closed_alerts(
    hours: int, db: AsyncIOMotorDatabase
) -> List[AlertModel]:
    """
    Get recently auto-closed alerts.
    
    Queries alerts that were auto-closed within the specified time window.
    
    Args:
        hours: Number of hours to look back
        db: MongoDB database instance
        
    Returns:
        List[AlertModel]: List of auto-closed alerts
        
    Raises:
        RuntimeError: If query fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        # Calculate cutoff time
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        
        # Query auto-closed alerts
        query = {
            "status": AlertStatus.AUTO_CLOSED.value,
            "closed_at": {"$gte": cutoff_time}
        }
        
        # Sort by closed_at descending
        cursor = alerts_collection.find(query).sort("closed_at", -1)
        results = await cursor.to_list(length=None)
        
        alerts = [AlertModel(**doc) for doc in results]
        
        _log_query_performance("get_auto_closed_alerts", start_time)
        return alerts
        
    except PyMongoError as e:
        logger.error(f"Database error getting auto-closed alerts: {str(e)}")
        raise RuntimeError(f"Failed to get auto-closed alerts: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting auto-closed alerts: {str(e)}")
        raise RuntimeError(f"Failed to get auto-closed alerts: {str(e)}") from e


async def get_trend_data(
    days: int, db: AsyncIOMotorDatabase
) -> List[TrendDataPoint]:
    """
    Get daily alert trends.
    
    Aggregates alerts by date and counts total, escalated, auto-closed, and resolved.
    
    Args:
        days: Number of days to look back
        db: MongoDB database instance
        
    Returns:
        List[TrendDataPoint]: List of daily trend data points
        
    Raises:
        RuntimeError: If aggregation fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        # Calculate date range
        start_date = datetime.utcnow() - timedelta(days=days)
        
        pipeline = [
            # Match alerts within date range
            {
                "$match": {
                    "timestamp": {"$gte": start_date}
                }
            },
            # Group by date
            {
                "$group": {
                    "_id": {
                        "$dateToString": {
                            "format": "%Y-%m-%d",
                            "date": "$timestamp"
                        }
                    },
                    "total_alerts": {"$sum": 1},
                    "escalated": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", AlertStatus.ESCALATED.value]}, 1, 0]
                        }
                    },
                    "auto_closed": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", AlertStatus.AUTO_CLOSED.value]}, 1, 0]
                        }
                    },
                    "resolved": {
                        "$sum": {
                            "$cond": [{"$eq": ["$status", AlertStatus.RESOLVED.value]}, 1, 0]
                        }
                    }
                }
            },
            # Sort by date ascending
            {"$sort": {"_id": 1}}
        ]
        
        cursor = alerts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        trend_points = []
        for doc in results:
            trend_point = TrendDataPoint(
                date=doc["_id"],
                total_alerts=doc.get("total_alerts", 0),
                escalated=doc.get("escalated", 0),
                auto_closed=doc.get("auto_closed", 0),
                resolved=doc.get("resolved", 0)
            )
            trend_points.append(trend_point)
        
        _log_query_performance("get_trend_data", start_time)
        return trend_points
        
    except PyMongoError as e:
        logger.error(f"Database error getting trend data: {str(e)}")
        raise RuntimeError(f"Failed to get trend data: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting trend data: {str(e)}")
        raise RuntimeError(f"Failed to get trend data: {str(e)}") from e


async def get_source_distribution(
    db: AsyncIOMotorDatabase
) -> Dict[str, int]:
    """
    Get alert counts by source type.
    
    Aggregates alerts grouped by source_type and returns counts.
    
    Args:
        db: MongoDB database instance
        
    Returns:
        Dict[str, int]: Dictionary mapping source_type to count
        
    Raises:
        RuntimeError: If aggregation fails
    """
    start_time = time.time()
    
    try:
        alerts_collection = db["alerts"]
        
        pipeline = [
            {
                "$group": {
                    "_id": "$source_type",
                    "count": {"$sum": 1}
                }
            }
        ]
        
        cursor = alerts_collection.aggregate(pipeline)
        results = await cursor.to_list(length=None)
        
        distribution = {doc["_id"]: doc["count"] for doc in results}
        
        _log_query_performance("get_source_distribution", start_time)
        return distribution
        
    except PyMongoError as e:
        logger.error(f"Database error getting source distribution: {str(e)}")
        raise RuntimeError(f"Failed to get source distribution: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error getting source distribution: {str(e)}")
        raise RuntimeError(f"Failed to get source distribution: {str(e)}") from e

