# Spotify to YouTube Music Migration Script

A script to migrate library and playlists from Spotify to YouTube Music. This is meant to be paired with [jonathanbell/spotify_export](https://github.com/jonathanbell/spotify_export)

⚠️ This is a work in progress but feel free to use it if you want 🤙

![](https://miro.medium.com/v2/resize:fit:751/1*0zSv0aE2Whxf0ecf1PGRuw.jpeg)

## Prerequisites

- Python version 3.12.x (or a Python version _around_ 3.12)

## Installation (local)

1. `python3 -m venv venv`
1. `source venv/bin/activate`
1. `pip install -r requirements.txt`
1. The script relies wholly on [the `ytmusicapi` Python package](https://github.com/sigma67/ytmusicapi?tab=readme-ov-file). [We need to authenticate with YouTube Music](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html) in order for it to work. Run: `ytmusicapi oauth` (and follow the prompts in the CLI and browser)
1. If using `pyenv`, run `python3.11 ./src/main.py`. Otherwise run `python ./src/main.py`.

## TODOs

- [ ] Create documentation
