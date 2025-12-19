"""Power outage monitoring and notification system."""

import asyncio
import logging
from datetime import datetime
from typing import List, Dict, Any
from zoneinfo import ZoneInfo

import httpx
from telegram import Bot
from telegram.error import TelegramError

from bot.config import JSON_URL
from bot.database import (
    get_db, Outage, NotificationSent, get_users_with_language_for_locality
)
from bot.translations import get_text

logger = logging.getLogger(__name__)


class OutageMonitor:
    """Monitor power outages and send notifications."""

    def __init__(self, bot: Bot):
        self.bot = bot

    async def check_for_outages(self):
        """Poll JSON endpoint and process new outages."""
        logger.info("Checking for new power outages...")

        try:
            outages_data = await self._fetch_outages()
            if not outages_data:
                logger.warning("No data received from JSON endpoint")
                return

            new_outages = self._process_outages(outages_data)
            logger.info(f"Found {len(new_outages)} new outages")

            if new_outages:
                await self._send_notifications(new_outages)

        except Exception as e:
            logger.error(f"Error checking for outages: {e}", exc_info=True)

    async def _fetch_outages(self) -> Dict[str, List[Dict[str, Any]]]:
        """Fetch outages from JSON endpoint."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(JSON_URL)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            logger.error(f"HTTP error fetching outages: {e}")
            return {}
        except Exception as e:
            logger.error(f"Error fetching outages: {e}")
            return {}

    def _process_outages(self, data: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Process outages data and return list of new outage IDs."""
        new_outage_ids = []
        db = get_db()

        try:
            # Process both 'today' and 'future' outages
            all_outages = data.get("today", []) + data.get("future", [])

            for outage_data in all_outages:
                outage_id = outage_data.get("id")
                if not outage_id:
                    logger.warning(f"Outage missing ID: {outage_data}")
                    continue

                # Check if outage already exists
                existing = db.query(Outage).filter(Outage.id == outage_id).first()

                if not existing:
                    # New outage - create it
                    try:
                        outage = Outage(
                            id=outage_id,
                            locality=outage_data.get("locality", ""),
                            district=outage_data.get("district", ""),
                            streets=outage_data.get("streets", ""),
                            date_description=outage_data.get("date", ""),
                            from_time=datetime.fromisoformat(
                                outage_data["from"].replace("Z", "+00:00")
                            ),
                            to_time=datetime.fromisoformat(
                                outage_data["to"].replace("Z", "+00:00")
                            )
                        )
                        db.add(outage)
                        db.commit()
                        new_outage_ids.append(outage_id)
                        logger.info(f"New outage detected: {outage_id} in {outage.locality}")

                    except Exception as e:
                        logger.error(f"Error creating outage {outage_id}: {e}")
                        db.rollback()
                        continue

                else:
                    # Update last_checked timestamp
                    existing.last_checked = datetime.utcnow()
                    db.commit()

        except Exception as e:
            logger.error(f"Error processing outages: {e}")
            db.rollback()
        finally:
            db.close()

        return new_outage_ids

    async def _send_notifications(self, outage_ids: List[str]):
        """Send notifications for new outages."""
        db = get_db()

        try:
            for outage_id in outage_ids:
                # Query the outage
                outage = db.query(Outage).filter(Outage.id == outage_id).first()
                if not outage:
                    continue

                # Find all users subscribed to this locality (with their language preferences)
                users_with_lang = get_users_with_language_for_locality(db, outage.locality)

                logger.info(
                    f"Sending notifications for {outage.locality} to {len(users_with_lang)} users"
                )

                # Send notification to each user
                for user_id, user_lang in users_with_lang:
                    # Check if notification already sent
                    already_sent = db.query(NotificationSent).filter(
                        NotificationSent.user_id == user_id,
                        NotificationSent.outage_id == outage.id
                    ).first()

                    if already_sent:
                        continue

                    # Send notification
                    success = await self._send_notification_to_user(user_id, outage, user_lang)

                    if success:
                        # Record notification as sent
                        notification = NotificationSent(
                            user_id=user_id,
                            outage_id=outage.id
                        )
                        db.add(notification)
                        db.commit()

                    # Small delay to respect rate limits
                    await asyncio.sleep(0.05)  # 20 messages per second

        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            db.rollback()
        finally:
            db.close()

    async def _send_notification_to_user(self, user_id: int, outage: Outage, lang: str) -> bool:
        """Send notification about an outage to a specific user."""
        try:
            message = self._format_outage_message(outage, lang)
            await self.bot.send_message(chat_id=user_id, text=message)
            logger.info(f"Sent notification to user {user_id} for outage {outage.id}")
            return True

        except TelegramError as e:
            logger.error(f"Telegram error sending to user {user_id}: {e}")

            # If user blocked the bot, mark them as inactive
            if "blocked" in str(e).lower() or "deactivated" in str(e).lower():
                db = get_db()
                try:
                    from bot.database import User
                    user = db.query(User).filter(User.telegram_id == user_id).first()
                    if user:
                        user.is_active = False
                        db.commit()
                        logger.info(f"Marked user {user_id} as inactive")
                finally:
                    db.close()

            return False

        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}")
            return False

    def _format_outage_message(self, outage: Outage, lang: str) -> str:
        """Format outage information as a message."""
        # Convert UTC times to Mauritius timezone (UTC+4)
        mauritius_tz = ZoneInfo("Indian/Mauritius")
        from_time_local = outage.from_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(mauritius_tz)
        to_time_local = outage.to_time.replace(tzinfo=ZoneInfo("UTC")).astimezone(mauritius_tz)

        # Format times in Mauritius timezone
        from_time_str = from_time_local.strftime("%H:%M")
        to_time_str = to_time_local.strftime("%H:%M")
        date_str = from_time_local.strftime("%d %B %Y")

        district_display = outage.district.replace("_", " ").title()

        if outage.streets:
            return get_text(
                lang, "outage_alert",
                locality=outage.locality,
                district=district_display,
                date=date_str,
                from_time=from_time_str,
                to_time=to_time_str,
                streets=outage.streets
            )
        else:
            return get_text(
                lang, "outage_alert_no_streets",
                locality=outage.locality,
                district=district_display,
                date=date_str,
                from_time=from_time_str,
                to_time=to_time_str
            )


async def run_monitor_check(bot: Bot):
    """Run a single monitoring check - to be called by scheduler."""
    monitor = OutageMonitor(bot)
    await monitor.check_for_outages()
