import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.common_handlers import logger
from bot.music import get_last_five_liked_track, get_track_info
from bot.utils import database, format_users_of_group, \
    fix_yandex_image_url, format_message
from constants import State, CallbackData


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
