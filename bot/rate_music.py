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
from bot.utils import (
    database,
    fix_yandex_image_uri,
    send_or_edit_message,
    build_paginated_keyboard,
)
from bot.constants import State, CallbackData


async def rate_track_handler(update: Update, _) -> int:
    """
    Handler for starting the rating process. Shows a list of groups to choose from.
    """

    user = update.effective_user
    logger.info('User %d in "rate_track_handler"', user.id)
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "rate")
    await query.edit_message_text(
        "Выберите группу, в которой хотите оценить трек", reply_markup=reply_markup
    )

    return State.RATE_MUSIC.value


async def choose_track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Shows tracks available for rating in the selected group.
    """

    user = update.effective_user
    logger.info('User %d in "choose_track"', user.id)
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

    context.user_data["data"] = tracks

    reply_markup, _ = build_paginated_keyboard(tracks, page=0)

    await send_or_edit_message(
        update,
        text="Выберите трек",
        reply_markup=reply_markup,
    )


async def chosen_track_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Displays selected track info and shows rating buttons.
    """

    user = update.effective_user
    logger.info('User %d in "chosen_track_handler"', user.id)
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
                callback_data=f"rate_{context.user_data['share_group_id']}",
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


async def change_rating_handler(update: Update, _):
    """
    Applies the user's rating to the selected track.
    """

    user = update.effective_user
    logger.info('User %d in "change_rating_handler"', user.id)
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
        text="✅ Оценка успешно поставлена",
        reply_markup=reply_markup,
    )
