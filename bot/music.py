from yandex_music import ClientAsync

from bot.utils import database


async def get_last_five_liked_track(user_id: int):
    token = database.get_token(user_id)
    client = await ClientAsync(token).init()

    five_liked_short_track = (await client.users_likes_tracks())[:5]
    result = []
    for i in range(0, 5):
        result.append((await client.tracks(five_liked_short_track[i].id))[0])

    return result


async def get_track_info(user_id: int, track_id):
    token = database.get_token(user_id)
    client = await ClientAsync(token).init()

    return (await client.tracks(track_id))[0]
