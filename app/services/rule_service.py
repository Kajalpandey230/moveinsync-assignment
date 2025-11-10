"""Rule service for MongoDB operations on rules collection."""

import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import EscalationCondition, RuleModel, SourceType

# Cache for active rules with TTL
_active_rules_cache: Optional[Dict[SourceType, List[RuleModel]]] = None
_cache_timestamp: Optional[datetime] = None
CACHE_TTL_MINUTES = 5


def _clear_cache() -> None:
    """Clear the active rules cache."""
    global _active_rules_cache, _cache_timestamp
    _active_rules_cache = None
    _cache_timestamp = None


def _is_cache_valid() -> bool:
    """Check if the cache is still valid (within TTL)."""
    global _cache_timestamp
    if _cache_timestamp is None:
        return False
    return datetime.utcnow() - _cache_timestamp < timedelta(minutes=CACHE_TTL_MINUTES)


async def load_default_rules(db: AsyncIOMotorDatabase) -> int:
    """
    Load default rules from JSON file into database.

    Reads app/config/default_rules.json, parses JSON, and inserts rules
    that don't already exist in the database.

    Args:
        db: MongoDB database instance

    Returns:
        int: Number of rules inserted

    Raises:
        FileNotFoundError: If default_rules.json file is not found
        json.JSONDecodeError: If JSON parsing fails
        RuntimeError: If database operations fail
    """
    try:
        # Get path to default_rules.json
        config_path = Path(__file__).parent.parent / "config" / "default_rules.json"

        # Read and parse JSON file
        if not config_path.exists():
            raise FileNotFoundError(f"Default rules file not found: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        if "rules" not in data:
            raise ValueError("Invalid JSON structure: 'rules' key not found")

        rules_data = data["rules"]
        if not isinstance(rules_data, list):
            raise ValueError("Invalid JSON structure: 'rules' must be an array")

        # Get rules collection
        rules_collection = db["rules"]

        inserted_count = 0

        # Process each rule
        for rule_dict in rules_data:
            try:
                rule_id = rule_dict.get("rule_id")
                if not rule_id:
                    continue  # Skip rules without rule_id

                # Check if rule already exists
                existing_rule = await rules_collection.find_one({"rule_id": rule_id})
                if existing_rule:
                    continue  # Skip if already exists

                # Convert source_type string to enum
                source_type_str = rule_dict.get("source_type")
                if isinstance(source_type_str, str):
                    source_type = SourceType(source_type_str)
                else:
                    continue  # Skip if invalid source_type

                # Create EscalationCondition from conditions dict
                conditions_dict = rule_dict.get("conditions", {})
                conditions = EscalationCondition(**conditions_dict)

                # Create rule document
                rule_doc = {
                    "rule_id": rule_id,
                    "source_type": source_type.value,
                    "name": rule_dict.get("name", ""),
                    "description": rule_dict.get("description"),
                    "conditions": conditions.model_dump(),
                    "is_active": rule_dict.get("is_active", True),
                    "priority": rule_dict.get("priority", 1),
                    "created_at": datetime.utcnow(),
                    "updated_at": None,
                }

                # Insert into database
                await rules_collection.insert_one(rule_doc)
                inserted_count += 1

            except (ValueError, KeyError) as e:
                # Skip invalid rule entries
                continue
            except PyMongoError as e:
                # Log error but continue with other rules
                continue

        # Clear cache after loading
        _clear_cache()

        return inserted_count

    except FileNotFoundError as e:
        raise FileNotFoundError(f"Default rules file not found: {str(e)}") from e
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in default rules file: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Failed to load default rules: {str(e)}") from e


async def get_active_rules_for_source(
    source_type: SourceType, db: AsyncIOMotorDatabase
) -> List[RuleModel]:
    """
    Get all active rules for a specific source type.

    Queries rules collection for active rules matching the source type,
    sorted by priority descending.

    Args:
        source_type: Source type to filter by
        db: MongoDB database instance

    Returns:
        List[RuleModel]: List of active rules for the source type

    Raises:
        RuntimeError: If database query fails
    """
    try:
        rules_collection = db["rules"]

        # Query active rules for source type
        cursor = rules_collection.find(
            {"source_type": source_type.value, "is_active": True}
        ).sort("priority", -1)

        rule_docs = await cursor.to_list(length=None)

        # Convert to RuleModel list
        rules = [RuleModel(**doc) for doc in rule_docs]

        return rules

    except PyMongoError as e:
        raise RuntimeError(f"Database error retrieving rules: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error retrieving rules: {str(e)}") from e


async def get_all_active_rules(
    db: AsyncIOMotorDatabase,
) -> Dict[SourceType, List[RuleModel]]:
    """
    Get all active rules grouped by source type.

    Uses in-memory cache with 5-minute TTL for performance.
    Queries database if cache is invalid or missing.

    Args:
        db: MongoDB database instance

    Returns:
        Dict[SourceType, List[RuleModel]]: Dictionary mapping source types to their rules

    Raises:
        RuntimeError: If database query fails
    """
    global _active_rules_cache, _cache_timestamp

    # Check if cache is valid
    if _active_rules_cache is not None and _is_cache_valid():
        return _active_rules_cache

    try:
        rules_collection = db["rules"]

        # Query all active rules, sorted by priority descending
        cursor = rules_collection.find({"is_active": True}).sort("priority", -1)

        rule_docs = await cursor.to_list(length=None)

        # Convert to RuleModel list
        rules = [RuleModel(**doc) for doc in rule_docs]

        # Group by source_type
        grouped_rules: Dict[SourceType, List[RuleModel]] = {}
        for rule in rules:
            source_type = rule.source_type
            if source_type not in grouped_rules:
                grouped_rules[source_type] = []
            grouped_rules[source_type].append(rule)

        # Update cache
        _active_rules_cache = grouped_rules
        _cache_timestamp = datetime.utcnow()

        return grouped_rules

    except PyMongoError as e:
        raise RuntimeError(f"Database error retrieving all active rules: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error retrieving all active rules: {str(e)}") from e


async def create_rule(rule_data: RuleModel, db: AsyncIOMotorDatabase) -> RuleModel:
    """
    Create a new rule in the database.

    Checks if rule_id already exists and raises error if duplicate.

    Args:
        rule_data: RuleModel instance to create
        db: MongoDB database instance

    Returns:
        RuleModel: Created rule model

    Raises:
        HTTPException: 400 if rule_id already exists
        RuntimeError: If database operation fails
    """
    try:
        rules_collection = db["rules"]

        # Check if rule_id already exists
        existing_rule = await rules_collection.find_one({"rule_id": rule_data.rule_id})
        if existing_rule:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Rule with ID {rule_data.rule_id} already exists",
            )

        # Create rule document
        rule_doc = {
            "rule_id": rule_data.rule_id,
            "source_type": rule_data.source_type.value,
            "name": rule_data.name,
            "description": rule_data.description,
            "conditions": rule_data.conditions.model_dump(),
            "is_active": rule_data.is_active,
            "priority": rule_data.priority,
            "created_at": datetime.utcnow(),
            "updated_at": None,
        }

        # Insert into database
        result = await rules_collection.insert_one(rule_doc)

        # Fetch the created rule
        created_rule_doc = await rules_collection.find_one({"_id": result.inserted_id})
        if not created_rule_doc:
            raise RuntimeError("Failed to retrieve created rule")

        # Clear cache
        _clear_cache()

        return RuleModel(**created_rule_doc)

    except HTTPException:
        raise
    except PyMongoError as e:
        raise RuntimeError(f"Database error creating rule: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error creating rule: {str(e)}") from e


async def update_rule(
    rule_id: str, updates: dict, db: AsyncIOMotorDatabase
) -> RuleModel:
    """
    Update an existing rule.

    Updates specified fields and sets updated_at timestamp.

    Args:
        rule_id: Rule ID to update
        updates: Dictionary of fields to update
        db: MongoDB database instance

    Returns:
        RuleModel: Updated rule model

    Raises:
        HTTPException: 404 if rule not found
        RuntimeError: If database operation fails
    """
    try:
        rules_collection = db["rules"]

        # Find rule by rule_id
        existing_rule = await rules_collection.find_one({"rule_id": rule_id})
        if not existing_rule:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found",
            )

        # Prepare update document
        update_doc: Dict = {
            "updated_at": datetime.utcnow(),
        }

        # Add fields from updates dict
        allowed_fields = {
            "name",
            "description",
            "conditions",
            "is_active",
            "priority",
            "source_type",
        }

        for key, value in updates.items():
            if key in allowed_fields:
                if key == "conditions" and isinstance(value, dict):
                    # Convert conditions dict to EscalationCondition
                    update_doc["conditions"] = EscalationCondition(**value).model_dump()
                elif key == "source_type":
                    # Convert source_type to enum value
                    if isinstance(value, str):
                        update_doc["source_type"] = SourceType(value).value
                    elif isinstance(value, SourceType):
                        update_doc["source_type"] = value.value
                else:
                    update_doc[key] = value

        # Update rule in database
        result = await rules_collection.update_one(
            {"rule_id": rule_id}, {"$set": update_doc}
        )

        if result.matched_count == 0:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Rule with ID {rule_id} not found",
            )

        # Fetch updated rule
        updated_rule_doc = await rules_collection.find_one({"rule_id": rule_id})
        if not updated_rule_doc:
            raise RuntimeError("Failed to retrieve updated rule")

        # Clear cache
        _clear_cache()

        return RuleModel(**updated_rule_doc)

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid update data: {str(e)}",
        )
    except PyMongoError as e:
        raise RuntimeError(f"Database error updating rule: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error updating rule: {str(e)}") from e


async def delete_rule(rule_id: str, db: AsyncIOMotorDatabase) -> bool:
    """
    Delete a rule by rule_id.

    Args:
        rule_id: Rule ID to delete
        db: MongoDB database instance

    Returns:
        bool: True if rule was deleted, False if not found

    Raises:
        RuntimeError: If database operation fails
    """
    try:
        rules_collection = db["rules"]

        # Delete rule
        result = await rules_collection.delete_one({"rule_id": rule_id})

        # Clear cache
        _clear_cache()

        return result.deleted_count > 0

    except PyMongoError as e:
        raise RuntimeError(f"Database error deleting rule: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error deleting rule: {str(e)}") from e

