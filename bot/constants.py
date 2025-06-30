from enum import auto, Enum


class State(Enum):
    """States"""

    START = auto()
    ENTER_TOKEN = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    TAKE_USERNAME = auto()
    USER_TO_GROUP = auto()
    SHARE_TRACK = auto()
    RATE_MUSIC = auto()
    TAKE_MESSAGE = auto()
    SHARE_MUSIC = auto()
    SEARCH_QUERY_MUSIC = auto()
    VIEW_HISTORY = auto()


class CallbackData(Enum):
    """Callback data"""

    MENU = auto()
    ACCOUNT = auto()
    MANAGE_GROUPS = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    ADD_USER = auto()
    UPDATE_TOKEN = auto()
    SEND_MESSAGE = auto()
    CHOOSE_LIKED_TRACK = auto()
    SEND_TRACK_REQUEST = auto()
    SEND_ALBUM_REQUEST = auto()
    HISTORY = auto()
    MY_HISTORY = auto()
    MY_HISTORY_COR = auto()
    GROUP_HISTORY = auto()
    GROUP_HISTORY_COR = auto()
    CREATE_PLAYLIST = auto()
    RATE_TRACK = auto()
