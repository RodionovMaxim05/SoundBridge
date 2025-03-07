from telegram import Update, InlineKeyboardMarkup

from database import Database

database = Database()


def format_groups_with_users(user_id: int) -> str:
    """
    Formats the list of groups and their members for a given user into a readable string.
    """

    user_groups = database.get_user_groups(user_id)
    return "\n\n".join(
        f"Группа: {group.name}\nУчастники: {', '.join(user.name for user in database.get_group_users(group.id))}"
        for group in user_groups
    )


async def send_or_edit_message(update: Update, text: str, reply_markup: InlineKeyboardMarkup = None,
                               parse_mode: str = None) -> None:
    """
    A universal function for sending or editing a message.
    Determines whether a new message should be sent or an existing one edited.
    """
    if update.message:
        await update.message.reply_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
    else:
        await update.callback_query.edit_message_text(text=text, reply_markup=reply_markup, parse_mode=parse_mode)
