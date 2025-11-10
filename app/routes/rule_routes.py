"""Rule management routes for creating, listing, and managing rules."""

from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.database.connection import Database
from src.database.models import (
    EscalationCondition,
    RuleModel,
    SourceType,
)
from app.services.rule_service import (
    create_rule,
    delete_rule,
    get_active_rules_for_source,
    load_default_rules,
    update_rule,
)

router = APIRouter(prefix="/api/rules", tags=["Rules"])


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================


class RuleResponse(BaseModel):
    """Response model for rule data."""

    id: Optional[str] = Field(None, description="Rule database ID")
    rule_id: str = Field(..., description="Unique rule identifier")
    source_type: SourceType = Field(..., description="Alert source type this rule applies to")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    conditions: EscalationCondition = Field(..., description="Escalation/closure conditions")
    is_active: bool = Field(..., description="Whether the rule is active")
    priority: int = Field(..., description="Rule priority")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")

    class Config:
        """Pydantic configuration."""

        from_attributes = True


class CreateRuleRequest(BaseModel):
    """Request model for creating a new rule."""

    rule_id: str = Field(..., description="Unique rule identifier")
    source_type: SourceType = Field(..., description="Alert source type this rule applies to")
    name: str = Field(..., description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    conditions: EscalationCondition = Field(..., description="Escalation/closure conditions")
    is_active: bool = Field(default=True, description="Whether the rule is active")
    priority: int = Field(default=1, description="Rule priority")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "rule_id": "RULE-OVERSPEED-001",
                "source_type": "OVERSPEEDING",
                "name": "Overspeeding Escalation Rule",
                "description": "Escalate if 3 overspeeding incidents within 1 hour",
                "conditions": {
                    "escalate_if_count": 3,
                    "window_mins": 60,
                },
                "is_active": True,
                "priority": 1,
            }
        }


class UpdateRuleRequest(BaseModel):
    """Request model for updating a rule."""

    name: Optional[str] = Field(None, description="Rule name")
    description: Optional[str] = Field(None, description="Rule description")
    conditions: Optional[EscalationCondition] = Field(None, description="Escalation/closure conditions")
    is_active: Optional[bool] = Field(None, description="Whether the rule is active")
    priority: Optional[int] = Field(None, description="Rule priority")
    source_type: Optional[SourceType] = Field(None, description="Alert source type")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "is_active": False,
                "priority": 2,
            }
        }


class LoadDefaultsResponse(BaseModel):
    """Response model for loading default rules."""

    message: str = Field(..., description="Response message")
    count: int = Field(..., description="Number of rules loaded")

    class Config:
        """Pydantic configuration."""

        json_schema_extra = {
            "example": {
                "message": "Loaded 5 rules",
                "count": 5,
            }
        }


# ============================================================================
# HELPER FUNCTIONS
# ============================================================================


def rule_model_to_response(rule: RuleModel) -> RuleResponse:
    """
    Convert RuleModel to RuleResponse.

    Args:
        rule: RuleModel instance

    Returns:
        RuleResponse: Rule response model
    """
    return RuleResponse(
        id=str(rule.id) if rule.id else None,
        rule_id=rule.rule_id,
        source_type=rule.source_type,
        name=rule.name,
        description=rule.description,
        conditions=rule.conditions,
        is_active=rule.is_active,
        priority=rule.priority,
        created_at=rule.created_at,
        updated_at=rule.updated_at,
    )


# ============================================================================
# RULE ENDPOINTS
# ============================================================================


@router.post(
    "/load-defaults",
    response_model=LoadDefaultsResponse,
    status_code=status.HTTP_200_OK,
    summary="Load default rules",
    description="Load default rules from JSON file. No authentication required.",
)
async def load_default_rules_endpoint():
    """
    Load default rules from JSON file.

    Returns:
        LoadDefaultsResponse: Response with count of loaded rules

    Raises:
        HTTPException: 500 if loading fails
    """
    try:
        # Get database
        db = Database.get_database()

        # Load default rules
        count = await load_default_rules(db)

        return LoadDefaultsResponse(
            message=f"Loaded {count} rules",
            count=count,
        )

    except FileNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Default rules file not found: {str(e)}",
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to load default rules: {str(e)}",
        )


@router.get(
    "",
    response_model=List[RuleResponse],
    status_code=status.HTTP_200_OK,
    summary="List rules",
    description="List rules with optional filtering. No authentication required.",
)
async def list_rules(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    source_type: Optional[SourceType] = Query(None, description="Filter by source type"),
):
    """
    List rules with optional filtering.

    Args:
        is_active: Optional filter for active status
        source_type: Optional filter for source type

    Returns:
        List[RuleResponse]: List of rules
    """
    try:
        # Get database
        db = Database.get_database()
        rules_collection = db["rules"]

        # Build query
        query = {}
        if is_active is not None:
            query["is_active"] = is_active
        if source_type:
            query["source_type"] = source_type.value

        # Query rules
        cursor = rules_collection.find(query).sort("priority", -1)
        rule_docs = await cursor.to_list(length=None)

        # Convert to RuleModel and then to RuleResponse
        rules = [RuleModel(**doc) for doc in rule_docs]
        rule_responses = [rule_model_to_response(rule) for rule in rules]

        return rule_responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list rules: {str(e)}",
        )


@router.get(
    "/{rule_id}",
    response_model=RuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get rule by ID",
    description="Get a specific rule by its ID. No authentication required.",
)
async def get_rule(rule_id: str):
    """
    Get a rule by its ID.

    Args:
        rule_id: Rule ID to retrieve

    Returns:
        RuleResponse: Rule information

    Raises:
        HTTPException: 404 if rule not found
    """
    try:
        # Get database
        db = Database.get_database()
        rules_collection = db["rules"]

        # Find rule by rule_id
        rule_doc = await rules_collection.find_one({"rule_id": rule_id})

        if not rule_doc:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found",
            )

        rule = RuleModel(**rule_doc)
        return rule_model_to_response(rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve rule: {str(e)}",
        )


@router.post(
    "",
    response_model=RuleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new rule",
    description="Create a new rule. No authentication required.",
)
async def create_rule_endpoint(
    request: CreateRuleRequest,
):
    """
    Create a new rule.

    Args:
        request: Rule creation request data

    Returns:
        RuleResponse: Created rule information

    Raises:
        HTTPException: 400 if rule_id already exists, 500 if creation fails
    """
    try:
        # Get database
        db = Database.get_database()

        # Create RuleModel from request
        rule_data = RuleModel(
            rule_id=request.rule_id,
            source_type=request.source_type,
            name=request.name,
            description=request.description,
            conditions=request.conditions,
            is_active=request.is_active,
            priority=request.priority,
        )

        # Create rule
        created_rule = await create_rule(rule_data, db)

        return rule_model_to_response(created_rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rule: {str(e)}",
        )


@router.put(
    "/{rule_id}",
    response_model=RuleResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a rule",
    description="Update an existing rule. No authentication required.",
)
async def update_rule_endpoint(
    rule_id: str,
    request: UpdateRuleRequest,
):
    """
    Update an existing rule.

    Args:
        rule_id: Rule ID to update
        request: Rule update request data

    Returns:
        RuleResponse: Updated rule information

    Raises:
        HTTPException: 404 if rule not found, 400 if update data is invalid
    """
    try:
        # Get database
        db = Database.get_database()

        # Build updates dict (exclude None values)
        updates = {}
        if request.name is not None:
            updates["name"] = request.name
        if request.description is not None:
            updates["description"] = request.description
        if request.conditions is not None:
            updates["conditions"] = request.conditions.model_dump()
        if request.is_active is not None:
            updates["is_active"] = request.is_active
        if request.priority is not None:
            updates["priority"] = request.priority
        if request.source_type is not None:
            updates["source_type"] = request.source_type

        if not updates:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No fields to update",
            )

        # Update rule
        updated_rule = await update_rule(rule_id, updates, db)

        return rule_model_to_response(updated_rule)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rule: {str(e)}",
        )


@router.delete(
    "/{rule_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a rule",
    description="Delete a rule by its ID. No authentication required.",
)
async def delete_rule_endpoint(
    rule_id: str
):
    """
    Delete a rule.

    Args:
        rule_id: Rule ID to delete

    Returns:
        None (204 No Content)

    Raises:
        HTTPException: 500 if deletion fails
    """
    try:
        # Get database
        db = Database.get_database()

        # Delete rule
        deleted = await delete_rule(rule_id, db)

        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found",
            )

        return None

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete rule: {str(e)}",
        )


@router.get(
    "/active/{source_type}",
    response_model=List[RuleResponse],
    status_code=status.HTTP_200_OK,
    summary="Get active rules for source type",
    description="Get all active rules for a specific source type. No authentication required.",
)
async def get_active_rules_for_source_endpoint(
    source_type: SourceType,
):
    """
    Get all active rules for a specific source type.

    Args:
        source_type: Source type to filter by

    Returns:
        List[RuleResponse]: List of active rules for the source type
    """
    try:
        # Get database
        db = Database.get_database()

        # Get active rules for source type
        rules = await get_active_rules_for_source(source_type, db)

        # Convert to response models
        rule_responses = [rule_model_to_response(rule) for rule in rules]

        return rule_responses

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve active rules: {str(e)}",
        )

