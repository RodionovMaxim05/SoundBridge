import yandex_music.exceptions
from yandex_music import ClientAsync

from bot.utils import database


async def get_yandex_music_client(user_id: int):
    """
    Retrieves and validates the Yandex Music token, then initializes the client.
    """

    token = database.get_token(user_id)
    if not token:
        raise ValueError(
            "❌ У вас нет токена для доступа в Яндекс Музыку.\n\nПожалуйста, обновите его, используя /token")

    try:
        client = await ClientAsync(token).init()
        return client
    except yandex_music.exceptions.YandexMusicError:
        raise ValueError("❌ Ваш токен Яндекс Музыки неверен.\n\nПожалуйста, обновите его, используя /token")


async def get_last_five_liked_track(user_id: int):
    client = await get_yandex_music_client(user_id)

    five_liked_short_track = (await client.users_likes_tracks())[:5]
    result = []
    for i in range(0, 5):
        result.append((await client.tracks(five_liked_short_track[i].id))[0])

    return result


async def get_track_info(user_id: int, track_id: int):
    client = await get_yandex_music_client(user_id)

    return (await client.tracks(track_id))[0]


async def get_album_info(user_id: int, track_id: int):
    client = await get_yandex_music_client(user_id)

    return (await client.albums(track_id))[0]


async def search_request(user_id: int, query: str, type_of_search: str):
    client = await get_yandex_music_client(user_id)

    return (await client.search(query)).tracks if type_of_search == "track" else (await client.search(query)).albums
