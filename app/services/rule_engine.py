"""Rule engine for evaluating rules and triggering escalations/auto-closures."""

import logging
from datetime import datetime, timedelta
from typing import Dict, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo.errors import PyMongoError

from src.database.models import AlertModel, AlertStatus, SourceType
from app.services.alert_service import update_alert_status
from app.services.rule_service import get_active_rules_for_source

# Configure logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


async def _get_similar_alerts_count(
    driver_id: str,
    source_type: SourceType,
    window_mins: int,
    db: AsyncIOMotorDatabase,
    exclude_alert_id: Optional[str] = None,
) -> int:
    """
    Get count of similar alerts for a driver within a time window.

    Queries alerts matching:
    - Same driver_id
    - Same source_type
    - Status in [OPEN, ESCALATED]
    - Timestamp within window (current_time - window_mins)

    Args:
        driver_id: Driver ID to filter by
        source_type: Source type to filter by
        window_mins: Time window in minutes
        db: MongoDB database instance
        exclude_alert_id: Optional alert ID to exclude from count

    Returns:
        int: Count of matching alerts
    """
    try:
        alerts_collection = db["alerts"]

        # Calculate time window start
        window_start = datetime.utcnow() - timedelta(minutes=window_mins)

        # Build query
        query = {
            "metadata.driver_id": driver_id,
            "source_type": source_type.value,
            "status": {"$in": [AlertStatus.OPEN.value, AlertStatus.ESCALATED.value]},
            "timestamp": {"$gte": window_start},
        }

        # Exclude specific alert if provided
        if exclude_alert_id:
            query["alert_id"] = {"$ne": exclude_alert_id}

        # Count matching alerts
        count = await alerts_collection.count_documents(query)

        logger.info(
            f"Found {count} similar alerts for driver {driver_id}, "
            f"source_type {source_type.value}, window {window_mins} mins"
        )

        return count

    except PyMongoError as e:
        logger.error(f"Database error counting similar alerts: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error counting similar alerts: {str(e)}")
        raise


async def check_and_escalate(
    alert: AlertModel, db: AsyncIOMotorDatabase
) -> bool:
    """
    Check escalation conditions and escalate alert if criteria are met.

    Evaluates active rules for the alert's source type and escalates if
    the count of similar alerts within the time window meets the threshold.

    Args:
        alert: Alert model to check
        db: MongoDB database instance

    Returns:
        bool: True if alert was escalated, False otherwise
    """
    try:
        # Prevent duplicate escalation
        if alert.status == AlertStatus.ESCALATED:
            logger.info(f"Alert {alert.alert_id} already escalated, skipping")
            return False

        # Get driver_id from metadata
        driver_id = alert.metadata.driver_id if alert.metadata else None
        if not driver_id:
            logger.warning(
                f"Alert {alert.alert_id} has no driver_id, cannot check escalation"
            )
            return False

        # Get active rules for source type
        rules = await get_active_rules_for_source(alert.source_type, db)

        if not rules:
            logger.info(
                f"No active rules found for source_type {alert.source_type.value}"
            )
            return False

        logger.info(
            f"Checking escalation for alert {alert.alert_id}, "
            f"driver {driver_id}, {len(rules)} active rules"
        )

        # Evaluate each rule with escalate_if_count
        for rule in rules:
            try:
                # Check if rule has escalation condition
                if not rule.conditions.escalate_if_count:
                    continue

                escalate_count = rule.conditions.escalate_if_count
                window_mins = rule.conditions.window_mins or 60  # Default 60 mins

                # Get count of similar alerts
                similar_count = await _get_similar_alerts_count(
                    driver_id=driver_id,
                    source_type=alert.source_type,
                    window_mins=window_mins,
                    db=db,
                    exclude_alert_id=alert.alert_id,
                )

                # Include current alert in count
                total_count = similar_count + 1

                logger.info(
                    f"Rule {rule.rule_id}: {total_count} alerts found "
                    f"(threshold: {escalate_count}, window: {window_mins} mins)"
                )

                # Check if threshold is met
                if total_count >= escalate_count:
                    reason = (
                        f"{total_count} {alert.source_type.value} incidents "
                        f"detected within {window_mins} minutes "
                        f"(threshold: {escalate_count})"
                    )

                    logger.info(
                        f"Escalating alert {alert.alert_id} due to rule {rule.rule_id}: {reason}"
                    )

                    # Update alert status to ESCALATED
                    updated_alert = await update_alert_status(
                        alert_id=alert.alert_id,
                        new_status=AlertStatus.ESCALATED,
                        reason=reason,
                        triggered_by="system",
                        rule_id=rule.rule_id,
                        db=db,
                    )

                    logger.info(
                        f"Alert {alert.alert_id} escalated successfully. "
                        f"New status: {updated_alert.status.value}"
                    )

                    return True

            except Exception as e:
                # Log error but continue with other rules
                logger.error(
                    f"Error evaluating rule {rule.rule_id} for alert {alert.alert_id}: {str(e)}"
                )
                continue

        logger.info(f"No escalation triggered for alert {alert.alert_id}")
        return False

    except Exception as e:
        logger.error(f"Error checking escalation for alert {alert.alert_id}: {str(e)}")
        return False


async def check_auto_close_conditions(
    alert: AlertModel, db: AsyncIOMotorDatabase
) -> Tuple[bool, Optional[str]]:
    """
    Check if alert should be auto-closed based on conditions or expiration.

    Evaluates active rules for auto-close conditions and checks expiration.

    Args:
        alert: Alert model to check
        db: MongoDB database instance

    Returns:
        Tuple[bool, Optional[str]]: (should_close, reason) if should close,
                                    (False, None) otherwise
    """
    try:
        # Skip if already closed or resolved
        if alert.status in [AlertStatus.AUTO_CLOSED, AlertStatus.RESOLVED]:
            logger.info(
                f"Alert {alert.alert_id} already in terminal state: {alert.status.value}"
            )
            return False, None

        # Get active rules for source type
        rules = await get_active_rules_for_source(alert.source_type, db)

        # Check rule-based auto-close conditions
        for rule in rules:
            try:
                auto_close_condition = rule.conditions.auto_close_if
                if not auto_close_condition:
                    continue

                logger.info(
                    f"Checking auto-close condition '{auto_close_condition}' "
                    f"for alert {alert.alert_id} (rule: {rule.rule_id})"
                )

                # Check document_valid condition
                if auto_close_condition == "document_valid":
                    if alert.metadata and alert.metadata.document_valid is True:
                        reason = f"Document renewed (rule: {rule.rule_id})"
                        logger.info(
                            f"Auto-close condition met for alert {alert.alert_id}: {reason}"
                        )
                        return True, reason

                # Add more conditions here as needed
                # Example:
                # elif auto_close_condition == "other_condition":
                #     if some_check:
                #         return True, "Reason"

            except Exception as e:
                # Log error but continue with other rules
                logger.error(
                    f"Error checking auto-close condition for rule {rule.rule_id}: {str(e)}"
                )
                continue

        # Check expiration
        if alert.expires_at:
            now = datetime.utcnow()
            if alert.expires_at <= now:
                reason = f"Time window expired (expired at: {alert.expires_at})"
                logger.info(
                    f"Alert {alert.alert_id} expired: {reason}"
                )
                return True, reason

        return False, None

    except Exception as e:
        logger.error(
            f"Error checking auto-close conditions for alert {alert.alert_id}: {str(e)}"
        )
        return False, None


async def apply_auto_close(
    alert_id: str, reason: str, db: AsyncIOMotorDatabase
) -> AlertModel:
    """
    Apply auto-close to an alert.

    Updates alert status to AUTO_CLOSED and sets auto_close_reason.

    Args:
        alert_id: Alert ID to auto-close
        reason: Reason for auto-closure
        db: MongoDB database instance

    Returns:
        AlertModel: Updated alert model

    Raises:
        RuntimeError: If auto-close operation fails
    """
    try:
        logger.info(f"Applying auto-close to alert {alert_id}: {reason}")

        # Update alert status to AUTO_CLOSED
        # update_alert_status will set auto_close_reason when reason is provided
        updated_alert = await update_alert_status(
            alert_id=alert_id,
            new_status=AlertStatus.AUTO_CLOSED,
            reason=reason,
            triggered_by="system",
            rule_id=None,
            db=db,
        )

        logger.info(
            f"Alert {alert_id} auto-closed successfully. Status: {updated_alert.status.value}"
        )

        return updated_alert

    except Exception as e:
        logger.error(f"Error applying auto-close to alert {alert_id}: {str(e)}")
        raise RuntimeError(f"Failed to auto-close alert: {str(e)}") from e


async def evaluate_all_pending_alerts(
    db: AsyncIOMotorDatabase,
) -> Dict[str, int]:
    """
    Evaluate all pending alerts for auto-closure conditions.

    Queries all alerts with status OPEN or ESCALATED, checks auto-close
    conditions, and applies auto-close if needed.

    Args:
        db: MongoDB database instance

    Returns:
        Dict[str, int]: Statistics with total_checked and auto_closed counts
    """
    try:
        alerts_collection = db["alerts"]

        # Query all pending alerts
        query = {
            "status": {"$in": [AlertStatus.OPEN.value, AlertStatus.ESCALATED.value]}
        }

        cursor = alerts_collection.find(query)
        alert_docs = await cursor.to_list(length=None)

        total_checked = len(alert_docs)
        auto_closed = 0

        logger.info(f"Evaluating {total_checked} pending alerts for auto-close conditions")

        # Process each alert
        for alert_doc in alert_docs:
            try:
                alert = AlertModel(**alert_doc)

                # Check auto-close conditions
                should_close, reason = await check_auto_close_conditions(alert, db)

                if should_close and reason:
                    # Apply auto-close
                    await apply_auto_close(alert.alert_id, reason, db)
                    auto_closed += 1
                    logger.info(
                        f"Auto-closed alert {alert.alert_id}: {reason}"
                    )

            except Exception as e:
                # Log error but continue with other alerts
                logger.error(
                    f"Error processing alert {alert_doc.get('alert_id', 'unknown')}: {str(e)}"
                )
                continue

        stats = {
            "total_checked": total_checked,
            "auto_closed": auto_closed,
        }

        logger.info(
            f"Evaluation complete: {total_checked} checked, {auto_closed} auto-closed"
        )

        return stats

    except PyMongoError as e:
        logger.error(f"Database error evaluating pending alerts: {str(e)}")
        raise RuntimeError(f"Failed to evaluate pending alerts: {str(e)}") from e
    except Exception as e:
        logger.error(f"Unexpected error evaluating pending alerts: {str(e)}")
        raise RuntimeError(f"Failed to evaluate pending alerts: {str(e)}") from e

