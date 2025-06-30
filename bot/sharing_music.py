import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Bot,
    InputMediaPhoto,
)
from telegram.error import TelegramError
from telegram.ext import ContextTypes

from bot.common_handlers import (
    logger,
    group_selection,
    handle_error_with_back_button,
)
from bot.music import (
    get_last_five_liked_track,
    get_track_info,
    search_request,
    get_album_info,
)
from bot.utils import (
    database,
    format_users_of_group,
    fix_yandex_image_uri,
    format_message,
    format_track_name,
)
from constants import State, CallbackData


async def share_music_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handles the initial step of sharing a music. Displays a list of user's groups to choose from.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "share_music_handler"')
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "share")
    await query.edit_message_text(
        "Выберите группу, с которой хотите поделиться", reply_markup=reply_markup
    )
    return State.SHARE_MUSIC.value


async def choose_music_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the selection of a group and prompts the user to choose a music to share.
    """

    logger.info(f'User {update.effective_user.id} in "choose_music_handler"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])
    context.user_data["share_group_id"] = group_id

    keyboard = [
        [
            InlineKeyboardButton(
                "❤️ Выбрать из 5 последних любимых",
                callback_data=str(CallbackData.CHOOSE_LIKED_TRACK.value),
            )
        ],
        [
            InlineKeyboardButton(
                "🔎️ Поиск трека",
                callback_data=str(CallbackData.SEND_TRACK_REQUEST.value),
            )
        ],
        [
            InlineKeyboardButton(
                "📁 Поиск альбома",
                callback_data=str(CallbackData.SEND_ALBUM_REQUEST.value),
            )
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{format_users_of_group(group_id)}Выберите, чем хотите поделиться",
        reply_markup=reply_markup,
    )
    return State.SHARE_MUSIC.value


async def show_liked_track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Displays the last five liked tracks for the user to choose from.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "choose_track_handler"')
    query = update.callback_query
    await query.answer()

    try:
        liked_tracks = await get_last_five_liked_track(user.id)
    except ValueError as e:
        return await handle_error_with_back_button(update, context, str(e))

    keyboard = [
        [
            InlineKeyboardButton(
                f"{', '.join(artist.name for artist in track.artists)} — {track.title}",
                callback_data=f"chosen_{track.id}",
            )
        ]
        for track in liked_tracks
    ]
    keyboard.append(
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"{format_users_of_group(context.user_data["share_group_id"])}Выберите, чем хотите поделиться",
        reply_markup=reply_markup,
    )
    return State.SHARE_MUSIC.value


async def search_music(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the initial step of searching for a music. Prompts the user to enter a search query.
    """

    logger.info(f'User {update.effective_user.id} in "search_music"')
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Введите ваш поисковый запрос\n\nИли напишить /start для отмены"
    )

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


async def receive_search_query(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the user's search query, performs a search, and displays the results as inline keyboard buttons.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "receive_search_query"')
    user_message = update.message.text

    type_of_search = context.user_data["search"]

    try:
        result_of_search = await search_request(user.id, user_message, type_of_search)
    except ValueError as e:
        return await handle_error_with_back_button(update, context, str(e))

    count_of_results = min(result_of_search.total + 1, 7) - 1

    keyboard = [
        [
            InlineKeyboardButton(
                f"{result_of_search.results[i].artists[0].name} - {result_of_search.results[i].title}",
                callback_data=f"chosen_{result_of_search.results[i].id}",
            )
        ]
        for i in range(count_of_results)
    ]
    keyboard.append(
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data=f"share_{context.user_data["share_group_id"]}",
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "Выберите подходящий вариант", reply_markup=reply_markup
    )

    return State.SHARE_MUSIC.value


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the selection of a music and prompts the user to share their emotions about it.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "message_handler"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    yandex_id = int(callback_data.split("_")[1])
    context.user_data["yandex_id"] = yandex_id

    type_of_search = context.user_data.get("search", "track")
    music_info = (
        await get_track_info(user.id, yandex_id)
        if type_of_search == "track"
        else await get_album_info(user.id, yandex_id)
    )

    caption = (
        format_track_name(music_info, type_of_search)
        + "Поделитесь эмоциями об этом треке\n\nИли напишите /start для отмены"
    )
    await query.edit_message_media(
        media=InputMediaPhoto(
            media=fix_yandex_image_uri(music_info.cover_uri),
            caption=caption,
            parse_mode=telegram.constants.ParseMode.HTML,
        )
    )

    return State.TAKE_MESSAGE.value


async def send_message_to_users(
    update: Update,
    bot: Bot,
    music_id: any,
    users: any,
    message_text: str,
    photo: str,
    parse_mode: str = None,
) -> None:
    """
    Sends a message to a list of users by their user IDs.
    """

    keyboard = [
        [
            InlineKeyboardButton(f"{index}", callback_data=f"mark_{index}_{music_id}")
            for index in range(6)
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    for user in users:
        if (
            user.id != update.effective_user.id
        ):  # Avoid sending the message to the sender
            try:
                await bot.send_photo(
                    chat_id=user.id,
                    photo=photo,
                    caption=message_text,
                    parse_mode=parse_mode,
                    reply_markup=reply_markup,
                )
                logger.info(f"Message sent to user {user.id}.")
            except TelegramError as e:
                logger.error(f"Failed to send message to user {user.id}: {e}")


async def receive_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Receives the user's message and sends it to the selected group.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "receive_message"')

    group_id = context.user_data.get("share_group_id")
    yandex_id = context.user_data["yandex_id"]
    type_of_search = context.user_data.get("search", "track")

    database.incr_count_of_sharing(user.id)

    user_message = update.message.text
    music_info = (
        await get_track_info(user.id, yandex_id)
        if type_of_search == "track"
        else await get_album_info(user.id, yandex_id)
    )

    photo_uri = fix_yandex_image_uri(music_info.cover_uri)

    music_id = database.insert_music(
        yandex_id=yandex_id,
        title=f"{', '.join(artist.name for artist in music_info.artists)} — {music_info.title}",
        message=user_message,
        type_of_music=type_of_search,
        photo_uri=photo_uri,
        user_id=user.id,
        group_id=group_id,
    )

    await send_message_to_users(
        update,
        context.bot,
        music_id=music_id,
        users=database.get_group_users(group_id),
        message_text=format_message(
            user.name, user_message, music_info, type_of_search
        ),
        photo=photo_uri,
        parse_mode=telegram.constants.ParseMode.HTML,
    )

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✅ Сообщение успешно отправлено", reply_markup=reply_markup
    )

    return State.START.value


async def mark_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> None:
    """
    Handles the user's response to the inline keyboard.
    """

    query = update.callback_query
    await query.answer()

    callback_data = query.data
    mark = int(callback_data.split("_")[1])
    music_id = int(callback_data.split("_")[2])

    user = query.from_user
    logger.info(f"User {user.id} selected mark {mark}")

    database.rate_music(user.id, music_id, mark)

    await query.delete_message()
