import logging
import os
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from llm import OpenRouterClient
from bot.config import BotConfig
from bot.feedback import save_feedback, get_all_feedback, format_feedback_list

logger = logging.getLogger(__name__)

# Create router
router = Router()

# Global variables (will be set in main.py)
llm_client: OpenRouterClient = None
bot_config: BotConfig = None


# FSM States for feedback
class FeedbackStates(StatesGroup):
    waiting_for_comment = State()


def set_dependencies(client: OpenRouterClient, config: BotConfig):
    """Set LLM client and config"""
    global llm_client, bot_config
    llm_client = client
    bot_config = config


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


@router.message(Command("myid"))
async def cmd_myid(message: Message):
    """Show user's Telegram ID"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested their ID")
    await message.answer(f"Твой Telegram ID: {user_id}")


def is_admin(user_id: int) -> bool:
    """Check if user is admin"""
    return user_id in bot_config.admin.user_ids


@router.message(Command("config"))
async def cmd_config(message: Message):
    """Show current configuration (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return

    logger.info(f"Admin {user_id} requested config")

    admins = ", ".join(str(uid) for uid in bot_config.admin.user_ids) or "не заданы"
    model = getattr(llm_client, "model", "не задана")

    config_text = f"""⚙️ Текущие настройки:

• Файл базы знаний: {bot_config.data_file}
• Модель OpenRouter: {model}
• Администраторы: {admins}

Бот использует весь файл data.txt как контекст в системном промпте.
Чтобы обновить знания, загрузите новый файл и перезапустите бота."""

    await message.answer(config_text)


@router.message(Command("add_admin"))
async def cmd_add_admin(message: Message):
    """Add admin user (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return

    try:
        parts = message.text.split()
        if len(parts) != 2:
            await message.answer("Использование: /add_admin <user_id>\nПример: /add_admin 123456789")
            return

        new_admin_id = int(parts[1])

        if new_admin_id in bot_config.admin.user_ids:
            await message.answer(f"Пользователь {new_admin_id} уже является администратором")
            return

        bot_config.admin.user_ids.append(new_admin_id)
        bot_config.save_json_config()

        logger.info(f"Admin {user_id} added new admin {new_admin_id}")
        await message.answer(f"✅ Пользователь {new_admin_id} добавлен в администраторы")

    except ValueError:
        await message.answer("Ошибка: введи корректный user_id")
    except Exception as e:
        logger.error(f"Error adding admin: {e}")
        await message.answer("Произошла ошибка при добавлении администратора")


@router.message(Command("get_data"))
async def cmd_get_data(message: Message):
    """Send data.txt file (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return

    try:
        data_file_path = bot_config.data_file
        if not os.path.exists(data_file_path):
            await message.answer("❌ Файл data.txt не найден")
            return

        logger.info(f"Admin {user_id} requested data.txt")

        file = FSInputFile(data_file_path)
        await message.answer_document(
            document=file,
            caption="📄 Текущий файл базы знаний\n\nДля обновления: отправь отредактированный файл и используй /reload_data"
        )

    except Exception as e:
        logger.error(f"Error sending data file: {e}")
        await message.answer("Произошла ошибка при отправке файла")


@router.message(Command("reload_data"))
async def cmd_reload_data(message: Message):
    """Reload knowledge base with new data (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return

    try:
        logger.info(f"Admin {user_id} requested data reload")
        await message.answer(
            "⚠️ Для обновления базы знаний нужно перезапустить бота.\n\n"
            "Отправь отредактированный data.txt, я его сохраню, а затем перезапусти бота командой в консоли."
        )

    except Exception as e:
        logger.error(f"Error in reload_data: {e}")
        await message.answer("Произошла ошибка")


@router.message(F.document)
async def handle_document(message: Message):
    """Handle uploaded documents (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        return

    try:
        document = message.document

        # Check file extension
        if not document.file_name.endswith('.txt'):
            await message.answer("❌ Поддерживаются только .txt файлы")
            return

        logger.info(f"Admin {user_id} uploaded file: {document.file_name}")

        # Download file
        file = await message.bot.get_file(document.file_id)
        file_path = file.file_path

        # Download to temporary location
        temp_file = f"temp_{document.file_name}"
        await message.bot.download_file(file_path, temp_file)

        # Save as data.txt
        target_path = bot_config.data_file

        # Backup old file
        if os.path.exists(target_path):
            backup_path = f"{target_path}.backup"
            os.replace(target_path, backup_path)
            logger.info(f"Created backup: {backup_path}")

        # Move new file
        os.replace(temp_file, target_path)

        logger.info(f"Admin {user_id} updated data.txt")
        await message.answer(
            "✅ Файл data.txt обновлен!\n\n"
            "⚠️ Чтобы изменения вступили в силу, перезапусти бота:\n"
            "1. Останови бота (Ctrl+C)\n"
            "2. Запусти снова: python main.py"
        )

    except Exception as e:
        logger.error(f"Error handling document: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при обработке файла")


@router.message(Command("feedback"))
async def cmd_feedback(message: Message):
    """Request user feedback"""
    user_id = message.from_user.id
    logger.info(f"User {user_id} requested feedback")

    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="👍 Полезно", callback_data="feedback_positive"),
            InlineKeyboardButton(text="👎 Не помогло", callback_data="feedback_negative")
        ]
    ])

    await message.answer(
        "Как тебе работа бота?\nВыбери оценку:",
        reply_markup=keyboard
    )


@router.callback_query(F.data.in_(["feedback_positive", "feedback_negative"]))
async def handle_feedback_rating(callback: CallbackQuery, state: FSMContext):
    """Handle feedback rating button"""
    user_id = callback.from_user.id
    rating = "positive" if callback.data == "feedback_positive" else "negative"

    # Save rating to state
    await state.update_data(rating=rating)
    await state.set_state(FeedbackStates.waiting_for_comment)

    rating_emoji = "👍" if rating == "positive" else "👎"

    await callback.message.edit_text(
        f"{rating_emoji} Спасибо за оценку!\n\n"
        "Хочешь добавить комментарий? Напиши его следующим сообщением.\n"
        "Или отправь /skip чтобы пропустить."
    )
    await callback.answer()

    logger.info(f"User {user_id} gave {rating} feedback, waiting for comment")


@router.message(FeedbackStates.waiting_for_comment, Command("skip"))
async def skip_feedback_comment(message: Message, state: FSMContext):
    """Skip feedback comment"""
    user_id = message.from_user.id
    data = await state.get_data()
    rating = data.get('rating')

    # Save feedback without comment
    save_feedback(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        rating=rating,
        comment=None
    )

    await state.clear()
    await message.answer("✅ Спасибо за отзыв!")
    logger.info(f"User {user_id} skipped feedback comment")


@router.message(FeedbackStates.waiting_for_comment)
async def receive_feedback_comment(message: Message, state: FSMContext):
    """Receive feedback comment"""
    user_id = message.from_user.id
    comment = message.text
    data = await state.get_data()
    rating = data.get('rating')

    # Save feedback with comment
    save_feedback(
        user_id=user_id,
        username=message.from_user.username,
        first_name=message.from_user.first_name,
        last_name=message.from_user.last_name,
        rating=rating,
        comment=comment
    )

    await state.clear()
    await message.answer("✅ Спасибо за подробный отзыв! Это поможет улучшить бота.")
    logger.info(f"User {user_id} submitted feedback with comment")


@router.message(Command("feedback_list"))
async def cmd_feedback_list(message: Message):
    """Show all feedback (admin only)"""
    user_id = message.from_user.id

    if not is_admin(user_id):
        await message.answer("Эта команда доступна только администраторам.")
        return

    logger.info(f"Admin {user_id} requested feedback list")

    try:
        feedback_list = get_all_feedback()
        formatted = format_feedback_list(feedback_list)

        # Split long messages
        if len(formatted) > 4000:
            # Send in chunks
            chunks = [formatted[i:i+4000] for i in range(0, len(formatted), 4000)]
            for chunk in chunks:
                await message.answer(chunk)
        else:
            await message.answer(formatted)

    except Exception as e:
        logger.error(f"Error getting feedback list: {e}", exc_info=True)
        await message.answer("❌ Произошла ошибка при получении отзывов")


@router.message(F.text)
async def handle_question(message: Message):
    """Handle user questions"""
    user_id = message.from_user.id
    query = message.text

    logger.info(f"User {user_id} asked: {query}")

    try:
        answer = llm_client.generate_answer(query)
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
