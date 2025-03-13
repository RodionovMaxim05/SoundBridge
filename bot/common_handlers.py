import logging

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, User
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils import database, send_or_edit_message
from constants import State, CallbackData

logger = logging.getLogger(__name__)


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the /start command. Initializes the bot, creates database tables,
    and inserts the user into the database. Displays a menu with options.
    """

    user = update.effective_user
    logger.info(f"User {user.id} - {user.name} started the bot.")
    database.create_tables()
    database.insert_user(user.id, user.name)

    keyboard = [
        [InlineKeyboardButton("📊 Мой аккаунт", callback_data=str(CallbackData.ACCOUNT.value))],
        [InlineKeyboardButton("👨‍👩‍👦‍👦 Управление группами", callback_data=str(CallbackData.MANAGE_GROUPS.value))],
        [InlineKeyboardButton("🔉 Поделиться музыкой", callback_data=str(CallbackData.SEND_MESSAGE.value))],
        [InlineKeyboardButton("🗃 История", callback_data=str(CallbackData.HISTORY.value))],
        [InlineKeyboardButton("⚙️ Обновить Токен", callback_data=str(CallbackData.UPDATE_TOKEN.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(update, text="Пожалуйста, выберите действие", reply_markup=reply_markup)

    return State.START.value


async def token_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the "Update Token" callback. Prompts the user to enter a new token.
    """

    logger.info(f"User {update.effective_user.id} in \"token_handler\"")
    await send_or_edit_message(update, text="Введите ваш токен\n\nИли напишить /start для отмены")

    return State.ENTER_TOKEN.value


async def receive_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the token from the user and updates it in the database.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"token_handler\"")

    user_message = update.message.text

    if database.update_user_token(user.id, user_message):
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text("✅ Токен успешно обновлен", reply_markup=reply_markup)

        return State.START.value

    await update.message.reply_text("Что-то пошло не так :(")
    return ConversationHandler.END


async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /account command. Displays the user's account information,
    including token status and sharing statistics.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"token_handler\"")

    result = database.get_user_statistic(user.id)

    token = '✔️' if result.get('token') else '❌'

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(
        update,
        text=f"<b>Ваш аккаунт\n\nТокен:</b> {token}\n\n📊 <b>Статистика\n\nКоличество композиций, которыми вы поделились:</b> {result.get('count_of_sharing')}\n",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML
    )

    return State.START.value


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /help command. Provides a simple response indicating no help is available.
    """

    logger.info(f"User {update.effective_user.id} in \"token_handler\"")
    await update.message.reply_text("Помощи нет.")


def group_selection(user: User, cl_data: str) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard markup for selecting a group.
    """

    groups = database.get_user_groups(user.id)

    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"{cl_data}_{group.id}")])

    keyboard.append([InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup
