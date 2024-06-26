import argparse
from youtube_music import YoutubeMusic

ytmusic = YoutubeMusic()


def main():
    parser = argparse.ArgumentParser(
        description="Migrate your Spotify data to YouTube Music. Use https://github.com/jonathanbell/spotify_export to export your Spotify data and create your spotify_library.json file before using this script."
    )
    parser.add_argument(
        "--playlists",
        action="store_true",
        help="Import playlists from Spotify to YouTube Music. Requires the data/spotify_library.json file.",
    )
    parser.add_argument(
        "--lists",
        type=str,
        help="Specify a comma separated list of playlists to import. Must be used with --playlists.",
    )
    parser.add_argument(
        "--followed-artists",
        action="store_true",
        help="Import followed artists from Spotify to YouTube Music. Requires the data/spotify_library.json file.",
    )
    parser.add_argument(
        "--liked-songs",
        action="store_true",
        help="Import liked songs from Spotify to YouTube Music Liked Music. Requires the data/spotify_library.json file.",
    )
    parser.add_argument(
        "--saved-albums",
        action="store_true",
        help="Import saved albums from Spotify to YouTube Music. Requires the data/spotify_library.json file.",
    )
    parser.add_argument(
        "--spotify-playlists",
        action="store_true",
        help="List all importable Spotify playlists from the spotify_library.json file.",
    )
    parser.add_argument(
        "--slow-motion",
        action="store_true",
        help="Call the unofficial YouTube Music API in slow motion. Will likely help prevent your account from being banned.",
    )

    args = parser.parse_args()

    if args.spotify_playlists:
        ytmusic.list_importable_playlists()
    elif args.playlists:
        if args.lists:
            ytmusic.import_playlists(
                playlist_names=[playlist.strip() for playlist in args.lists.split(",")],
                slow=args.slow_motion,
            )
        else:
            ytmusic.import_playlists(playlist_names=None, slow=args.slow_motion)
    elif args.followed_artists:
        ytmusic.import_followed_artists(slow=args.slow_motion)
    elif args.liked_songs:
        ytmusic.import_liked_songs(slow=args.slow_motion)
    elif args.saved_albums:
        ytmusic.import_saved_albums(slow=args.slow_motion)
    else:
        print("No valid arguments provided. Use --help for more information.")


if __name__ == "__main__":
    main()
