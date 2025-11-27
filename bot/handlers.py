import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from rag import RAGRetriever
from llm import OpenRouterClient

logger = logging.getLogger(__name__)

# Create router
router = Router()

# Global variables (will be set in main.py)
rag_retriever: RAGRetriever = None
llm_client: OpenRouterClient = None


def set_dependencies(retriever: RAGRetriever, client: OpenRouterClient):
    """Set RAG retriever and LLM client"""
    global rag_retriever, llm_client
    rag_retriever = retriever
    llm_client = client


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    logger.info(f"User {message.from_user.id} started the bot")
    await message.answer("Привет! Я помощник для поступающих в ШАД. Задай мне вопрос!")


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Handle /help command"""
    logger.info(f"User {message.from_user.id} requested help")
    await message.answer("Просто напиши мне свой вопрос о поступлении в ШАД.")


@router.message(F.text)
async def handle_question(message: Message):
    """Handle user questions"""
    user_id = message.from_user.id
    query = message.text

    logger.info(f"User {user_id} asked: {query}")

    try:
        # Retrieve relevant context
        context = rag_retriever.get_context(query, top_k=3)
        logger.debug(f"Retrieved context for user {user_id}")

        # Generate answer
        answer = llm_client.generate_answer(query, context)
        logger.info(f"Generated answer for user {user_id}")

        # Send answer
        await message.answer(answer)

    except Exception as e:
        logger.error(f"Error handling question from user {user_id}: {e}", exc_info=True)
        await message.answer("Извините, произошла ошибка. Попробуйте позже.")


def register_handlers(dp):
    """Register all handlers"""
    dp.include_router(router)
    logger.info("Handlers registered")
