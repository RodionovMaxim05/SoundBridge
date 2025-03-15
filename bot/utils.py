import telegram
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from yandex_music import Track

from database import Database

database = Database()


def format_groups_with_users(user_id: int) -> str:
    """
    Formats the list of groups and their members for a given user into a readable string.
    """

    user_groups = database.get_user_groups(user_id)
    return "\n\n".join(
        f"Группа: {group.name}\n\t\t\t\tУчастники: {', '.join(user.name for user in database.get_group_users(group.id))}"
        for group in user_groups
    )


def format_users_of_group(group_id: int) -> str:
    """
    Formats the information about a group and its members into a readable string.
    """

    return (
        f"Группа: {database.get_group_name(group_id)}\n\t\t\t\tУчастники: {', '.join(user.name for user in database.get_group_users(group_id))}\n\n"
    )


async def send_or_edit_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str,
                               reply_markup: InlineKeyboardMarkup = None,
                               parse_mode: str = None) -> None:
    """
    A universal function for sending or editing a message.
    Determines whether a new message should be sent or an existing one edited.
    """

    try:
        if update.message:
            await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
        else:
            await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    except:
        query = update.callback_query
        await query.answer()
        await query.delete_message()
        await query.message.reply_text(text=text, parse_mode=telegram.constants.ParseMode.HTML,
                                       reply_markup=reply_markup)


def fix_yandex_image_uri(url: str, size: str = "m1000x1000") -> str:
    """
    Fixes a Yandex image URL by adding the protocol and replacing `%%` with the desired size.
    """

    if not url.startswith("http"):
        url = f"https://{url}"
    if url.endswith("/%%"):
        url = url.replace("/%%", f"/{size}")
    return url


def make_url_for_music(music_info: Track, type_of_search: str):
    """
    Generates a Yandex Music URL for the given music.
    """

    return f"https://music.yandex.ru/album/{music_info.albums[0].id}/track/{music_info.id}" if type_of_search == "track" else f"https://music.yandex.ru/album/{music_info.id}"


def format_track_name(music_info: Track, type_of_search: str) -> str:
    """
    Formats a message with music information.
    """

    return f"<a href=\"{make_url_for_music(music_info, type_of_search)}\">{', '.join(artist.name for artist in music_info.artists)} — {music_info.title}</a>\n\n"


def format_message(username: str, user_message: str, music_info: Track, type_of_search: str) -> str:
    """
    Formats a message with music information and user's comment.
    """

    return (
            format_track_name(music_info, type_of_search) + f"От {username}:\n<blockquote>{user_message}</blockquote>")
