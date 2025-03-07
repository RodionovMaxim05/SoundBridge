import logging
from enum import auto, Enum

import telegram
from decouple import config
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CommandHandler, CallbackQueryHandler, ConversationHandler, Application, MessageHandler, filters
from telegram.ext import ContextTypes

from database import Database

database = Database()


class State(Enum):
    """States"""
    START = auto()
    ENTER_TOKEN = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()


class CallbackData(Enum):
    """Callback data"""
    MENU = auto()
    MANAGE_GROUPS = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    UPDATE_TOKEN = auto()


logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
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
        [InlineKeyboardButton("👨‍👩‍👦‍👦 Управление группами", callback_data=str(CallbackData.MANAGE_GROUPS.value))],
        [InlineKeyboardButton("⚙️ Обновить Токен", callback_data=str(CallbackData.UPDATE_TOKEN.value))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Пожалуйста, выберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Пожалуйста, выберите действие:", reply_markup=reply_markup)

    return State.START.value


def format_groups_with_users(user_id: int) -> str:
    """
    Formats the list of groups and their members for a given user into a readable string.
    """

    user_groups = database.get_user_groups(user_id)
    return "\n\n".join(
        f"Группа: {group.name}\nУчастники: {', '.join(user.name for user in database.get_group_users(group.id))}"
        for group in user_groups
    )


async def manage_groups(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the "Manage Groups" callback. Displays the user's groups and provides options to create or delete groups.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"manage_groups\"")
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🛠 Создать группу", callback_data=str(CallbackData.CREATE_GROUP.value))],
        [InlineKeyboardButton("🗑 Удалить группу", callback_data=str(CallbackData.DELETE_GROUP.value))],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"Ваши группы:\n{format_groups_with_users(user.id)}",
        reply_markup=reply_markup)
    return State.START.value


async def create_group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the "Create Group" callback. Checks if the user has reached the group limit
    and prompts the user to enter a group name.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"create_group_handler\"")
    query = update.callback_query
    await query.answer()

    if len(database.get_user_groups(user.id)) >= 5:
        keyboard = [
            [InlineKeyboardButton("🗑 Удалить группу", callback_data=str(CallbackData.DELETE_GROUP.value))],
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text("❗️ Достигнут лимит количества групп, больше групп создавать нельзя",
                                      reply_markup=reply_markup)
        return State.START.value

    await query.edit_message_text("Введите название группы\n\nИли напишить /start для отмены")
    return State.CREATE_GROUP.value


async def receive_name_of_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the group name from the user and creates the group in the database.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"receive_name_of_group\"")
    user_message = update.message.text

    if database.create_group(user_message, user.id):
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(f"✅ Группа \"{user_message}\" успешно создана", reply_markup=reply_markup)

        return State.START.value

    await update.message.reply_text("Что-то пошло не так :(")
    return ConversationHandler.END


async def delete_group_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the "Delete Group" callback. Displays a list of the user's groups for deletion.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"delete_group_handler\"")
    query = update.callback_query
    await query.answer()

    groups = database.get_user_groups(user.id)

    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"delete_{group.id}")])

    keyboard.append([InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите группы, которую хотите удалить", reply_markup=reply_markup)
    return State.DELETE_GROUP.value


async def confirm_group_deletion(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
     Confirms the deletion of a group. Displays a confirmation message with options to proceed or cancel.
    """

    logger.info(f"User {update.effective_user.id} in \"confirm_group_deletion\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("🗑 Удалить группу", callback_data=f"exactly_{group_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"❓ Вы действительно хотите удалить группу {database.get_group_name(group_id)}?",
                                  reply_markup=reply_markup)
    return State.DELETE_GROUP.value


async def delete_group_callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the actual deletion of a group from the database.
    """

    logger.info(f"User {update.effective_user.id} in \"delete_group_callback_handler\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    if database.delete_group(group_id):
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("✅ Группа успешно удалена", reply_markup=reply_markup)

        return State.START.value

    await update.message.reply_text("Что-то пошло не так :(")
    return ConversationHandler.END


async def token_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the "Update Token" callback. Prompts the user to enter a new token.
    """

    logger.info(f"User {update.effective_user.id} in \"token_handler\"")
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Введите ваш токен\n\nИли напишить /start для отмены")
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
    await update.message.reply_text(
        text=f"<b>Ваш аккаунт\n\nТокен:</b> {token}\n\n📊 <b>Statistics\n\nКоличество:</b> {result.get('count_of_sharing')}\n",
        parse_mode=telegram.constants.ParseMode.HTML)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the /help command. Provides a simple response indicating no help is available.
    """

    logger.info(f"User {update.effective_user.id} in \"token_handler\"")
    await update.message.reply_text("Помощи нет.")


main_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_handler),
        CommandHandler("token", token_handler)
    ],
    states={
        State.START.value: [
            CallbackQueryHandler(manage_groups, pattern="^" + str(CallbackData.MANAGE_GROUPS.value) + "$"),
            CallbackQueryHandler(create_group_handler, pattern="^" + str(CallbackData.CREATE_GROUP.value) + "$"),
            CallbackQueryHandler(delete_group_handler, pattern="^" + str(CallbackData.DELETE_GROUP.value) + "$"),
            CallbackQueryHandler(token_handler, pattern="^" + str(CallbackData.UPDATE_TOKEN.value) + "$"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.CREATE_GROUP.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name_of_group)],
        State.DELETE_GROUP.value: [
            CallbackQueryHandler(confirm_group_deletion, pattern="^delete_"),
            CallbackQueryHandler(delete_group_callback_handler, pattern="^exactly_"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.ENTER_TOKEN.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
    },
    fallbacks=[CommandHandler("start", start_handler)],
)


def register_handlers(application):
    """
    Registers all command and conversation handlers with the bot application.
    """

    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('account', account_handler))
    application.add_handler(main_conversation)


def main() -> None:
    """
    Initializes the bot, sets up the application, and starts polling for updates.
    """
    
    application = Application.builder().token(config('TOKEN')).build()
    register_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
