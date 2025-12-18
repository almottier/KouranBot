"""Main entry point for KouranBot."""

import asyncio
import logging
import sys

from aiohttp import web
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

from bot.config import TELEGRAM_BOT_TOKEN, POLLING_INTERVAL
from bot.database import init_database, init_localities_from_json
from bot.handlers import (
    start_command, help_command, subscribe_command,
    mysubscriptions_command, unsubscribe_command, language_command,
    button_callback, handle_text_message
)
from bot.monitor import run_monitor_check

# Configure logging
logging.basicConfig(
    format="[%(asctime)s] [%(levelname)s] [%(name)s] - %(message)s",
    level=logging.INFO,
    stream=sys.stdout
)

logger = logging.getLogger(__name__)


async def health_check(request):
    """Health check endpoint for Coolify."""
    return web.json_response({"status": "healthy", "service": "KouranBot"})


async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle errors in the bot."""
    logger.error(f"Update {update} caused error {context.error}", exc_info=context.error)


async def post_init(application: Application):
    """Run initialization tasks after bot starts."""
    logger.info("Initializing KouranBot...")

    # Create database tables if they don't exist
    try:
        init_database()
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise

    # Initialize districts and localities from JSON
    try:
        init_localities_from_json()
    except Exception as e:
        logger.error(f"Failed to initialize localities: {e}")
        raise

    logger.info("KouranBot initialization complete")


async def monitor_job(context: ContextTypes.DEFAULT_TYPE):
    """Scheduled job to check for outages."""
    try:
        await run_monitor_check(context.bot)
    except Exception as e:
        logger.error(f"Error in monitor job: {e}", exc_info=True)


async def start_health_server():
    """Start HTTP health check server."""
    app = web.Application()
    app.router.add_get("/health", health_check)
    app.router.add_get("/", health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 8080)
    await site.start()
    logger.info("Health check server started on port 8080")


def main():
    """Start the bot."""
    logger.info("Starting KouranBot...")

    # Create application
    application = (
        Application.builder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Register command handlers
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("subscribe", subscribe_command))
    application.add_handler(CommandHandler("mysubscriptions", mysubscriptions_command))
    application.add_handler(CommandHandler("unsubscribe", unsubscribe_command))
    application.add_handler(CommandHandler("language", language_command))

    # Register callback query handler
    application.add_handler(CallbackQueryHandler(button_callback))

    # Register text message handler (for non-command messages)
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text_message))

    # Register error handler
    application.add_error_handler(error_handler)

    # Set up scheduler for monitoring
    scheduler = AsyncIOScheduler()

    # Run monitor check every POLLING_INTERVAL minutes
    scheduler.add_job(
        monitor_job,
        "interval",
        minutes=POLLING_INTERVAL,
        args=[application],
        id="outage_monitor",
        replace_existing=True
    )

    # Run initial check after 30 seconds
    scheduler.add_job(
        monitor_job,
        "date",
        run_date=None,
        args=[application],
        id="initial_check"
    )

    scheduler.start()
    logger.info(f"Scheduler started - checking for outages every {POLLING_INTERVAL} minutes")

    # Start health check server
    loop = asyncio.get_event_loop()
    loop.create_task(start_health_server())

    # Start the bot
    logger.info("Bot is running. Press Ctrl+C to stop.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)
