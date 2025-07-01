import telegram
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from bot.common_handlers import logger, group_selection
from bot.music import create_or_update_playlist
from bot.sharing_music import handle_error_with_back_button
from bot.utils import database, format_groups_with_users
from constants import State, CallbackData


async def manage_groups_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the "Manage Groups" callback. Displays the user's groups and provides options to create or delete groups.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "manage_groups_handler"')
    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "🛠 Создать группу",
                callback_data=str(CallbackData.CREATE_GROUP.value),
            )
        ],
        [
            InlineKeyboardButton(
                "➕ Добавить пользователя в группу",
                callback_data=str(CallbackData.ADD_USER.value),
            )
        ],
        [
            InlineKeyboardButton(
                "🎧 Создать/Обновить общий плейлист",
                callback_data=str(CallbackData.CREATE_PLAYLIST.value),
            )
        ],
        [
            InlineKeyboardButton(
                "🗑 Удалить группу",
                callback_data=str(CallbackData.DELETE_GROUP.value),
            )
        ],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"<b>Ваши группы:</b>\n{format_groups_with_users(user.id)}",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML,
    )
    return State.START.value


async def create_group_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the "Create Group" callback. Checks if the user has reached the group limit
    and prompts the user to enter a group name.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "create_group_handler"')
    query = update.callback_query
    await query.answer()

    if len(database.get_user_groups(user.id)) >= 5:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🗑 Удалить группу",
                    callback_data=str(CallbackData.DELETE_GROUP.value),
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data=str(CallbackData.MENU.value)
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await query.edit_message_text(
            "❗️ Достигнут лимит количества групп, больше групп создавать нельзя",
            reply_markup=reply_markup,
        )
        return State.START.value

    await query.edit_message_text(
        "Введите название группы\n\nИли напишить /start для отмены"
    )
    return State.CREATE_GROUP.value


async def receive_name_of_group_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Receives the group name from the user and creates the group in the database.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "receive_name_of_group_handler"')
    user_message = update.message.text

    database.create_group(user_message, user.id)

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        f'✅ Группа "{user_message}" успешно создана', reply_markup=reply_markup
    )

    return State.START.value


async def delete_group_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the "Delete Group" callback. Displays a list of the user's groups for deletion.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "delete_group_handler"')
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "delete")

    await query.edit_message_text(
        "Выберите группы, которую хотите удалить", reply_markup=reply_markup
    )
    return State.DELETE_GROUP.value


async def confirm_group_deletion_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
):
    """
    Confirms the deletion of a group. Displays a confirmation message with options to proceed or cancel.
    """

    logger.info(f'User {update.effective_user.id} in "confirm_group_deletion_handler"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("🗑 Удалить группу", callback_data=f"exactly_{group_id}")],
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        f"❓ Вы действительно хотите удалить группу {database.get_group_name(group_id)}?",
        reply_markup=reply_markup,
    )


async def delete_group_callback_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the actual deletion of a group from the database.
    """

    logger.info(f'User {update.effective_user.id} in "delete_group_callback_handler"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    database.delete_group(group_id)

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(
        "✅ Группа успешно удалена", reply_markup=reply_markup
    )

    return State.START.value


async def name_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """
    Handles the username input step. Prompts the user to enter a username (with @) to add to a group.
    """

    logger.info(f'User {update.effective_user.id} in "name_handler"')
    query = update.callback_query
    await query.answer()

    await query.edit_message_text(
        "Введите Username пользователя (вместе с @)\n\nИли напишить /start для отмены"
    )

    return State.TAKE_USERNAME.value


async def check_name_and_choose_group_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Validates the entered username and displays a list of groups to which the user can be added.
    If the username is invalid, notifies the user and provides an option to go back.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "check_name_and_choose_group_handler"')

    user_message = update.message.text
    if database.check_username(user_message):
        groups = database.get_user_groups(user.id)
        context.user_data["add_user"] = user_message

        keyboard = []
        for group in groups:
            keyboard.append(
                [
                    InlineKeyboardButton(
                        f"{group.name}", callback_data=f"addUser_{group.id}"
                    )
                ]
            )

        keyboard.append(
            [
                InlineKeyboardButton(
                    f"🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value)
                )
            ]
        )
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            "Выберите группу, в которую хотите добавить пользователя",
            reply_markup=reply_markup,
        )
        return State.USER_TO_GROUP.value
    else:
        keyboard = [
            [
                InlineKeyboardButton(
                    "🔙 Назад", callback_data=str(CallbackData.MANAGE_GROUPS.value)
                )
            ],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"❌ Пользователя {user_message} нет в базе данных бота.\n\nЕсли username правильный, попросите пользователя запустить бота.",
            reply_markup=reply_markup,
        )

        return State.START.value


async def add_user_to_the_group_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Adds the selected user to the chosen group.
    """

    logger.info(f'User {update.effective_user.id} in "add_user_to_the_group_handler"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])
    username = context.user_data["add_user"]

    if len(database.get_group_users(group_id)) == 6:
        message = f"❌ В группе {database.get_group_name(group_id)} достигнут лимит количества пользователей"
    else:
        database.add_user_to_group(group_id, username)
        message = f"✅ Пользователь {username} успешно добавлен в группу {database.get_group_name(group_id)}"

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.edit_message_text(message, reply_markup=reply_markup)

    return State.START.value


async def create_playlist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Handles the initial step of creating or updating a playlist.
    Prompts the user to select a group for which the playlist will be created/updated.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "create_playlist_handler"')
    query = update.callback_query
    await query.answer()

    reply_markup = group_selection(user, "playlist")

    await query.edit_message_text(
        "<b>Как это работает</b>\n\nВ вашем аккаунте Яндекс Музыка создастся плейлист с названием вашей группы, "
        "в нем будут храниться все песни, которыми вы поделились в этом боте.\n❗️Кроме того, в него вы самостоятельно"
        "можете добавлять треки прямо в приложении, и они будут появляться у остальных участников вашей группы\n\n"
        "Выберите группу, для которой хотите создать/обновить плейлист",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML,
    )

    return State.START.value


async def group_playlist_handler(
    update: Update, context: ContextTypes.DEFAULT_TYPE
) -> int:
    """
    Processes the selected group and creates or updates the playlist for that group.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "group_playlist"')
    query = update.callback_query
    await query.answer()

    callback_data = query.data
    group_id = int(callback_data.split("_")[1])

    keyboard = [
        [InlineKeyboardButton("🔙 Назад", callback_data=str(CallbackData.MENU.value))],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        await create_or_update_playlist(
            user.id, group_id, database.get_group_name(group_id)
        )
    except ValueError as e:
        return await handle_error_with_back_button(update, context, str(e))

    await query.edit_message_text(
        f"✅ Плейлист {database.get_group_name(group_id)} успешно создан/обновлен",
        reply_markup=reply_markup,
    )

    return State.START.value
