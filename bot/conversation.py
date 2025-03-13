from telegram.ext import ConversationHandler, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot.group_management import manage_groups, create_group_handler, delete_group_handler, name_handler, \
    receive_name_of_group, confirm_group_deletion, delete_group_callback_handler, check_name_and_choose_group, \
    add_user_to_the_group
from bot.history import history_handler, get_my_history, get_group_history, group_history_handler
from bot.sharing_music import share_music_handler, choose_music_handler, message_handler, show_liked_track, \
    receive_message, receive_search_query, search_track, search_album
from common_handlers import start_handler, token_handler, receive_token, help_handler, account_handler
from constants import State, CallbackData

main_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_handler),
        CommandHandler("token", token_handler),
        CommandHandler("account", account_handler)
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
            CallbackQueryHandler(share_music_handler, pattern="^" + str(CallbackData.SEND_MESSAGE.value) + "$"),
            CallbackQueryHandler(history_handler, pattern="^" + str(CallbackData.HISTORY.value) + "$"),
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
            CallbackQueryHandler(add_user_to_the_group, pattern="^addUser_"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.SHARE_MUSIC.value: [
            CallbackQueryHandler(choose_music_handler, pattern="^share_"),
            CallbackQueryHandler(show_liked_track, pattern="^" + str(CallbackData.CHOOSE_LIKED_TRACK.value) + "$"),
            CallbackQueryHandler(message_handler, pattern="^chosen_"),
            CallbackQueryHandler(search_track, pattern="^" + str(CallbackData.SEND_TRACK_REQUEST.value) + "$"),
            CallbackQueryHandler(search_album, pattern="^" + str(CallbackData.SEND_ALBUM_REQUEST.value) + "$"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ],
        State.TAKE_MESSAGE.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message)],
        State.ENTER_TOKEN.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token)],
        State.SEARCH_QUERY_MUSIC.value: [MessageHandler(filters.TEXT & ~filters.COMMAND, receive_search_query)],
        State.VIEW_HISTORY.value: [
            CallbackQueryHandler(history_handler, pattern="^" + str(CallbackData.HISTORY.value) + "$"),
            CallbackQueryHandler(get_my_history, pattern="^" + str(CallbackData.MY_HISTORY.value) + "$"),
            CallbackQueryHandler(group_history_handler, pattern="^" + str(CallbackData.GROUP_HISTORY.value) + "$"),
            CallbackQueryHandler(get_group_history, pattern="^history_"),
            CallbackQueryHandler(start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"),
        ]

    },
    fallbacks=[CommandHandler("start", start_handler),
               CommandHandler("token", token_handler)],
)


def register_handlers(application):
    """
    Registers all command and conversation handlers with the bot application.
    """

    application.add_handler(CommandHandler('help', help_handler))
    application.add_handler(main_conversation)
