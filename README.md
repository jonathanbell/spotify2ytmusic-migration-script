# Spotify to YouTube Music Migration Script

A script to migrate library and playlists from Spotify to YouTube Music.

## Prerequisites

- Python version 3.12.x (or a version _around_ that version number)

## Installation (local)

1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. The script relies wholly on [the `ytmusicapi` Python package](https://github.com/sigma67/ytmusicapi?tab=readme-ov-file). [We need to authenticate with YouTube Music](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html) in order for it to work. Run: `ytmusicapi oauth` (and follow the prompts in the CLI and browser)
1. If using `pyenv`, run `python3.11 ./src/main.py`. Otherwise run `python ./src/main.py`.
