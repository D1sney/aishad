import asyncio
import logging
from aiogram import Bot, Dispatcher
from aiogram.client.bot import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import BotConfig
from bot.logger_config import setup_logging
from bot.handlers import register_handlers, set_dependencies
from bot.feedback import init_db
from llm import OpenRouterClient

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot"""
    # Setup logging
    setup_logging(level=logging.INFO)
    logger.info("Starting ШАД Admission Bot")

    # Initialize feedback database
    init_db()
    logger.info("Feedback database initialized")

    # Load configuration
    config = BotConfig.from_env()
    config.validate()
    logger.info("Configuration loaded and validated")

    # Initialize LLM client
    logger.info("Initializing OpenRouter client...")
    llm_client = OpenRouterClient(
        api_key=config.openrouter_api_key,
        data_file=config.data_file
    )

    # Set dependencies for handlers
    set_dependencies(llm_client, config)

    # Initialize bot and dispatcher with FSM storage
    bot = Bot(
        token=config.telegram_token,
        default=DefaultBotProperties(parse_mode="Markdown")
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    # Register handlers
    register_handlers(dp)

    logger.info("Bot is starting...")
    try:
        await dp.start_polling(bot)
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
