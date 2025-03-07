from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot.handlers import check_name_and_choose_group, name_handler, add_user_to_the_group
from constants import State, CallbackData
from handlers import start_handler, manage_groups, create_group_handler, receive_name_of_group, delete_group_handler, \
    confirm_group_deletion, delete_group_callback_handler, token_handler, receive_token, help_handler, account_handler

main_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_handler),
        CommandHandler("token", token_handler)
    ],
    states={
        State.START.value: [
            CallbackQueryHandler(account_handler, pattern="^" + str(CallbackData.ACCOUNT.value) + "$"),
            CallbackQueryHandler(manage_groups, pattern="^" + str(CallbackData.MANAGE_GROUPS.value) + "$"),
            CallbackQueryHandler(create_group_handler, pattern="^" + str(CallbackData.CREATE_GROUP.value) + "$"),
            CallbackQueryHandler(delete_group_handler, pattern="^" + str(CallbackData.DELETE_GROUP.value) + "$"),
            CallbackQueryHandler(name_handler, pattern="^" + str(CallbackData.ADD_USER.value) + "$"),
            CallbackQueryHandler(token_handler, pattern="^" + str(CallbackData.UPDATE_TOKEN.value) + "$"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.CREATE_GROUP.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_name_of_group)],
        State.DELETE_GROUP.value: [
            CallbackQueryHandler(confirm_group_deletion, pattern="^delete_"),
            CallbackQueryHandler(delete_group_callback_handler, pattern="^exactly_"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.TAKE_USERNAME.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, check_name_and_choose_group)],
        State.USER_TO_GROUP.value: [
            CallbackQueryHandler(name_handler, pattern="^" + str(CallbackData.ADD_USER.value) + "$"),
            CallbackQueryHandler(add_user_to_the_group, pattern="^addUser*"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.ENTER_TOKEN.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
    },
    fallbacks=[CommandHandler("start", start_handler)],
)


def register_handlers(application):
    """
    Registers all command and conversation handlers with the bot application.
    """

    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(CommandHandler('account', account_handler))
    application.add_handler(main_conversation)
