from telegram.ext import (
    ConversationHandler,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.group_management import (
    manage_groups_handler,
    create_group_handler,
    delete_group_handler,
    name_handler,
    receive_name_of_group_handler,
    confirm_group_deletion_handler,
    delete_group_callback_handler,
    check_name_and_choose_group_handler,
    add_user_to_the_group_handler,
    create_playlist_handler,
    group_playlist_handler,
)
from bot.history import (
    history_handler,
    carousel_navigation_handler,
    group_history_list_handler,
    group_history_carousel_handler,
    display_my_history_list_handler,
    display_my_history_carousel_handler,
    display_group_history_carousel_handler,
    display_group_history_list_handler,
)
from bot.rate_music import (
    rate_track_handler,
    choose_track_handler,
    chosen_track_handler,
    change_rating_handler,
)
from bot.sharing_music import (
    share_music_handler,
    choose_music_handler,
    message_handler,
    show_liked_track_handler,
    receive_message_handler,
    receive_search_query_handler,
    search_track_handler,
    search_album_handler,
    mark_callback_handler,
)
from bot.utils import pagination_handler
from bot.common_handlers import (
    start_handler,
    token_handler,
    receive_token_handler,
    account_handler,
)
from bot.constants import State, CallbackData

main_conversation = ConversationHandler(
    entry_points=[
        CommandHandler("start", start_handler),
        CommandHandler("token", token_handler),
        CommandHandler("account", account_handler),
    ],
    states={
        State.START.value: [
            CallbackQueryHandler(
                account_handler, pattern="^" + str(CallbackData.ACCOUNT.value) + "$"
            ),
            CallbackQueryHandler(
                manage_groups_handler,
                pattern="^" + str(CallbackData.MANAGE_GROUPS.value) + "$",
            ),
            CallbackQueryHandler(
                create_group_handler,
                pattern="^" + str(CallbackData.CREATE_GROUP.value) + "$",
            ),
            CallbackQueryHandler(
                delete_group_handler,
                pattern="^" + str(CallbackData.DELETE_GROUP.value) + "$",
            ),
            CallbackQueryHandler(
                name_handler, pattern="^" + str(CallbackData.ADD_USER.value) + "$"
            ),
            CallbackQueryHandler(
                token_handler,
                pattern="^" + str(CallbackData.UPDATE_TOKEN.value) + "$",
            ),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
            CallbackQueryHandler(
                share_music_handler,
                pattern="^" + str(CallbackData.SEND_MESSAGE.value) + "$",
            ),
            CallbackQueryHandler(
                rate_track_handler,
                pattern="^" + str(CallbackData.RATE_TRACK.value) + "$",
            ),
            CallbackQueryHandler(
                history_handler, pattern="^" + str(CallbackData.HISTORY.value) + "$"
            ),
            CallbackQueryHandler(
                create_playlist_handler,
                pattern="^" + str(CallbackData.CREATE_PLAYLIST.value) + "$",
            ),
            CallbackQueryHandler(group_playlist_handler, pattern="^playlist_"),
        ],
        State.CREATE_GROUP.value: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, receive_name_of_group_handler
            )
        ],
        State.DELETE_GROUP.value: [
            CallbackQueryHandler(confirm_group_deletion_handler, pattern="^delete_"),
            CallbackQueryHandler(delete_group_callback_handler, pattern="^exactly_"),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
        ],
        State.TAKE_USERNAME.value: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, check_name_and_choose_group_handler
            )
        ],
        State.USER_TO_GROUP.value: [
            CallbackQueryHandler(
                name_handler, pattern="^" + str(CallbackData.ADD_USER.value) + "$"
            ),
            CallbackQueryHandler(add_user_to_the_group_handler, pattern="^addUser_"),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
        ],
        State.SHARE_MUSIC.value: [
            CallbackQueryHandler(choose_music_handler, pattern="^share_"),
            CallbackQueryHandler(
                show_liked_track_handler,
                pattern="^" + str(CallbackData.CHOOSE_LIKED_TRACK.value) + "$",
            ),
            CallbackQueryHandler(pagination_handler, pattern="^(prev|next)_\\d+$"),
            CallbackQueryHandler(message_handler, pattern="^chosen_"),
            CallbackQueryHandler(
                search_track_handler,
                pattern="^" + str(CallbackData.SEND_TRACK_REQUEST.value) + "$",
            ),
            CallbackQueryHandler(
                search_album_handler,
                pattern="^" + str(CallbackData.SEND_ALBUM_REQUEST.value) + "$",
            ),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
        ],
        State.RATE_MUSIC.value: [
            CallbackQueryHandler(choose_track_handler, pattern="^rate_"),
            CallbackQueryHandler(pagination_handler, pattern="^(prev|next)_\\d+$"),
            CallbackQueryHandler(chosen_track_handler, pattern="^chosen_"),
            CallbackQueryHandler(change_rating_handler, pattern="^rating_"),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
        ],
        State.TAKE_MESSAGE.value: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_message_handler)
        ],
        State.ENTER_TOKEN.value: [
            MessageHandler(filters.TEXT & ~filters.COMMAND, receive_token_handler)
        ],
        State.SEARCH_QUERY_MUSIC.value: [
            MessageHandler(
                filters.TEXT & ~filters.COMMAND, receive_search_query_handler
            )
        ],
        State.VIEW_HISTORY.value: [
            CallbackQueryHandler(
                history_handler, pattern="^" + str(CallbackData.HISTORY.value) + "$"
            ),
            CallbackQueryHandler(
                display_my_history_list_handler,
                pattern="^" + str(CallbackData.MY_HISTORY.value) + "$",
            ),
            CallbackQueryHandler(
                display_my_history_carousel_handler,
                pattern="^" + str(CallbackData.MY_HISTORY_COR.value) + "$",
            ),
            CallbackQueryHandler(
                carousel_navigation_handler, pattern="^(prev|next)_\\d+$"
            ),
            CallbackQueryHandler(
                group_history_list_handler,
                pattern="^" + str(CallbackData.GROUP_HISTORY.value) + "$",
            ),
            CallbackQueryHandler(
                group_history_carousel_handler,
                pattern="^" + str(CallbackData.GROUP_HISTORY_COR.value) + "$",
            ),
            CallbackQueryHandler(
                history_handler,
                pattern="^" + str(CallbackData.MANAGE_GROUPS.value) + "$",
            ),
            CallbackQueryHandler(
                display_group_history_list_handler, pattern="^listHistory"
            ),
            CallbackQueryHandler(
                display_group_history_carousel_handler, pattern="^carouselHistory"
            ),
            CallbackQueryHandler(
                start_handler, pattern="^" + str(CallbackData.MENU.value) + "$"
            ),
        ],
    },
    fallbacks=[
        CommandHandler("start", start_handler),
        CommandHandler("token", token_handler),
    ],
)


def register_handlers(application):
    """
    Registers all command and conversation handlers with the bot application.
    """

    application.add_handler(
        CallbackQueryHandler(mark_callback_handler, pattern="^mark_")
    )
    application.add_handler(main_conversation)
