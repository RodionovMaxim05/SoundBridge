import logging

import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.error import TelegramError
from telegram.ext import ContextTypes, ConversationHandler

from bot.music import get_last_five_liked_track, get_track_info
from bot.utils import database, format_groups_with_users, send_or_edit_message, format_users_of_group, \
    fix_yandex_image_url, format_message
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
        [InlineKeyboardButton("🔉 Поделиться треком", callback_data=str(CallbackData.SEND_MESSAGE.value))],
        [InlineKeyboardButton("⚙️ Обновить Токен", callback_data=str(CallbackData.UPDATE_TOKEN.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(update, text="Пожалуйста, выберите действие", reply_markup=reply_markup)

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

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(
        update,
        text=f"<b>Ваш аккаунт\n\nТокен:</b> {token}\n\n📊 <b>Statistics\n\nКоличество треков, которыми поделился:</b> {result.get('count_of_sharing')}\n",
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
        context.user_data["add_user"] = user_message

        keyboard = []
        for group in groups:
            keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"addUser_{group.id}")])

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
    group_id = int(callback_data.split("_")[1])
    username = context.user_data["add_user"]

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


async def share_track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the initial step of sharing a track. Displays a list of user's groups to choose from.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"share_track_handler\"")
    query = update.callback_query
    await query.answer()

    groups = database.get_user_groups(user.id)

    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"share_{group.id}")])
    keyboard.append([InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MENU.value))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите группу, с которой хотите поделиться", reply_markup=reply_markup)
    return State.SHARE_TRACK.value


async def choose_track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the selection of a group and prompts the user to choose a track to share.
    """

    logger.info(f"User {update.effective_user.id} in \"choose_track_handler\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])
    context.user_data["share_group_id"] = group_id

    keyboard = [
        [InlineKeyboardButton("❤️ Выбрать из 5 последних понравившихся треков",
                              callback_data=str(CallbackData.CHOOSE_LIKED_TRACK.value))],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"{format_users_of_group(group_id)}Выберите, чем хотите поделиться",
                                  reply_markup=reply_markup)
    return State.SHARE_TRACK.value


async def show_liked_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the last five liked tracks for the user to choose from.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"choose_track_handler\"")
    query = update.callback_query
    await query.answer()

    liked_tracks = await get_last_five_liked_track(user.id)

    keyboard = [
        [InlineKeyboardButton(f"{track.artists[0].name} - {track.title}", callback_data=f"chosen_{track.id}")]
        for track in liked_tracks
    ]
    keyboard.append([InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{format_users_of_group(context.user_data["share_group_id"])}Выберите, чем хотите поделиться",
        reply_markup=reply_markup)
    return State.SHARE_TRACK.value


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the selection of a track and prompts the user to share their emotions about it.
    """

    logger.info(f"User {update.effective_user.id} in \"message_handler\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    track_id = int(callback_data.split("_")[1])
    context.user_data["share_track_id"] = track_id

    await query.edit_message_text("Поделитесь эмоциями об этом треке\n\nИли напишить /start для отмены")
    return State.TAKE_MESSAGE.value


async def send_message_to_users(update: Update, bot: Bot, users: any, message_text: str, photo: str,
                                parse_mode: str = None) -> None:
    """
    Sends a message to a list of users by their user IDs.
    """

    for user in users:
        if user.id != update.effective_user.id:  # Avoid sending the message to the sender
            try:
                await bot.send_photo(chat_id=user.id, photo=photo,
                                     caption=message_text,
                                     parse_mode=parse_mode)
                logger.info(f"Message sent to user {user.id}.")
            except TelegramError as e:
                logger.error(f"Failed to send message to user {user.id}: {e}")


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the user's message and sends it to the selected group.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"receive_message\"")

    group_id = context.user_data.get("share_group_id")
    track_id = context.user_data["share_track_id"]

    database.incr_count_of_sharing(user.id)

    user_message = update.message.text
    track_info = await get_track_info(user.id, track_id)

    await  send_message_to_users(update, context.bot, users=database.get_group_users(group_id),
                                 message_text=format_message(user.name, user_message, track_info),
                                 photo=fix_yandex_image_url(track_info.cover_uri),
                                 parse_mode=telegram.constants.ParseMode.HTML)

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Сообщение успешно обновлен", reply_markup=reply_markup)

    return State.START.value
