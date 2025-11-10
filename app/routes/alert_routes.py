"""Alert management routes for creating, listing, and managing alerts."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.database.connection import Database
from src.database.models import (
    AlertModel,
    AlertMetadata,
    AlertSeverity,
    AlertStateTransition,
    AlertStatus,
    SourceType,
)
from app.services.alert_service import (
    add_resolution,
    create_alert,
    get_alert_by_id,
    list_alerts,
    update_alert_status,
)

router = APIRouter(prefix="/api/alerts", tags=["Alerts"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class CreateAlertRequest(BaseModel):
    """Request model for creating a new alert."""

    source_type: SourceType = Field(..., description="Source type of the alert")
    metadata: AlertMetadata = Field(..., description="Alert metadata")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "source_type": "OVERSPEEDING",
                "metadata": {
                    "driver_id": "DRV001",
                    "vehicle_id": "VEH123",
                    "speed": 85.5,
                    "speed_limit": 60.0,
                    "location": "MG Road, Bangalore",
                },
            }
        }


class AlertResponse(BaseModel):
    """Response model for alert data."""

    id: Optional[str] = Field(None, description="Alert database ID")
    alert_id: str = Field(..., description="Unique alert identifier")
    source_type: SourceType = Field(..., description="Source type of the alert")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    status: AlertStatus = Field(..., description="Current alert status")
    timestamp: datetime = Field(..., description="Alert creation timestamp")
    metadata: AlertMetadata = Field(..., description="Alert metadata")
    state_history: List[AlertStateTransition] = Field(
        default_factory=list, description="History of state transitions"
    )
    escalated_at: Optional[datetime] = Field(None, description="Escalation timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    auto_close_reason: Optional[str] = Field(None, description="Reason for auto-closure")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration time")
    resolved_by: Optional[str] = Field(None, description="User who resolved the alert")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class AlertListResponse(BaseModel):
    """Response model for alert list with pagination."""

    alerts: List[AlertResponse] = Field(..., description="List of alerts")
    total: int = Field(..., description="Total number of alerts matching filters")
    skip: int = Field(..., description="Number of alerts skipped")
    limit: int = Field(..., description="Maximum number of alerts returned")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "alerts": [],
                "total": 0,
                "skip": 0,
                "limit": 50,
            }
        }


class UpdateStatusRequest(BaseModel):
    """Request model for updating alert status."""

    new_status: AlertStatus = Field(..., description="New status to transition to")
    reason: str = Field(..., min_length=1, description="Reason for status change")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "new_status": "ESCALATED",
                "reason": "Multiple incidents detected within time window",
            }
        }


class ResolveAlertRequest(BaseModel):
    """Request model for resolving an alert."""

    resolution_notes: str = Field(..., min_length=1, description="Resolution notes")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "resolution_notes": "Issue resolved by contacting driver and updating route",
            }
        }


class StateHistoryResponse(BaseModel):
    """Response model for alert state history."""

    state_history: List[AlertStateTransition] = Field(
        ..., description="History of state transitions"
    )

    class Config:
        """Pydantic configuration."""

        from_attributes = True


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def alert_model_to_response(alert: AlertModel) -> AlertResponse:
    """
    Convert AlertModel to AlertResponse.

    Args:
        alert: AlertModel instance

    Returns:
        AlertResponse: Alert response model
    """
    return AlertResponse(
        id=str(alert.id) if alert.id else None,
        alert_id=alert.alert_id,
        source_type=alert.source_type,
        severity=alert.severity,
        status=alert.status,
        timestamp=alert.timestamp,
        metadata=alert.metadata,
        state_history=alert.state_history,
        escalated_at=alert.escalated_at,
        closed_at=alert.closed_at,
        resolved_at=alert.resolved_at,
        auto_close_reason=alert.auto_close_reason,
        expires_at=alert.expires_at,
        resolved_by=alert.resolved_by,
        resolution_notes=alert.resolution_notes,
        created_at=alert.created_at,
        updated_at=alert.updated_at,
    )


# ============================================================================
# ALERT ENDPOINTS
# ============================================================================


@router.post(
    "",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new alert",
    description="Create a new alert. No authentication required.",
)
async def create_new_alert(
    request: CreateAlertRequest,
):
    """
    Create a new alert.

    Validates source_type, creates alert using alert_service, and optionally
    triggers rule engine for real-time escalation.

    Args:
        request: Alert creation request data

    Returns:
        AlertResponse: Created alert information

    Raises:
        HTTPException: 400 if validation fails, 500 if creation fails
    """
    try:
        # Get database
        db = Database.get_database()

        # Prepare alert data - convert metadata to dict
        # Use model_dump() for Pydantic v2, with fallback to dict() for v1
        if hasattr(request.metadata, 'model_dump'):
            metadata_dict = request.metadata.model_dump()
        else:
            # Fallback for Pydantic v1
            metadata_dict = request.metadata.dict()

        alert_data = {
            "source_type": request.source_type,
            "metadata": metadata_dict,
        }

        # Create alert
        created_alert = await create_alert(alert_data, db)

        # Call rule engine for real-time escalation
        try:
            from app.services.rule_engine import check_and_escalate

            await check_and_escalate(created_alert, db)
        except Exception as e:
            # Log error but don't fail the alert creation
            # The escalation can be retried later
            import logging

            logger = logging.getLogger(__name__)
            logger.warning(
                f"Failed to check escalation for alert {created_alert.alert_id}: {str(e)}"
            )

        return alert_model_to_response(created_alert)

    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create alert: {str(e)}",
        )


@router.get(
    "",
    response_model=AlertListResponse,
    status_code=status.HTTP_200_OK,
    summary="List alerts",
    description="List alerts with filtering and pagination. No authentication required.",
)
async def list_alerts_endpoint(
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    source_type: Optional[SourceType] = Query(None, description="Filter by source type"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by severity"),
    driver_id: Optional[str] = Query(None, description="Filter by driver ID"),
    skip: int = Query(0, ge=0, description="Number of alerts to skip"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of alerts to return"),
):
    """
    List alerts with filtering and pagination.

    Args:
        status: Optional status filter
        source_type: Optional source type filter
        severity: Optional severity filter
        driver_id: Optional driver ID filter
        skip: Number of alerts to skip (pagination)
        limit: Maximum number of alerts to return

    Returns:
        AlertListResponse: List of alerts with pagination info
    """
    try:
        # Get database
        db = Database.get_database()

        # Build filters dict
        filters = {}
        if status:
            filters["status"] = status
        if source_type:
            filters["source_type"] = source_type
        if severity:
            filters["severity"] = severity
        if driver_id:
            filters["driver_id"] = driver_id

        # Call alert service
        alerts, total_count = await list_alerts(filters, skip, limit, db)

        # Convert to response models
        alert_responses = [alert_model_to_response(alert) for alert in alerts]

        return AlertListResponse(
            alerts=alert_responses,
            total=total_count,
            skip=skip,
            limit=limit,
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list alerts: {str(e)}",
        )


@router.patch(
    "/{alert_id}/status",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Update alert status",
    description="Update the status of an alert. No authentication required.",
)
async def update_status(
    alert_id: str,
    request: UpdateStatusRequest,
):
    """
    Update alert status.

    Args:
        alert_id: Alert ID to update
        request: Status update request data

    Returns:
        AlertResponse: Updated alert information

    Raises:
        HTTPException: 400 if transition is invalid, 404 if alert not found
    """
    try:
        # Get database
        db = Database.get_database()

        # Update alert status
        updated_alert = await update_alert_status(
            alert_id=alert_id,
            new_status=request.new_status,
            reason=request.reason,
            triggered_by="system",
            rule_id=None,
            db=db,
        )

        return alert_model_to_response(updated_alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update alert status: {str(e)}",
        )


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve an alert",
    description="Resolve an alert with resolution notes. No authentication required.",
)
async def resolve_alert(
    alert_id: str,
    request: ResolveAlertRequest,
):
    """
    Resolve an alert.

    Args:
        alert_id: Alert ID to resolve
        request: Resolution request data

    Returns:
        AlertResponse: Updated alert information

    Raises:
        HTTPException: 400 if alert cannot be resolved, 404 if alert not found
    """
    try:
        # Get database
        db = Database.get_database()

        # Add resolution
        updated_alert = await add_resolution(
            alert_id=alert_id,
            notes=request.resolution_notes,
            user_id="system",
            db=db,
        )

        return alert_model_to_response(updated_alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to resolve alert: {str(e)}",
        )


@router.get(
    "/{alert_id}/history",
    response_model=StateHistoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get alert state history",
    description="Get the state transition history of an alert. No authentication required.",
)
async def get_alert_history(
    alert_id: str
):
    """
    Get alert state history.

    Args:
        alert_id: Alert ID to get history for

    Returns:
        StateHistoryResponse: Alert state history

    Raises:
        HTTPException: 404 if alert not found
    """
    try:
        # Get database
        db = Database.get_database()

        # Get alert
        alert = await get_alert_by_id(alert_id, db)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        return StateHistoryResponse(state_history=alert.state_history)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert history: {str(e)}",
        )


@router.get(
    "/{alert_id}",
    response_model=AlertResponse,
    status_code=status.HTTP_200_OK,
    summary="Get alert by ID",
    description="Get a specific alert by its ID. No authentication required.",
)
async def get_alert(alert_id: str):
    """
    Get an alert by its ID.

    Args:
        alert_id: Alert ID to retrieve

    Returns:
        AlertResponse: Alert information with full state history

    Raises:
        HTTPException: 404 if alert not found
    """
    try:
        # Get database
        db = Database.get_database()

        # Get alert
        alert = await get_alert_by_id(alert_id, db)

        if not alert:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Alert with ID {alert_id} not found",
            )

        return alert_model_to_response(alert)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve alert: {str(e)}",
        )

