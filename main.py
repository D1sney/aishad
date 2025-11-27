import asyncio
import logging
from aiogram import Bot, Dispatcher

from bot.config import BotConfig
from bot.logger_config import setup_logging
from bot.handlers import register_handlers, set_dependencies
from rag import RAGRetriever
from llm import OpenRouterClient

logger = logging.getLogger(__name__)


async def main():
    """Main function to run the bot"""
    # Setup logging
    setup_logging(level=logging.INFO)
    logger.info("Starting ШАД Admission Bot")

    # Load configuration
    config = BotConfig.from_env()
    config.validate()
    logger.info("Configuration loaded and validated")

    # Initialize RAG retriever
    logger.info("Initializing RAG retriever...")
    rag_retriever = RAGRetriever(data_file=config.data_file)

    # Initialize LLM client
    logger.info("Initializing OpenRouter client...")
    llm_client = OpenRouterClient(api_key=config.openrouter_api_key)

    # Set dependencies for handlers
    set_dependencies(rag_retriever, llm_client)

    # Initialize bot and dispatcher
    bot = Bot(token=config.telegram_token)
    dp = Dispatcher()

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
