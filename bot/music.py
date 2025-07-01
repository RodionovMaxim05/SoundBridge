import yandex_music.exceptions
from yandex_music import ClientAsync

from bot.common_handlers import logger
from bot.utils import database


async def get_yandex_music_client(user_id: int):
    """
    Retrieves and validates the Yandex Music token, then initializes the client.
    """

    token = database.get_token(user_id)
    if not token:
        raise ValueError(
            "❌ У вас нет токена для доступа в Яндекс Музыку.\n\nПожалуйста, обновите его, используя /token"
        )

    try:
        client = await ClientAsync(token).init()
        return client
    except yandex_music.exceptions.YandexMusicError:
        raise ValueError(
            "❌ Ваш токен Яндекс Музыки неверен.\n\nПожалуйста, обновите его, используя /token"
        )


async def get_last_n_liked_track(user_id: int, n: int):
    client = await get_yandex_music_client(user_id)

    five_liked_short_track = (await client.users_likes_tracks())[:n]
    result = []
    for i in range(0, n):
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

    return (
        (await client.search(query)).tracks
        if type_of_search == "track"
        else (await client.search(query)).albums
    )


async def get_group_track_list(user_id: int, group_id: int):
    client = await get_yandex_music_client(user_id)
    playlist = database.get_playlist(user_id, group_id)
    return (await client.users_playlists(playlist.kind)).tracks


async def update_tracks(client: ClientAsync, playlist, user_id: int, group_id: int):
    track_list_pl = (await client.users_playlists(playlist.kind)).tracks
    existing_track_ids_ym = {track.id for track in track_list_pl}

    for track in database.get_group_sharing(group_id):
        if track.type_of_music != "track":
            continue

        if track.yandex_id in existing_track_ids_ym:
            continue

        track_info = await get_track_info(user_id, track.yandex_id)
        updated_playlist = await client.users_playlists(kind=playlist.kind)

        await client.users_playlists_insert_track(
            kind=playlist.kind,
            track_id=track.yandex_id,
            revision=updated_playlist.revision,
            album_id=track_info.albums[0].id,
        )


async def download_new_tracks_from_playlist(user_id: int, group_id: int):
    client = await get_yandex_music_client(user_id)
    playlist = database.get_playlist(user_id, group_id)

    track_list_pl = (await client.users_playlists(playlist.kind)).tracks
    existing_track_ids_db = {
        music.yandex_id
        for music in database.get_group_sharing(group_id)
        if music.type_of_music == "track"
    }

    for track_pl in track_list_pl:
        if track_pl.id in existing_track_ids_db:
            continue

        track_info = await get_track_info(user_id, track_pl.id)

        database.insert_music(
            yandex_id=track_pl.id,
            title=f"{', '.join(artist.name for artist in track_info.artists)} — {track_info.title}",
            type_of_music="track",
            message="ДОБАВЛЕН ИЗ ПЛЕЙЛИСТА",
            photo_uri=track_info.cover_uri,
            user_id=user_id,
            group_id=group_id,
        )

        # Update playlists for other group members
        for groupmate in database.get_group_users(group_id):
            if groupmate.id != user_id and groupmate.token:
                playlist_usr = database.get_playlist(groupmate.id, group_id)
                groupmate_client = await get_yandex_music_client(groupmate.id)

                await update_tracks(
                    groupmate_client, playlist_usr, groupmate.id, group_id
                )


async def create_or_update_playlist(user_id: int, group_id: int, title: str = ""):
    client = await get_yandex_music_client(user_id)

    playlist = database.get_playlist(user_id, group_id)
    if not playlist:
        if title:
            playlist = await client.users_playlists_create(title)
            database.create_playlist_for_user_in_group(
                user_id, group_id, playlist.kind, playlist.owner.uid
            )
        else:
            return

    await update_tracks(client, playlist, user_id, group_id)
    await download_new_tracks_from_playlist(user_id, group_id)


async def playlist_update_job(context):
    logger.info("Playlist update via JobQueue started")

    try:
        users = database.get_all_users()
        for user in users:
            for group in database.get_user_groups(user.id):
                try:
                    await create_or_update_playlist(user.id, group.id)
                    logger.info(
                        f"Updated playlist for user {user.id} in group {group.id}"
                    )
                except Exception as e:
                    logger.error(
                        f"Failed to update playlist for user {user.id} in group {group.id}: {e}"
                    )
    except Exception as e:
        logger.error(f"Error in playlist_update_job: {e}")
