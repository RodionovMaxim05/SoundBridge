from enum import auto, Enum


class State(Enum):
    """States"""

    START = auto()
    ENTER_TOKEN = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    TAKE_USERNAME = auto()
    USER_TO_GROUP = auto()


class CallbackData(Enum):
    """Callback data"""

    MENU = auto()
    ACCOUNT = auto()
    MANAGE_GROUPS = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    ADD_USER = auto()
    UPDATE_TOKEN = auto()
