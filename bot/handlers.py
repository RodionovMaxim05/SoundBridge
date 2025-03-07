import logging

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from bot.utils import database, format_groups_with_users
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
        [InlineKeyboardButton("👨‍👩‍👦‍👦 Управление группами", callback_data=str(CallbackData.MANAGE_GROUPS.value))],
        [InlineKeyboardButton("⚙️ Обновить Токен", callback_data=str(CallbackData.UPDATE_TOKEN.value))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Пожалуйста, выберите действие:", reply_markup=reply_markup)
    else:
        await update.callback_query.edit_message_text("Пожалуйста, выберите действие:", reply_markup=reply_markup)

    return State.START.value


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
        [InlineKeyboardButton("➕ Добавить пользователя в группу", callback_data=str(CallbackData.ADD_USER.value))],
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


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the username input step. Prompts the user to enter a username (with @) to add to a group.
    """

    logger.info(f"User {update.effective_user.id} in \"name_handler\"")
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Введите Username пользователя (вместе с @)\n\nИли напишить /start для отмены")
    return State.TAKE_USERNAME.value


async def check_name_and_choose_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Validates the entered username and displays a list of groups to which the user can be added.
    If the username is invalid, notifies the user and provides an option to go back.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"check_name_and_choose_group\"")

    user_message = update.message.text
    if database.check_username(user_message):
        groups = database.get_user_groups(user.id)

        keyboard = []
        for group in groups:
            keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"addUser*{user_message}*{group.id}")])

        keyboard.append([InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value))])
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text("Выберите группу, в которую хотите добавить пользователя",
                                        reply_markup=reply_markup)
        return State.USER_TO_GROUP.value
    else:
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await update.message.reply_text(
            f"❌ Пользователя {user_message} нет в базе данных бота.\n\nЕсли username правильный, попросите пользователя запустить бота.",
            reply_markup=reply_markup)

        return State.START.value


async def add_user_to_the_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Adds the selected user to the chosen group. Notifies the user of success or failure.
    """

    logger.info(f"User {update.effective_user.id} in \"add_user_to_the_group\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    username = str(callback_data.split("*")[1])
    group_id = int(callback_data.split("*")[2])

    if database.add_user_to_group(group_id, username):
        keyboard = [
            [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
        ]

        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text(f"✅ Пользователь {username} успешно добавлен в группу {group_id}",
                                      reply_markup=reply_markup)

        return State.START.value

    await update.message.reply_text("Что-то пошло не так :(")
    return ConversationHandler.END
