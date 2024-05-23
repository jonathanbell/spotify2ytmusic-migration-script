# Spotify to YouTube Music Migration Script

So.. You want to give your money to one of the largest corporations in the world instead of the little 2006 Swedish company that could (_"I think I can.. I think I can.."_) OK, well, here is a way for you to import your Spotify library into YouTube Music, you filthy animal.

Ugh.. I can't even believe I'm helping you do this. The only reason I made this script was to swap my subscription over to YT Music from Spotify "seamlessly". I feel like the pond scum of the Earth for doing so. I'm sorry, Daniel.

First of all, you need to export your Spotify library into a format that this script will understand. Probably, the easiest way for you to do that is to use [this tool](https://github.com/jonathanbell/spotify_export) that I also wrote. The migration script in this repo is designed to be used with the JSON output produced by this [Spotify Export tool](https://github.com/jonathanbell/spotify_export).

Simply, [download a binary that matches your system](https://github.com/jonathanbell/spotify_export/releases) (Win/Mac/Linux) and run it. If you are on a Mac, you'll have to make the binary executable: `chmod +x /path/to/spotify_export-mac64 && ./path/to/spotify_export-mac64`. After authenticating via Spotify a `spotify_library.json` file will be placed onto your Desktop. _Use this file with this Python script_, provided here (in this repo).

This script depends _heavily_ on [the `ytmusicapi` package](https://github.com/sigma67/ytmusicapi). Since that package is written in fucking Python, so is this script.

⚠️ This is still a work in progress and contributions are welcome. It works on my machine and I imported my Spotify library to YouTube Music without too much headache. Have fun.

!["I want you to develop free software (for me)"](https://miro.medium.com/v2/resize:fit:751/1*0zSv0aE2Whxf0ecf1PGRuw.jpeg)

## Prerequisites

- Python version 3.12.x (it's probably easiest to use a Python virtual environment - see below)
- `pip`

## Installation

1. Clone/download this repo and `cd` into its directory
1. `python3 -m venv venv` (_or_ `python -m venv venv` if `python` already points to version 3 on your system)
1. `source venv/bin/activate` will activate the virtual environment (if you're into that kind of thing)
1. `pip install -r requirements.txt`
1. The script has a major dependency on [the `ytmusicapi` Python package](https://github.com/sigma67/ytmusicapi?tab=readme-ov-file). So before running any import commands, we need to [authenticate with the YouTube Music API](https://ytmusicapi.readthedocs.io/en/stable/setup/oauth.html) in order for it to work. Run: `ytmusicapi oauth` (and follow the prompts in the CLI and browser)
1. If using `pyenv`, run `python3.11 ./src/main.py --help`. Otherwise run `python3 ./src/main.py --help` or `python ./src/main.py --help` (if you have `python` setup to run as Python version 3 on your system). This command will list all of the available options/functionality associated with the script.

## Usage

Place your `spotify_library.json` file in the `data` directory (eg. `data/spotify_library.json`) before running any of the commands.

If a song, artist, etc. cannot be found by the script while searching YT Music, the item will end up in the `lost_and_found.txt` file here: `data/lost_and_found.txt`. You can think of this file as a log of items that was not added to YT Music for whatever reason.

The output of `--help` should be clear enough but I'll list a few examples here.

### Playlists

`--spotify-playlists` List all of the available playlists to import (via the `spotify_library.json` file)

`./src/main.py --playlists` will import all of your Spotify playlists into YouTube Music.

For a more fine-grained/surgical approach, you can pass the names of which playlists to import via the `--lists` property. Separate the names of the playlists with a comma.

Example: `./src/main.py --playlists --lists='lofi beats, Your Top Songs 2023'`

### Followed artists

`--followed-artists` will import your existing flowed artists from Spotify into YT Music and "subscribe" you to each artist.

Example: `python3.11 ./src/main.py --followed-artists`

### Liked songs

`--liked-songs` will import all of your Spotify Liked Songs into YT Music's "Liked Music" list.

Example: `python3.11 ./src/main.py --liked-songs`

### Saved albums

`--saved-albums` creates new playlists with the artist and album name. Adds the tracks that are on the album to the playlist.

Example: `python3.11 ./src/main.py --saved-albums`

## Errors do be like that

It would seem that unofficial, designed-for-browser YT Music API doesn't take kindly to overuse. I've encountered the error below more than once. Basically, just do what it says; _wait a little while and try again_.

```plaintext
Exception: Server returned HTTP 400: Bad Request.
You are creating too many playlists. Please wait a while before creating further playlists.
```
