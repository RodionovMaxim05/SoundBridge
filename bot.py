import logging

import telegram
from decouple import config
from telegram import Update
from telegram.ext import Application, ConversationHandler, MessageHandler, filters
from telegram.ext import CommandHandler
from telegram.ext import ContextTypes

from database import Database

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

database = Database()


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    database.create_tables()
    print(f"{user.id} - {user.name}")
    database.insert_user(user.id, user.name)
    await update.message.reply_text('Привет! Я бот. Нажимай на кнопку "/help" для получения подсказок по командам.')


async def account_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    res = database.get_user_statistic(user.id)

    token = '✔️' if res.get('token') else '❌'
    await update.message.reply_text(
        text=f"<b>Ваш аккаунт\n\nТокен:</b> {token}\n\n📊 <b>Statistics\n\nКоличество:</b> {res.get('count_of_sharing')}\n",
        parse_mode=telegram.constants.ParseMode.HTML)


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("Помощи нет.")


ENTER_TOKEN = 1


async def token_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    await update.message.reply_text("Введите ваш токен")
    return ENTER_TOKEN


async def receive_token(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    user = update.effective_user
    user_message = update.message.text

    if database.update_user_token(user.id, user_message):
        await update.message.reply_text("Токен успешно обновлен")
    else:
        await update.message.reply_text("Что-то пошло не так")

    return ConversationHandler.END


token_conversation = ConversationHandler(
    entry_points=[CommandHandler("token", token_handler)],
    states={
        ENTER_TOKEN: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
    },
    fallbacks=[],
)


def register_handlers(application):
    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('account', account_handler))
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(token_conversation)


def main() -> None:
    application = Application.builder().token(config('TOKEN')).build()

    register_handlers(application)

    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
