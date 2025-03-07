from enum import auto, Enum


class State(Enum):
    """States"""

    START = auto()
    ENTER_TOKEN = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()


class CallbackData(Enum):
    """Callback data"""

    MENU = auto()
    MANAGE_GROUPS = auto()
    CREATE_GROUP = auto()
    DELETE_GROUP = auto()
    UPDATE_TOKEN = auto()
