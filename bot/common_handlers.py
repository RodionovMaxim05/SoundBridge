import logging

import telegram
from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    User,
)
from telegram.ext import ContextTypes

from bot.utils import database, send_or_edit_message
from constants import State, CallbackData

logger = logging.getLogger(__name__)


async def start_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """
    Handles the /start command. Initializes the bot, creates database tables,
    and inserts the user into the database. Displays a menu with options.
    """

    user = update.effective_user
    logger.info(f"User {user.id} - {user.name} started the bot.")
    database.create_tables()
    database.insert_user(user.id, user.name)

    keyboard = [
        [
            InlineKeyboardButton(
                "📊 Мой аккаунт",
                callback_data=str(CallbackData.ACCOUNT.value),
            )
        ],
        [
            InlineKeyboardButton(
                "👨‍👩‍👦‍👦 Управление группами",
                callback_data=str(CallbackData.MANAGE_GROUPS.value),
            )
        ],
        [
            InlineKeyboardButton(
                "🔉 Поделиться музыкой",
                callback_data=str(CallbackData.SEND_MESSAGE.value),
            )
        ],
        [
            InlineKeyboardButton(
                "💯 Оценить трек из плейлиста",
                callback_data=str(CallbackData.RATE_TRACK.value),
            )
        ],
        [
            InlineKeyboardButton(
                "📜 История",
                callback_data=str(CallbackData.HISTORY.value),
            )
        ],
        [
            InlineKeyboardButton(
                "⚙️ Обновить Токен",
                callback_data=str(CallbackData.UPDATE_TOKEN.value),
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await send_or_edit_message(
        update,
        text="Пожалуйста, выберите действие",
        reply_markup=reply_markup,
    )

    return State.START.value


async def token_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """
    Handles the "Update Token" callback. Prompts the user to enter a new token.
    """

    logger.info(f'User {update.effective_user.id} in "token_handler"')
    await send_or_edit_message(
        update,
        text="Введите ваш токен\n\nИли напишить /start для отмены\n\n❗️<b>Как получить токен</b>\n\n"
        'По <b><a href="https://github.com/MarshalX/yandex-music-api/discussions/513 ">этой ссылке</a></b> '
        "описано несколько способов, но самый удобный (и тот, которым пользовался я) - это использование "
        "расширения для Chrome или Firefox: \n<b>1.</b> Установите расширение\n<b>2.</b> Авторизуйтесь "
        "(если не произошло автоматически)\n<b>3.</b> Предоставьте доступ\n<b>4.</b> Снова откройте "
        "расширение (т.к. тг бот там не работает)\n<b>5.</b> Снизу слева нажмите на кнопку "
        '"Скопировать токен"\n<b>6.</b> Вставьте токен сюда',
        parse_mode=telegram.constants.ParseMode.HTML,
    )

    return State.ENTER_TOKEN.value


async def receive_token_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> int:
    """
    Receives the token from the user and updates it in the database.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "receive_token_handler"')

    user_message = update.message.text

    database.update_user_token(user.id, user_message)

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data=str(CallbackData.MENU.value),
            )
        ],
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "✅ Токен успешно обновлен",
        reply_markup=reply_markup,
    )

    return State.START.value


async def account_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
) -> None:
    """
    Handles the /account command. Displays the user's account information,
    including token status and sharing statistics.
    """

    user = update.effective_user
    logger.info(f'User {user.id} in "token_handler"')

    result = database.get_user_statistic(user.id)

    token = "✔️" if result.get("token") else "❌"

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data=str(CallbackData.MENU.value),
            )
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    score_rated = result.get("score_of_rated_music")
    score_shared = result.get("score_of_shared_music")
    score_rated_str = (
        f"{score_rated:.2f}" if isinstance(score_rated, (int, float)) else score_rated
    )
    score_shared_str = (
        f"{score_shared:.2f}"
        if isinstance(score_shared, (int, float))
        else score_shared
    )

    await send_or_edit_message(
        update,
        text=f"<b>Ваш аккаунт\n\nТокен:</b> {token}\n\n📊 <b>Статистика:</b>\n\n"
        f"💽 Количество композиций, которыми вы поделились: <b>{result.get('count_of_sharing')}</b>\n\n"
        f"💯 Средняя ваша оценка: <b>{score_rated_str}</b>\n\n"
        f"⭐️ Средняя оценка по вашей музыке: <b>{score_shared_str}</b>\n",
        reply_markup=reply_markup,
        parse_mode=telegram.constants.ParseMode.HTML,
    )

    return State.START.value


def group_selection(user: User, cl_data: str) -> InlineKeyboardMarkup:
    """
    Creates an inline keyboard markup for selecting a group.
    """

    groups = database.get_user_groups(user.id)

    keyboard = []
    for group in groups:
        keyboard.append(
            [
                InlineKeyboardButton(
                    f"{group.name}",
                    callback_data=f"{cl_data}_{group.id}",
                )
            ]
        )

    keyboard.append(
        [
            InlineKeyboardButton(
                f"🔙 Назад",
                callback_data=str(CallbackData.MENU.value),
            )
        ]
    )
    reply_markup = InlineKeyboardMarkup(keyboard)

    return reply_markup


async def handle_error_with_back_button(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    error_message: str,
    back_button_callback_data: str = str(CallbackData.MENU.value),
    state: int = State.START.value,
) -> int:
    """
    Handles errors by displaying an error message with a "Back" button.
    """

    keyboard = [
        [
            InlineKeyboardButton(
                "🔙 Назад",
                callback_data=back_button_callback_data,
            )
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await send_or_edit_message(
        update,
        text=error_message,
        reply_markup=reply_markup,
    )

    return state
