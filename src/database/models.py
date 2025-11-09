"""Database models and schemas for MongoDB collections."""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field
from bson import ObjectId
from enum import Enum


class PyObjectId(ObjectId):
    """Custom ObjectId type for Pydantic models."""

    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")


# ============================================================================
# ENUMS
# ============================================================================

class AlertStatus(str, Enum):
    """Alert status enumeration."""
    OPEN = "OPEN"
    ESCALATED = "ESCALATED"
    AUTO_CLOSED = "AUTO_CLOSED"
    RESOLVED = "RESOLVED"


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class SourceType(str, Enum):
    """Alert source types."""
    OVERSPEEDING = "OVERSPEEDING"
    COMPLIANCE = "COMPLIANCE"
    FEEDBACK_NEGATIVE = "FEEDBACK_NEGATIVE"
    FEEDBACK_POSITIVE = "FEEDBACK_POSITIVE"
    DOCUMENT_EXPIRY = "DOCUMENT_EXPIRY"
    SAFETY = "SAFETY"


class UserRole(str, Enum):
    """User roles for authentication."""
    ADMIN = "ADMIN"
    OPERATOR = "OPERATOR"
    VIEWER = "VIEWER"


# ============================================================================
# ALERT MODELS
# ============================================================================

class AlertMetadata(BaseModel):
    """Flexible metadata structure for alerts."""
    driver_id: Optional[str] = Field(None, description="Driver identifier")
    vehicle_id: Optional[str] = Field(None, description="Vehicle identifier")
    speed: Optional[float] = Field(None, description="Speed value for overspeeding")
    speed_limit: Optional[float] = Field(None, description="Speed limit exceeded")
    location: Optional[str] = Field(None, description="Location of incident")
    document_type: Optional[str] = Field(None, description="Type of document (license, insurance, etc)")
    expiry_date: Optional[datetime] = Field(None, description="Document expiry date")
    document_valid: Optional[bool] = Field(None, description="Document validity status")
    feedback_rating: Optional[int] = Field(None, ge=1, le=5, description="Feedback rating")
    feedback_comment: Optional[str] = Field(None, description="Feedback comment")
    event_count: Optional[int] = Field(default=1, description="Number of similar events")
    additional_data: Optional[Dict[str, Any]] = Field(default={}, description="Additional metadata")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "driver_id": "DRV001",
                "vehicle_id": "VEH123",
                "speed": 85.5,
                "speed_limit": 60.0,
                "location": "MG Road, Bangalore",
                "event_count": 1
            }
        }


class AlertStateTransition(BaseModel):
    """Alert state transition history entry."""
    from_status: AlertStatus = Field(..., description="Previous status")
    to_status: AlertStatus = Field(..., description="New status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Transition timestamp")
    reason: Optional[str] = Field(None, description="Reason for state change")
    triggered_by: Optional[str] = Field(None, description="User or system that triggered change")
    rule_triggered: Optional[str] = Field(None, description="Rule that triggered the transition")

    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "from_status": "OPEN",
                "to_status": "ESCALATED",
                "timestamp": "2025-11-09T10:30:00",
                "reason": "3 overspeeding incidents within 1 hour",
                "triggered_by": "system",
                "rule_triggered": "overspeeding_escalation"
            }
        }


class AlertModel(BaseModel):
    """Alert model schema."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    alert_id: str = Field(..., description="Unique alert identifier")
    source_type: SourceType = Field(..., description="Source type of the alert")
    severity: AlertSeverity = Field(..., description="Alert severity level")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Current alert status")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Alert creation timestamp")
    metadata: AlertMetadata = Field(..., description="Alert metadata")
    
    # State management
    state_history: List[AlertStateTransition] = Field(
        default_factory=list,
        description="History of state transitions"
    )
    escalated_at: Optional[datetime] = Field(None, description="Escalation timestamp")
    closed_at: Optional[datetime] = Field(None, description="Closure timestamp")
    resolved_at: Optional[datetime] = Field(None, description="Resolution timestamp")
    
    # Auto-closure tracking
    auto_close_reason: Optional[str] = Field(None, description="Reason for auto-closure")
    expires_at: Optional[datetime] = Field(None, description="Alert expiration time")
    
    # Manual resolution
    resolved_by: Optional[str] = Field(None, description="User who resolved the alert")
    resolution_notes: Optional[str] = Field(None, description="Resolution notes")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "alert_id": "ALT-2025-001",
                "source_type": "OVERSPEEDING",
                "severity": "WARNING",
                "status": "OPEN",
                "metadata": {
                    "driver_id": "DRV001",
                    "vehicle_id": "VEH123",
                    "speed": 85.5,
                    "speed_limit": 60.0,
                    "location": "MG Road, Bangalore"
                }
            }
        }


# ============================================================================
# RULE ENGINE MODELS
# ============================================================================

class EscalationCondition(BaseModel):
    """Escalation condition for rule engine."""
    escalate_if_count: Optional[int] = Field(None, description="Number of events to trigger escalation")
    window_mins: Optional[int] = Field(None, description="Time window in minutes")
    auto_close_if: Optional[str] = Field(None, description="Condition for auto-closure")
    expire_after_mins: Optional[int] = Field(None, description="Auto-expire after minutes")
    
    class Config:
        """Pydantic configuration."""
        json_schema_extra = {
            "example": {
                "escalate_if_count": 3,
                "window_mins": 60
            }
        }


class RuleModel(BaseModel):
    """Rule configuration model."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    rule_id: str = Field(..., description="Unique rule identifier")
    source_type: SourceType = Field(..., description="Alert source type this rule applies to")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    
    # Rule conditions
    conditions: EscalationCondition = Field(..., description="Escalation/closure conditions")
    
    # Rule metadata
    is_active: bool = Field(default=True, description="Whether the rule is active")
    priority: int = Field(default=1, description="Rule priority (higher = more important)")
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "rule_id": "RULE-OVERSPEED-001",
                "source_type": "OVERSPEEDING",
                "name": "Overspeeding Escalation Rule",
                "description": "Escalate if 3 overspeeding incidents within 1 hour",
                "conditions": {
                    "escalate_if_count": 3,
                    "window_mins": 60
                },
                "is_active": True,
                "priority": 1
            }
        }


# ============================================================================
# USER & AUTHENTICATION MODELS
# ============================================================================

class UserModel(BaseModel):
    """User model schema for authentication."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    email: str = Field(..., description="User's email address")
    hashed_password: str = Field(..., description="Hashed password")
    full_name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    role: UserRole = Field(default=UserRole.VIEWER, description="User role")
    
    is_active: bool = Field(default=True, description="Whether the user is active")
    is_verified: bool = Field(default=False, description="Whether email is verified")
    
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Creation timestamp")
    updated_at: Optional[datetime] = Field(default=None, description="Last update timestamp")
    last_login: Optional[datetime] = Field(default=None, description="Last login timestamp")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "username": "operator1",
                "email": "operator@moveinsync.com",
                "full_name": "John Operator",
                "role": "OPERATOR",
                "is_active": True
            }
        }


# ============================================================================
# AUDIT & LOGGING MODELS
# ============================================================================

class AuditLogModel(BaseModel):
    """Audit log for tracking system activities."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    action: str = Field(..., description="Action performed")
    resource_type: str = Field(..., description="Type of resource (alert, rule, user)")
    resource_id: str = Field(..., description="ID of the resource")
    user_id: Optional[str] = Field(None, description="User who performed the action")
    details: Optional[Dict[str, Any]] = Field(default={}, description="Additional details")
    ip_address: Optional[str] = Field(None, description="IP address of requester")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="Action timestamp")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "action": "alert_escalated",
                "resource_type": "alert",
                "resource_id": "ALT-2025-001",
                "user_id": "system",
                "details": {"reason": "3 overspeeding incidents"}
            }
        }


# ============================================================================
# BACKGROUND JOB MODELS
# ============================================================================

class BackgroundJobModel(BaseModel):
    """Background job execution tracking."""
    
    id: Optional[PyObjectId] = Field(default_factory=PyObjectId, alias="_id")
    job_id: str = Field(..., description="Unique job identifier")
    job_type: str = Field(..., description="Type of job (auto_close_scanner, rule_evaluator)")
    status: str = Field(..., description="Job status (running, completed, failed)")
    
    started_at: datetime = Field(default_factory=datetime.utcnow, description="Job start time")
    completed_at: Optional[datetime] = Field(None, description="Job completion time")
    
    alerts_processed: int = Field(default=0, description="Number of alerts processed")
    alerts_closed: int = Field(default=0, description="Number of alerts auto-closed")
    alerts_escalated: int = Field(default=0, description="Number of alerts escalated")
    
    errors: List[str] = Field(default_factory=list, description="List of errors encountered")
    execution_time_ms: Optional[float] = Field(None, description="Execution time in milliseconds")

    class Config:
        """Pydantic configuration."""
        populate_by_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}
        json_schema_extra = {
            "example": {
                "job_id": "JOB-2025-001",
                "job_type": "auto_close_scanner",
                "status": "completed",
                "alerts_processed": 150,
                "alerts_closed": 12
            }
        }


# ============================================================================
# DASHBOARD AGGREGATION MODELS (Response Models)
# ============================================================================

class AlertSummary(BaseModel):
    """Alert summary for dashboard."""
    total_alerts: int = 0
    critical_count: int = 0
    warning_count: int = 0
    info_count: int = 0
    open_count: int = 0
    escalated_count: int = 0
    auto_closed_count: int = 0
    resolved_count: int = 0


class TopOffender(BaseModel):
    """Top offender entry for dashboard."""
    driver_id: str
    driver_name: Optional[str] = None
    open_alerts: int
    escalated_alerts: int
    total_alerts: int
    last_alert_time: datetime


class RecentActivity(BaseModel):
    """Recent activity entry for dashboard."""
    alert_id: str
    source_type: SourceType
    severity: AlertSeverity
    status: AlertStatus
    driver_id: Optional[str] = None
    timestamp: datetime
    action: str
    reason: Optional[str] = None


class TrendDataPoint(BaseModel):
    """Trend data point for charts."""
    date: str
    total_alerts: int
    escalated: int
    auto_closed: int
    resolved: int