import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
)
from telegram.ext import ContextTypes

from bot.common_handlers import logger, group_selection
from bot.music import get_track_info, get_album_info
from bot.utils import (
    database,
    make_url_for_music,
    fix_yandex_image_uri,
    send_or_edit_message,
)
from bot.constants import State, CallbackData


async def history_handler(update: Update, _) -> int:
    """
    Handles the initial step of viewing history. Displays options to view personal or group history.
    """

    user = update.effective_user
    logger.info('User %d in "history_handler"', user.id)

    keyboard = [
        [
            InlineKeyboardButton(
                "🚮 Моя история списком",
                callback_data=str(CallbackData.MY_HISTORY.value),
            ),
            InlineKeyboardButton(
                "🎠 Моя история каруселью",
                callback_data=str(CallbackData.MY_HISTORY_COR.value),
            ),
        ],
        [
            InlineKeyboardButton(
                "👨‍👩‍👦‍👦 История группы",
                callback_data=str(CallbackData.GROUP_HISTORY.value),
            ),
            InlineKeyboardButton(
                "🎡 История группы каруселью",
                callback_data=str(CallbackData.GROUP_HISTORY_COR.value),
            ),
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(
        update,
        text="Выберите, чью историю хотите посмотреть",
        reply_markup=reply_markup,
    )
    return State.VIEW_HISTORY.value


def get_carousel_keyboard(current_index, total_items):
    """
    Generates a carousel keyboard with navigation buttons.
    """

    keyboard = []
    if current_index > 0:
        keyboard.append(
            InlineKeyboardButton("⬅️", callback_data=f"prev_{current_index}")
        )
    if current_index < total_items - 1:
        keyboard.append(
            InlineKeyboardButton("➡️", callback_data=f"next_{current_index}")
        )
    return InlineKeyboardMarkup(
        [
            keyboard,
            [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data=str(CallbackData.HISTORY.value)
                )
            ],
        ]
    )


async def simple_format_history_music(music, is_group: bool, index: int) -> str:
    """
    Formats a single music entry into a clickable link with user or group information.
    """

    music_info = (
        await get_track_info(music.user_id, music.yandex_id)
        if music.type_of_music == "track"
        else await get_album_info(music.user_id, music.yandex_id)
    )

    music_url = make_url_for_music(music_info, music.type_of_music)

    text = (
        f'<b>{index}.</b> <a href="{music_url}">{music.title}</a> | '
        f"Ср. оценка: {music.average_mark:.2f} "
    )
    if is_group:
        text += f"| Пользователь: {database.get_username(music.user_id)}"
    else:
        text += f"| Группа: {database.get_group_name(music.group_id)}"

    return text


async def format_music_entry(music, is_group: bool, index: int = -1) -> str:
    """
    Formats a single music entry into a clickable link with user or group information.
    """

    music_info = (
        await get_track_info(music.user_id, music.yandex_id)
        if music.type_of_music == "track"
        else await get_album_info(music.user_id, music.yandex_id)
    )
    music_url = make_url_for_music(music_info, music.type_of_music)

    mark = music.average_mark if music.count_of_ratings > 0 else "Оценок нет"
    if index != -1:
        text = (
            f'{index}. <a href="{music_url}">{music.title}</a>\n\n<b>Ср. '
            f"оценка: {mark:.2f}</b>\n\n"
        )
    else:
        text = (
            f'<a href="{music_url}">{music.title}</a>\n\n<b>Ср. оценка: '
            f"{mark:.2f}</b>\n\n Пользователь: {database.get_username(music.user_id)}\n"
        )

    if is_group:
        text += (
            f"Пользователь: {database.get_username(music.user_id)}\n<blockquote>"
            f"{music.message}</blockquote>"
        )
    else:
        group_name = database.get_group_name(music.group_id)
        if group_name is None:
            text += f"Группа: Без группы\n<blockquote>{music.message}</blockquote>"
        else:
            text += (
                f"Группа: {database.get_group_name(music.group_id)}\n<blockquote>"
                f"{music.message}</blockquote>"
            )

    return text


async def get_history_data(update: Update, is_group: bool) -> tuple[list, str]:
    """
    Fetches the history data and prepares the initial text.
    """

    if is_group:
        callback_data = update.callback_query.data
        group_id = int(callback_data.split("_")[1])
        history = database.get_group_sharing(group_id)
        text = f"<b>История группы {database.get_group_name(group_id)}</b>\n\n"
    else:
        history = database.get_user_sharing(update.effective_user.id)
        text = "<b>Моя история:</b>\n\n"

    return history, text


async def display_carousel(query, history: list, is_group: bool):
    """
    Displays the history as a carousel.
    """

    current_index = 0
    music = history[current_index]
    text = await format_music_entry(music, is_group=is_group, index=current_index + 1)
    reply_markup = get_carousel_keyboard(current_index, len(history))

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=fix_yandex_image_uri(music.photo_uri),
            caption=text,
            parse_mode=telegram.constants.ParseMode.HTML,
        ),
        reply_markup=reply_markup,
    )


async def display_list(query, history: list, text: str, is_group: bool):
    """
    Displays the history as a list.
    """

    text += "\n".join(
        [
            await simple_format_history_music(
                music, is_group=is_group, index=(index + 1)
            )
            for index, music in enumerate(history)
        ]
    )
    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Назад", callback_data=str(CallbackData.HISTORY.value)
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        text,
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML,
        disable_web_page_preview=True,
    )


async def get_history(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    is_carousel: bool,
    is_group: bool,
):
    """
    Displays the sharing history either as a carousel or a list.
    """

    query = update.callback_query
    await query.answer()

    history, text = await get_history_data(update, is_group)
    if not history:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data=str(CallbackData.MENU.value)
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        await query.edit_message_text("Ваша история пуста", reply_markup=reply_markup)
        return State.VIEW_HISTORY.value

    if is_carousel:
        await display_carousel(query, history, is_group)
        context.user_data["is_group"] = is_group
        context.user_data["group_sharing_history"] = history
    else:
        await display_list(query, history, text, is_group)


async def carousel_navigation_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Handles navigation through the carousel.
    """

    logger.info('User %d in "carousel_navigation_handler"', update.effective_user.id)
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    direction, current_index = callback_data.split("_")
    current_index = int(current_index)

    history = context.user_data["group_sharing_history"]

    if direction == "prev":
        current_index -= 1
    elif direction == "next":
        current_index += 1

    music = history[current_index]
    text = await format_music_entry(
        music, is_group=context.user_data["is_group"], index=current_index + 1
    )
    reply_markup = get_carousel_keyboard(current_index, len(history))

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=fix_yandex_image_uri(music.photo_uri),
            caption=text,
            parse_mode=telegram.constants.ParseMode.HTML,
        ),
        reply_markup=reply_markup,
    )


async def select_group_history(update: Update, cl_data):
    """
    Allows to select a group to view its sharing history.
    """

    user = update.effective_user
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, cl_data)
    await query.edit_message_text(
        "Выберите группу, историю которой хотите посмотреть",
        reply_markup=reply_markup,
    )


async def group_history_list_handler(update: Update, _):
    """
    Handles the selection of a group to view its sharing history as a list.
    """

    logger.info('User %d in "group_history_list_handler"', update.effective_user.id)
    await select_group_history(update, "listHistory")


async def group_history_carousel_handler(update: Update, _):
    """
    Handles the selection of a group to view its sharing history as a carousel.
    """

    logger.info('User %d in "group_history_carousel_handler"', update.effective_user.id)
    await select_group_history(update, "carouselHistory")


async def display_my_history_list_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Displays the user's personal sharing history as a list.
    """

    logger.info(
        'User %d in "display_my_history_list_handler"', update.effective_user.id
    )
    await get_history(update, context, is_group=False, is_carousel=False)


async def display_my_history_carousel_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Displays the user's personal sharing history as a carousel.
    """

    logger.info(
        'User %d in "display_my_history_carousel_handler"', update.effective_user.id
    )
    await get_history(update, context, is_group=False, is_carousel=True)


async def display_group_history_list_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Displays the group's sharing history as a list.
    """

    logger.info(
        'User %d in "display_group_history_list_handler"', update.effective_user.id
    )
    await get_history(update, context, is_group=True, is_carousel=False)


async def display_group_history_carousel_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Displays the group's sharing history as a carousel.
    """

    logger.info(
        'User %d in "display_group_history_carousel_handler"', update.effective_user.id
    )
    await get_history(update, context, is_group=True, is_carousel=True)
