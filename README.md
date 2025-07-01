[//]: # (Project readme template from https://github.com/othneildrew/Best-README-Template/)
<a name="readme-top"></a>

[![MIT License](https://img.shields.io/badge/License-MIT-green.svg )](https://choosealicense.com/licenses/mit/ )
[![Code Style: Black](https://img.shields.io/badge/code%20style-black-000000.svg )](https://github.com/psf/black )
[![Lint: Pylint](https://img.shields.io/badge/lint-pylint-yellow )](https://pypi.org/project/pylint/ )

<h1 align="left">SoundBridge</h1>

## Description

A Telegram bot that allows you to share your favorite tracks and albums from [`Yandex Music`](https://music.yandex.ru/?) with your friends in a few clicks, discuss them, and create a shared playlist.

The bot's interaction with Yandex Music is based on the library [`yandex-music-api`](https://github.com/MarshalX/yandex-music-api).

## Features

- **Track Sharing**: Share your emotions about tracks and albums from Yandex Music in groups.
- **Shared Playlists**: Automatically sync music in your Yandex Music group playlist.
- **Ratings**: Rate tracks and view average ratings.
- **Music Sharing History**: View your or a group's history.

## Prerequisites

- Python 3.10+
- Yandex account to receive a token (preferably with a "Plus" subscription)
- Create a `.env` file in the project root and put the telegram bot `API Token` there:
```
TOKEN = <API Token>
```

## Installation

1. Create and activate Python virtual environment:
```bash
python -m venv env
source env/bin/activate
```

2. Install required dependencies:
```bash
pip install -r requirements.txt
```

3. Run the bot:
```bash
python3 -m bot.main
```

## License

Distributed under the [MIT License](https://choosealicense.com/licenses/mit/). See [`LICENSE`](LICENSE) for more
information.
