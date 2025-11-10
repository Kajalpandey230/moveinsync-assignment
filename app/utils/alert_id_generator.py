"""Alert ID generator using MongoDB atomic counters."""

from datetime import datetime
from typing import Dict

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import SourceType


# Prefix mapping for source types
SOURCE_PREFIX_MAP: Dict[SourceType, str] = {
    SourceType.OVERSPEEDING: "OSP",
    SourceType.COMPLIANCE: "CMP",
    SourceType.FEEDBACK_NEGATIVE: "FBN",
    SourceType.FEEDBACK_POSITIVE: "FBP",
    SourceType.DOCUMENT_EXPIRY: "DOC",
    SourceType.SAFETY: "SAF",
}


async def generate_alert_id(source_type: SourceType, db: AsyncIOMotorDatabase) -> str:
    """
    Generate a unique alert ID using atomic MongoDB counter operations.

    Format: {PREFIX}-{YEAR}-{SEQUENCE}
    Example: "OSP-2025-00001" for OVERSPEEDING

    Uses MongoDB's find_one_and_update for thread-safe atomic sequence generation.

    Args:
        source_type: The source type of the alert
        db: MongoDB database instance (AsyncIOMotorDatabase)

    Returns:
        str: Generated alert ID in format {PREFIX}-{YEAR}-{SEQUENCE}

    Raises:
        ValueError: If source_type is not in the prefix mapping
        RuntimeError: If counter operation fails
    """
    # Validate source type
    if source_type not in SOURCE_PREFIX_MAP:
        raise ValueError(f"Unknown source type: {source_type}")

    # Get prefix for source type
    prefix = SOURCE_PREFIX_MAP[source_type]

    # Get current year
    current_year = datetime.utcnow().year

    # Create counter document ID
    counter_id = f"alert_{prefix}_{current_year}"

    # Get counters collection
    counters_collection = db["counters"]

    try:
        # Atomic increment operation using find_one_and_update
        # This ensures thread-safety even with concurrent requests
        # $inc will create the document with sequence=1 if it doesn't exist,
        # or increment the existing sequence if it does
        result = await counters_collection.find_one_and_update(
            {"_id": counter_id},
            {"$inc": {"sequence": 1}},  # Increment sequence atomically
            upsert=True,  # Create document if it doesn't exist
            return_document=True,  # Return the updated document
        )

        # Extract sequence number
        # result should never be None with upsert=True, but handle it defensively
        if result is None:
            # Fallback: try to get the document directly
            result = await counters_collection.find_one({"_id": counter_id})
            if result is None:
                raise RuntimeError("Failed to create or retrieve counter document")
            sequence = result.get("sequence", 1)
        else:
            sequence = result.get("sequence", 1)

        # Zero-pad sequence to 5 digits
        sequence_str = str(sequence).zfill(5)

        # Generate alert ID
        alert_id = f"{prefix}-{current_year}-{sequence_str}"

        return alert_id

    except PyMongoError as e:
        raise RuntimeError(f"Failed to generate alert ID: {str(e)}") from e
    except Exception as e:
        raise RuntimeError(f"Unexpected error generating alert ID: {str(e)}") from e

