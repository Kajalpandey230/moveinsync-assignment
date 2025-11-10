"""Alert service for MongoDB operations on alerts collection."""

from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import (
    AlertModel,
    AlertMetadata,
    AlertSeverity,
    AlertStateTransition,
    AlertStatus,
    SourceType,
)
from app.utils.alert_id_generator import generate_alert_id

# Default expiration days (configurable)
DEFAULT_EXPIRATION_DAYS = 7

# Default severity mapping based on source type
DEFAULT_SEVERITY_MAP = {
    SourceType.OVERSPEEDING: AlertSeverity.WARNING,
    SourceType.COMPLIANCE: AlertSeverity.INFO,
    SourceType.FEEDBACK_NEGATIVE: AlertSeverity.WARNING,
    SourceType.FEEDBACK_POSITIVE: AlertSeverity.INFO,
    SourceType.DOCUMENT_EXPIRY: AlertSeverity.WARNING,
    SourceType.SAFETY: AlertSeverity.CRITICAL,
}

# State transition rules
VALID_TRANSITIONS: Dict[AlertStatus, List[AlertStatus]] = {
    AlertStatus.OPEN: [AlertStatus.ESCALATED, AlertStatus.AUTO_CLOSED, AlertStatus.RESOLVED],
    AlertStatus.ESCALATED: [AlertStatus.AUTO_CLOSED, AlertStatus.RESOLVED],
    AlertStatus.AUTO_CLOSED: [],  # Terminal state
    AlertStatus.RESOLVED: [],  # Terminal state
}


def _pydantic_to_dict(obj) -> dict:
    """
    Convert a Pydantic model to dictionary.
    Handles both Pydantic v1 (dict()) and v2 (model_dump()).

    Args:
        obj: Pydantic model instance

    Returns:
        dict: Dictionary representation of the model
    """
    if hasattr(obj, 'model_dump'):
        return obj.model_dump()
    elif hasattr(obj, 'dict'):
        return obj.dict()
    else:
        # Fallback: if it's already a dict, return it
        return dict(obj) if isinstance(obj, dict) else {}


def _validate_state_transition(current_status: AlertStatus, new_status: AlertStatus) -> None:
    """
    Validate if a state transition is allowed.

    Args:
        current_status: Current alert status
        new_status: Desired new status

    Raises:
        HTTPException: 400 if transition is invalid
    """
    if current_status == new_status:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Alert is already in {new_status.value} status",
        )

    allowed_transitions = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed_transitions:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid state transition: {current_status.value} → {new_status.value}. "
            f"Allowed transitions: {[t.value for t in allowed_transitions]}",
        )


async def create_alert(
    alert_data: dict,
    db: AsyncIOMotorDatabase,
    expiration_days: int = DEFAULT_EXPIRATION_DAYS,
) -> AlertModel:
    """
    Create a new alert in the database.

    Generates alert_id, sets default status and severity, initializes state history,
    and calculates expiration date.

    Args:
        alert_data: Dictionary containing alert data (source_type, metadata, etc.)
        db: MongoDB database instance
        expiration_days: Number of days until alert expires (default: 7)

    Returns:
        AlertModel: Created alert model

    Raises:
        RuntimeError: If alert creation fails
    """
    try:
        # Extract source_type from alert_data
        source_type = alert_data.get("source_type")
        if isinstance(source_type, str):
            source_type = SourceType(source_type)
        elif not isinstance(source_type, SourceType):
            raise ValueError("source_type must be a SourceType enum or valid string")

        # Generate alert_id
        alert_id = await generate_alert_id(source_type, db)

        # Get default severity based on source_type
        default_severity = DEFAULT_SEVERITY_MAP.get(
            source_type, AlertSeverity.INFO
        )

        # Get severity from alert_data or use default
        severity = alert_data.get("severity", default_severity)
        if isinstance(severity, str):
            severity = AlertSeverity(severity)
        elif not isinstance(severity, AlertSeverity):
            severity = default_severity

        # Get metadata
        metadata_dict = alert_data.get("metadata", {})
        metadata = AlertMetadata(**metadata_dict)

        # Current timestamp
        now = datetime.utcnow()

        # Calculate expires_at
        expires_at = now + timedelta(days=expiration_days)

        # Create initial state transition
        initial_transition = AlertStateTransition(
            from_status=AlertStatus.OPEN,
            to_status=AlertStatus.OPEN,
            timestamp=now,
            reason="Alert created",
            triggered_by="system",
        )

        # Create alert document
        alert_doc = {
            "alert_id": alert_id,
            "source_type": source_type.value,
            "severity": severity.value,
            "status": AlertStatus.OPEN.value,
            "timestamp": now,
            "metadata": _pydantic_to_dict(metadata),
            "state_history": [_pydantic_to_dict(initial_transition)],
            "escalated_at": None,
            "closed_at": None,
            "resolved_at": None,
            "auto_close_reason": None,
            "expires_at": expires_at,
            "resolved_by": None,
            "resolution_notes": None,
            "created_at": now,
            "updated_at": None,
        }

        # Insert into alerts collection
        alerts_collection = db["alerts"]
        result = await alerts_collection.insert_one(alert_doc)

        # Fetch the created alert
        created_alert_doc = await alerts_collection.find_one({"_id": result.inserted_id})
        if not created_alert_doc:
            raise RuntimeError("Failed to retrieve created alert")

        # Convert to AlertModel
        alert = AlertModel(**created_alert_doc)
        return alert

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except PyMongoError as e:
        raise RuntimeError(f"Database error creating alert: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error creating alert: {str(e)}") from e


async def get_alert_by_id(alert_id: str, db: AsyncIOMotorDatabase) -> Optional[AlertModel]:
    """
    Get an alert by its alert_id.

    Args:
        alert_id: The alert ID to search for
        db: MongoDB database instance

    Returns:
        AlertModel if found, None otherwise

    Raises:
        RuntimeError: If database query fails
    """
    try:
        alerts_collection = db["alerts"]
        alert_doc = await alerts_collection.find_one({"alert_id": alert_id})

        if not alert_doc:
            return None

        return AlertModel(**alert_doc)

    except PyMongoError as e:
        raise RuntimeError(f"Database error retrieving alert: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error retrieving alert: {str(e)}") from e


async def list_alerts(
    filters: dict,
    skip: int,
    limit: int,
    db: AsyncIOMotorDatabase,
) -> Tuple[List[AlertModel], int]:
    """
    List alerts with filtering, sorting, and pagination.

    Supports filters: status, source_type, severity, driver_id, date_range.

    Args:
        filters: Dictionary of filter criteria
        skip: Number of documents to skip (for pagination)
        limit: Maximum number of documents to return
        db: MongoDB database instance

    Returns:
        Tuple of (list of AlertModel, total count)

    Raises:
        RuntimeError: If database query fails
    """
    try:
        alerts_collection = db["alerts"]

        # Build match filter
        match_filter: Dict = {}

        # Status filter
        if "status" in filters and filters["status"]:
            if isinstance(filters["status"], str):
                match_filter["status"] = filters["status"]
            elif isinstance(filters["status"], AlertStatus):
                match_filter["status"] = filters["status"].value

        # Source type filter
        if "source_type" in filters and filters["source_type"]:
            if isinstance(filters["source_type"], str):
                match_filter["source_type"] = filters["source_type"]
            elif isinstance(filters["source_type"], SourceType):
                match_filter["source_type"] = filters["source_type"].value

        # Severity filter
        if "severity" in filters and filters["severity"]:
            if isinstance(filters["severity"], str):
                match_filter["severity"] = filters["severity"]
            elif isinstance(filters["severity"], AlertSeverity):
                match_filter["severity"] = filters["severity"].value

        # Driver ID filter (from metadata)
        if "driver_id" in filters and filters["driver_id"]:
            match_filter["metadata.driver_id"] = filters["driver_id"]

        # Date range filter
        if "date_range" in filters and filters["date_range"]:
            date_range = filters["date_range"]
            if isinstance(date_range, dict):
                if "start_date" in date_range:
                    match_filter.setdefault("timestamp", {})["$gte"] = date_range["start_date"]
                if "end_date" in date_range:
                    match_filter.setdefault("timestamp", {})["$lte"] = date_range["end_date"]

        # Build aggregation pipeline
        pipeline = [
            {"$match": match_filter} if match_filter else {"$match": {}},
            {"$sort": {"timestamp": -1}},  # Sort by timestamp descending
            {
                "$facet": {
                    "data": [
                        {"$skip": skip},
                        {"$limit": limit},
                    ],
                    "total": [{"$count": "count"}],
                }
            },
        ]

        # Execute aggregation
        cursor = alerts_collection.aggregate(pipeline)
        result = await cursor.to_list(length=1)
        if not result:
            return [], 0

        aggregation_result = result[0]
        alert_docs = aggregation_result.get("data", [])
        total_count = (
            aggregation_result.get("total", [{}])[0].get("count", 0)
            if aggregation_result.get("total")
            else 0
        )

        # Convert to AlertModel list
        alerts = [AlertModel(**doc) for doc in alert_docs]

        return alerts, total_count

    except PyMongoError as e:
        raise RuntimeError(f"Database error listing alerts: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error listing alerts: {str(e)}") from e


async def update_alert_status(
    alert_id: str,
    new_status: AlertStatus,
    reason: str,
    triggered_by: str,
    rule_id: Optional[str],
    db: AsyncIOMotorDatabase,
) -> AlertModel:
    """
    Update alert status with state transition validation.

    Validates state transitions, creates state history entry, updates timestamps,
    and sets severity to CRITICAL if escalated.

    Args:
        alert_id: Alert ID to update
        new_status: New status to transition to
        reason: Reason for the status change
        triggered_by: User or system that triggered the change
        rule_id: Optional rule ID that triggered the transition
        db: MongoDB database instance

    Returns:
        AlertModel: Updated alert model

    Raises:
        HTTPException: 400 if transition is invalid, 404 if alert not found
        RuntimeError: If database update fails
    """
    try:
        alerts_collection = db["alerts"]

        # Get current alert
        alert_doc = await alerts_collection.find_one({"alert_id": alert_id})
        if not alert_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        alert = AlertModel(**alert_doc)
        current_status = alert.status

        # Validate state transition
        _validate_state_transition(current_status, new_status)

        # Current timestamp
        now = datetime.utcnow()

        # Create state transition entry
        transition = AlertStateTransition(
            from_status=current_status,
            to_status=new_status,
            timestamp=now,
            reason=reason,
            triggered_by=triggered_by,
            rule_triggered=rule_id,
        )

        # Build $set fields
        set_fields: Dict = {
            "status": new_status.value,
            "updated_at": now,
        }

        # Update timestamps based on status
        if new_status == AlertStatus.ESCALATED:
            set_fields["escalated_at"] = now
            set_fields["severity"] = AlertSeverity.CRITICAL.value
        elif new_status == AlertStatus.AUTO_CLOSED:
            set_fields["closed_at"] = now
            if reason:
                set_fields["auto_close_reason"] = reason
        elif new_status == AlertStatus.RESOLVED:
            set_fields["resolved_at"] = now

        # Build update document
        update_doc: Dict = {
            "$set": set_fields,
            "$push": {"state_history": _pydantic_to_dict(transition)},
        }

        # Update alert in database
        result = await alerts_collection.update_one(
            {"alert_id": alert_id},
            update_doc,
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        # Fetch updated alert
        updated_alert_doc = await alerts_collection.find_one({"alert_id": alert_id})
        if not updated_alert_doc:
            raise RuntimeError("Failed to retrieve updated alert")

        return AlertModel(**updated_alert_doc)

    except HTTPException:
        raise
    except PyMongoError as e:
        raise RuntimeError(f"Database error updating alert status: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error updating alert status: {str(e)}") from e


async def add_resolution(
    alert_id: str,
    notes: str,
    user_id: str,
    db: AsyncIOMotorDatabase,
) -> AlertModel:
    """
    Add resolution to an alert.

    Sets status to RESOLVED, updates resolved_by, resolved_at, and resolution_notes,
    and adds state transition to history.

    Args:
        alert_id: Alert ID to resolve
        notes: Resolution notes
        user_id: User ID who resolved the alert
        db: MongoDB database instance

    Returns:
        AlertModel: Updated alert model

    Raises:
        HTTPException: 400 if alert cannot be resolved, 404 if alert not found
        RuntimeError: If database update fails
    """
    try:
        alerts_collection = db["alerts"]

        # Get current alert
        alert_doc = await alerts_collection.find_one({"alert_id": alert_id})
        if not alert_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        alert = AlertModel(**alert_doc)
        current_status = alert.status

        # Validate state transition to RESOLVED
        _validate_state_transition(current_status, AlertStatus.RESOLVED)

        # Current timestamp
        now = datetime.utcnow()

        # Create state transition entry
        transition = AlertStateTransition(
            from_status=current_status,
            to_status=AlertStatus.RESOLVED,
            timestamp=now,
            reason=f"Alert resolved by user {user_id}",
            triggered_by=user_id,
        )

        # Update alert
        update_doc = {
            "$set": {
                "status": AlertStatus.RESOLVED.value,
                "resolved_by": user_id,
                "resolved_at": now,
                "resolution_notes": notes,
                "updated_at": now,
            },
            "$push": {"state_history": _pydantic_to_dict(transition)},
        }

        result = await alerts_collection.update_one(
            {"alert_id": alert_id},
            update_doc,
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        # Fetch updated alert
        updated_alert_doc = await alerts_collection.find_one({"alert_id": alert_id})
        if not updated_alert_doc:
            raise RuntimeError("Failed to retrieve updated alert")

        return AlertModel(**updated_alert_doc)

    except HTTPException:
        raise
    except PyMongoError as e:
        raise RuntimeError(f"Database error adding resolution: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error adding resolution: {str(e)}") from e

