import json
import os
import sys
from ytmusicapi import YTMusic


class YoutubeMusic:
    def __init__(self):
        oauth_file_path = "oauth.json"
        if not os.path.exists(oauth_file_path):
            print(
                "The './oauth.json' file is missing. Please create it by running 'ytmusicapi oauth'."
            )
            sys.exit(1)
        spotify_library_path = "data/spotify_library.json"
        if not os.path.exists(spotify_library_path):
            print(
                "Error: 'spotify_library.json' file is missing in the data directory."
            )
            sys.exit(1)
        # Load the Spotify library JSON file to check for required keys
        with open(spotify_library_path, "r") as file:
            spotify_library = json.load(file)
        required_keys = ["followed_artists", "liked_songs", "playlists", "saved_albums"]
        missing_keys = [key for key in required_keys if key not in spotify_library]
        if missing_keys:
            print(
                f"Error: The following required keys are missing in 'spotify_library.json': {', '.join(missing_keys)}"
            )
            sys.exit(1)
        self.spotify_data = type("SpotifyData", (object,), spotify_library)
        self.ytmusicapi = YTMusic(oauth_file_path)

    def import_followed_artists(self):
        print("Importing followed artists...")
        if len(self.spotify_data.followed_artists) == 0:
            print("No followed artists to import.")
            return
        for artist in self.spotify_data.followed_artists:
            yt_candiates = self.ytmusicapi.search(
                query=artist["name"], filter="artists"
            )
            if len(yt_candiates) == 0:
                self._add_to_lost_and_found("artist", artist["name"])
                continue
            self.ytmusicapi.subscribe_artists([yt_candiates[0]["browseId"]])
            print(f"Subscribed to: {yt_candiates[0]['artist']}")

    def import_liked_songs(self):
        print("Importing liked songs...")
        if self.spotify_data.liked_songs[0]["track_count"] == 0:
            print("No liked songs to import.")
            return
        try:
            liked_songs_playlist_id = self.ytmusicapi.create_playlist(
                "Liked Songs", "Created by the Spotify to YTMusic Migration Script"
            )
        except Exception as e:
            print(f"Failed to create playlist: {e}")
            return
        video_ids = []
        print("Searching for liked songs...")
        counter = 1
        for song in self.spotify_data.liked_songs[0]["tracks"]:
            matched_yt_song = self._search_for_song(
                song["name"], song["artists"][0]["name"], song["album"]["name"]
            )
            if matched_yt_song:
                print(
                    f"Found on YT Music ({counter}/{len(self.spotify_data.liked_songs[0]['tracks'])}): {matched_yt_song['title']} - {matched_yt_song['artists'][0]['name']}"
                )
                video_ids.append(matched_yt_song["videoId"])
                if len(video_ids) >= 50:
                    print(
                        f"Adding the above {len(video_ids)} songs to Liked Songs playlist... 👆"
                    )
                    self.ytmusicapi.add_playlist_items(
                        liked_songs_playlist_id, video_ids
                    )
                    print("...✅")
                    video_ids = []
            else:
                self._add_to_lost_and_found(
                    "song", f"{song['name']} by {song['artists'][0]['name']}"
                )
            counter += 1
        if video_ids:
            self.ytmusicapi.add_playlist_items(liked_songs_playlist_id, video_ids)
        print(f"Added {len(video_ids)} songs to Liked Songs.")

    def import_playlists(self, playlist_name=None):
        print("Importing playlists...")
        if len(self.spotify_data.playlists) == 0:
            print("No playlists to import.")
            return
        if playlist_name:
            if playlist_name not in self.spotify_data.playlists:
                print(
                    f"🚨 Playlist '{playlist_name}' not found in spotify_library.json file."
                )
                return
            playlists = [
                playlist
                for playlist in self.spotify_data.playlists
                if playlist["name"] == playlist_name
            ]
        else:
            playlists = self.spotify_data.playlists
        for playlist in playlists:
            playlist_id = self.ytmusicapi.create_playlist(
                playlist["name"], "Created by the Spotify to YTMusic Migration Script"
            )
            print(f"📝 Created playlist: {playlist_id} - {playlist['name']}")
            video_ids = []
            print("Searching for playlist songs...")
            counter = 1
            for song in playlist["tracks"]:
                matched_yt_song = self._search_for_song(
                    song["name"], song["artists"][0]["name"], song["album"]["name"]
                )
                if matched_yt_song:
                    print(
                        f"Found on YT Music: {matched_yt_song['title']} - {matched_yt_song['artists'][0]['name']}"
                    )
                    video_ids.append(matched_yt_song["videoId"])
                    if len(video_ids) >= 50:
                        print(
                            f"Adding the above {len(video_ids)} songs to {playlist['name']} playlist... 👆"
                        )
                        self.ytmusicapi.add_playlist_items(playlist_id, video_ids)
                        print("...✅")
                        video_ids = []
                else:
                    self._add_to_lost_and_found(
                        "song", f"{song['name']} by {song['artists'][0]['name']}"
                    )
                counter += 1
            if video_ids:
                self.ytmusicapi.add_playlist_items(playlist_id, video_ids)
            print(
                f"Added {len(video_ids)} songs to {playlist['name']}."
            )  # todo: bug here?

    def import_saved_albums(self):
        print("Importing saved albums...")
        if len(self.spotify_data.saved_albums) == 0:
            print("No saved albums to import.")
            return
        for album in self.spotify_data.saved_albums:
            print(
                "Searching for: " + album["name"] + " by " + album["artists"][0]["name"]
            )
            yt_album_candidates = self.ytmusicapi.search(
                query=f'{album["name"]} by {album["artists"][0]["name"]}',
                filter="albums",
            )
            for yt_album_candidate in yt_album_candidates:
                new_playlist_id = None
                if yt_album_candidate["title"] == album["name"]:
                    new_playlist_id = self.ytmusicapi.create_playlist(
                        f'{yt_album_candidate["title"]} - {album["artists"][0]["name"]}',
                        "Created by the Spotify to YTMusic Migration Script",
                    )
                    print(
                        f'📝 Created playlist: {yt_album_candidate["title"]} - {album["artists"][0]["name"]}'
                    )
                    print("Searching for album songs...")
                    yt_album_details = self.ytmusicapi.get_album(
                        yt_album_candidate["browseId"]
                    )
                    for song in yt_album_details["tracks"]:
                        self.ytmusicapi.add_playlist_items(
                            new_playlist_id, [song["videoId"]]
                        )
                break
            if new_playlist_id:
                print(
                    f"Added {len(yt_album_details['tracks'])} songs to {yt_album_candidate['title']}."
                )
            else:
                self._add_to_lost_and_found(
                    "album", f"{album['name']} by {album['artists'][0]['name']}"
                )

    def list_importable_playlists(self):
        print("Importable playlists:")
        for playlist in self.spotify_data.playlists:
            print(playlist["name"])

    # inspo: https://github.com/linsomniac/spotify_to_ytmusic/blob/main/spotify2ytmusic/backend.py#L221
    def _search_for_song(self, track_name: str, artist_name: str, album_name: str):
        song = self.ytmusicapi.search(
            query=f"{track_name} by {artist_name}", filter="songs", limit=1
        )
        if song and len(song) > 0:
            return song[0]
        else:
            print("Performing deeper search...")
            song = self.ytmusicapi.search(
                query=f"{track_name} by {artist_name} on {album_name}",
                filter="songs",
                limit=1,
            )
            if song and len(song) > 0:
                print("Found song! 🙂")
                return song[0]
        self._add_to_lost_and_found("song", f"{track_name} by {artist_name}")
        return None

    def _add_to_lost_and_found(self, type, value):
        print(f"🤷 Could not find (adding to lost and found): {type} | {value}")
        lost_and_found_path = "data/lost_and_found.txt"
        with open(lost_and_found_path, "a") as file:
            file.write(f"{type} - {value}\n")
