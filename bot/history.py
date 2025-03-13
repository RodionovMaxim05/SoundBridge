import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.common_handlers import logger, group_selection
from bot.music import get_track_info, get_album_info
from bot.utils import database, make_url_for_music
from constants import State, CallbackData


async def history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the initial step of viewing history. Displays options to view personal or group history.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"history_handler\"")
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton("🚮 Моя история", callback_data=str(CallbackData.MY_HISTORY.value))],
        [InlineKeyboardButton("👨‍👩‍👦‍👦 История группы", callback_data=str(CallbackData.GROUP_HISTORY.value))],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text("Выберите, чью история, хотите посмотреть", reply_markup=reply_markup)
    return State.VIEW_HISTORY.value


async def format_history_music(music, is_group: bool, index: int) -> str:
    """
    Formats a single music entry into a clickable link with user or group information.
    """

    music_info = await get_track_info(music.user_id,
                                      music.yandex_id) if music.type == "track" else await get_album_info(music.user_id,
                                                                                                          music.yandex_id)
    music_url = make_url_for_music(music_info, music.type)

    if is_group:
        return f"{index}. <a href=\"{music_url}\">{music.title}</a> | Пользователь: {database.get_username(music.user_id)}"
    else:
        return f"{index}. <a href=\"{music_url}\">{music.title}</a> | Группа: {database.get_group_name(music.group_id)}"


async def get_my_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the user's personal sharing history.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"get_my_history\"")
    query = update.callback_query
    await query.answer()

    history = database.get_user_sharing(user.id)

    keyboard = [[InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.HISTORY.value))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = "Моя история:\n\n" + "\n".join(
        [await format_history_music(music, is_group=False, index=index) for index, music in enumerate(history)])
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.HTML,
                                  disable_web_page_preview=True)

    return State.VIEW_HISTORY.value


async def group_history_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Handles the selection of a group to view its sharing history.
    """

    user = update.effective_user
    logger.info(f"User {user.id} in \"group_history_handler\"")
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "history")

    await query.edit_message_text("Выберите группу, историю которой хотите посмотреть", reply_markup=reply_markup)
    return State.VIEW_HISTORY.value


async def get_group_history(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the sharing history of a selected group.
    """

    logger.info(f"User {update.effective_user.id} in \"get_group_history\"")
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    history = database.get_group_sharing(group_id)

    keyboard = [[InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.HISTORY.value))]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    text = f"История группы {database.get_group_name(group_id)}:\n\n" + "\n".join(
        [await format_history_music(music, is_group=True, index=index) for index, music in enumerate(history)])
    await query.edit_message_text(text, reply_markup=reply_markup, parse_mode=telegram.constants.ParseMode.HTML,
                                  disable_web_page_preview=True)

    return State.VIEW_HISTORY.value
