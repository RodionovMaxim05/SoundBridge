import telegram
from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
    InputMediaPhoto,
)
from telegram.ext import ContextTypes

from bot.common_handlers import logger, group_selection
from bot.history import format_music_entry
from bot.utils import database, fix_yandex_image_uri, send_or_edit_message
from constants import State, CallbackData


async def rate_track_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handler for starting the rating process. Shows a list of groups to choose from.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "rate_track_handler"')

    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "rate")
    await query.edit_message_text(
        "Выберите группу, в которой хотите оценить трек", reply_markup=reply_markup
    )

    return State.RATE_MUSIC.value


async def choose_track_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Shows tracks available for rating in the selected group.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "choose_track"')

    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])
    context.user_data["share_group_id"] = group_id

    tracks = [
        (music.title, music.id)
        for music in database.get_group_sharing(group_id)
        if music.type_of_music == "track" and music.user_id != user.id
    ]

    context.user_data["playlist"] = tracks

    reply_markup, _, _ = build_paginated_keyboard(tracks, page=0)

    await send_or_edit_message(
        update,
        context,
        text="Выберите, что хотите оценить",
        reply_markup=reply_markup,
    )
    return State.RATE_MUSIC.value


async def pagination_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handles pagination between tracks.
    """

    query = update.callback_query
    await query.answer()

    action, current_page = query.data.split("_")[0], int(query.data.split("_")[1])

    if action == "prev":
        current_page -= 1
    elif action == "next":
        current_page += 1

    reply_markup, current_page, total_pages = build_paginated_keyboard(
        context.user_data["playlist"], current_page
    )

    await query.edit_message_text(
        "Выберите, что хотите оценить", reply_markup=reply_markup
    )


def build_paginated_keyboard(data: list, page: int):
    """
    Builds an inline keyboard with pagination.
    """

    items_per_page = 5
    total_items = len(data)
    total_pages = (total_items + items_per_page - 1) // items_per_page

    page = max(0, min(page, total_pages - 1))

    start_index = page * items_per_page
    end_index = start_index + items_per_page
    current_page_items = data[start_index:end_index]

    keyboard = []

    for item in current_page_items:
        keyboard.append(
            [InlineKeyboardButton(str(item[0]), callback_data=f"chosen_{item[1]}")]
        )

    nav_buttons = []
    if page > 0:
        nav_buttons.append(
            InlineKeyboardButton("⬅️ Назад", callback_data=f"prev_{page}")
        )
    if page < total_pages - 1:
        nav_buttons.append(
            InlineKeyboardButton("➡️ Вперед", callback_data=f"next_{page}")
        )

    keyboard.append(nav_buttons)
    keyboard.append(
        [InlineKeyboardButton(f"🔙 Назад", callback_data=str(CallbackData.MENU.value))]
    )

    return InlineKeyboardMarkup(keyboard), page, total_pages


async def chosen_track_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Displays selected track info and shows rating buttons.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "chosen_track_handler"')

    query = update.callback_query
    await query.answer()

    track_id = int(query.data.split("_")[1])

    keyboard = [
        [
            InlineKeyboardButton(f"{index}", callback_data=f"rating_{index}_{track_id}")
            for index in range(6)
        ],
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"rate_{context.user_data["share_group_id"]}",
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    track = database.get_music_by_id(track_id)
    text = await format_music_entry(track, is_group=False)

    await query.edit_message_media(
        media=InputMediaPhoto(
            media=fix_yandex_image_uri(track.photo_uri),
            caption=text,
            parse_mode=telegram.constants.ParseMode.HTML,
        ),
        reply_markup=reply_markup,
    )

    return State.RATE_MUSIC.value


async def change_rating(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """
    Applies the user's rating to the selected track.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "change_rating"')

    query = update.callback_query
    await query.answer()

    callback_data = query.data
    mark = int(callback_data.split("_")[1])
    track_id = int(callback_data.split("_")[2])

    database.rate_music(user.id, track_id, mark)

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(
        update,
        context,
        text="✅ Оценка успешно поставлена",
        reply_markup=reply_markup,
    )

    return State.RATE_MUSIC.value
