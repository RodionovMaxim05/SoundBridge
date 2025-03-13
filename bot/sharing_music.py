import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, Bot
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.common_handlers import logger
from bot.music import get_last_five_liked_track, get_track_info, search_request, get_album_info
from bot.utils import database, format_users_of_group, \
    fix_yandex_image_url, format_message
from constants import State, CallbackData


async def share_music_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the initial step of sharing a music. Displays a list of user's groups to choose from.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"share_music_handler\"")
    query = update.callback_query
    await query.answer()

    groups = database.get_user_groups(user.id)

    keyboard = []
    for group in groups:
        keyboard.append([InlineKeyboardButton(f"{group.name}", callback_data=f"share_{group.id}")])
    keyboard.append([InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MENU.value))])
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите группу, с которой хотите поделиться", reply_markup=reply_markup)
    return State.SHARE_MUSIC.value


async def choose_music_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the selection of a group and prompts the user to choose a music to share.
    """

    logger.info(f"User {update.effective_user.id} in \"choose_music_handler\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])
    context.user_data["share_group_id"] = group_id

    keyboard = [
        [InlineKeyboardButton("❤️ Выбрать из 5 последних понравившихся треков",
                              callback_data=str(CallbackData.CHOOSE_LIKED_TRACK.value))],
        [InlineKeyboardButton("🔎️ Поиск трека",
                              callback_data=str(CallbackData.SEND_TRACK_REQUEST.value))],
        [InlineKeyboardButton("📁 Поиск альбома",
                              callback_data=str(CallbackData.SEND_ALBUM_REQUEST.value))],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(f"{format_users_of_group(group_id)}Выберите, чем хотите поделиться",
                                  reply_markup=reply_markup)
    return State.SHARE_MUSIC.value


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
    return State.SHARE_MUSIC.value


async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the initial step of searching for a music. Prompts the user to enter a search query.
    """

    logger.info(f"User {update.effective_user.id} in \"search_music\"")
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Введите ваш поисковый запрос\n\nИли напишить /start для отмены")
    return State.SEARCH_QUERY_MUSIC.value


async def search_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the initial step of searching for a track.
    """

    context.user_data["search"] = "track"
    return await search_music(update, context)


async def search_album(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the initial step of searching for an album.
    """

    context.user_data["search"] = "album"
    return await search_music(update, context)


async def receive_search_query(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the user's search query, performs a search, and displays the results as inline keyboard buttons.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"receive_search_query\"")
    query = update.message.text

    type_of_search = context.user_data["search"]
    result_of_search = await search_request(user.id, query, type_of_search)

    count_of_results = min(result_of_search.total, 7)

    keyboard = []
    for i in range(count_of_results):
        keyboard.append([InlineKeyboardButton(
            f"{result_of_search.results[i].artists[0].name} - {result_of_search.results[i].title}",
            callback_data=f"chosen_{result_of_search.results[i].id}")])
    keyboard.append([
        InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))
    ])
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите подходящий вариант", reply_markup=reply_markup)

    return State.SHARE_MUSIC.value


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the selection of a music and prompts the user to share their emotions about it.
    """

    logger.info(f"User {update.effective_user.id} in \"message_handler\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    music_id = int(callback_data.split("_")[1])
    context.user_data["share_id"] = music_id

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
    music_id = context.user_data["share_id"]
    type_of_search = context.user_data["search"]

    database.incr_count_of_sharing(user.id)

    user_message = update.message.text
    music_info = await get_track_info(user.id, music_id) if type_of_search == "track" else await get_album_info(user.id,
                                                                                                                music_id)

    await  send_message_to_users(update, context.bot, users=database.get_group_users(group_id),
                                 message_text=format_message(user.name, user_message, music_info, type_of_search),
                                 photo=fix_yandex_image_url(music_info.cover_uri),
                                 parse_mode=telegram.constants.ParseMode.HTML)

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("✅ Сообщение успешно обновлен", reply_markup=reply_markup)

    return State.START.value
