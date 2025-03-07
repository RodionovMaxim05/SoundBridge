import logging

from decouple import config
from telegram import Update
from telegram.ext import Application

from bot.conversation import register_handlers

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def main() -> None:
    """
    Initializes the bot, sets up the application, and starts polling for updates.
    """

    application = Application.builder().token(config('TOKEN')).build()
    register_handlers(application)
    application.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
