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
        print("Importing liked songs to Liked Music...")
        if self.spotify_data.liked_songs[0]["track_count"] == 0:
            print("No liked songs to import.")
            return
        print("Searching for liked songs...")
        counter = 1
        for song in reversed(self.spotify_data.liked_songs[0]["tracks"]):
            matched_yt_song = self._search_for_song(
                song["name"], song["artists"][0]["name"], song["album"]["name"]
            )
            if matched_yt_song:
                print(
                    f"Found on YT Music ({counter}/{len(self.spotify_data.liked_songs[0]['tracks'])}): {matched_yt_song['title']} - {matched_yt_song['artists'][0]['name']}"
                )
                self.ytmusicapi.rate_song(matched_yt_song["videoId"], "LIKE")
                print("...Liked 👍")
            else:
                self._add_to_lost_and_found(
                    "song", f"{song['name']} by {song['artists'][0]['name']}"
                )
            counter += 1
        print(f"Added {counter} songs to Liked Music.")

    def import_playlists(self, playlist_names=None):
        max_batch_size = 50
        print("Importing playlists...")
        if len(self.spotify_data.playlists) == 0:
            print("No playlists to import.")
            return
        if playlist_names:
            playlists = []
            for name in playlist_names:
                matched_playlists = [
                    playlist
                    for playlist in self.spotify_data.playlists
                    if playlist["name"] == name
                ]
                if not matched_playlists:
                    print(f"🚨 '{name}' was not found in spotify_library.json file.")
                    sys.exit(1)
                playlists.extend(matched_playlists)
        else:
            playlists = self.spotify_data.playlists
        for playlist in playlists:
            playlist_id = self.ytmusicapi.create_playlist(
                playlist["name"], "Created by the Spotify to YTMusic Migration Script"
            )
            print(f"📝 Created playlist: {playlist_id} - {playlist['name']}")
            video_ids = []
            added_songs_counter = 0
            print("Searching for playlist songs...")
            for song in playlist["tracks"]:
                if song["artists"] is None:
                    continue
                matched_yt_song = self._search_for_song(
                    song["name"], song["artists"][0]["name"], song["album"]["name"]
                )
                if matched_yt_song:
                    print(
                        f"Found on YT Music: {matched_yt_song['title']} - {matched_yt_song['artists'][0]['name']}"
                    )
                    video_ids.append(matched_yt_song["videoId"])
                    added_songs_counter += 1
                    if len(video_ids) >= max_batch_size:
                        print(
                            f"Adding the above {len(video_ids)} songs to {playlist['name']} playlist... 👆"
                        )
                        result = self.ytmusicapi.add_playlist_items(
                            playlist_id, video_ids, None, True
                        )
                        if result["status"] == "STATUS_SUCCEEDED":
                            print("...✅")
                        else:
                            print(
                                "❌ Error while adding songs to playlist("
                                + playlist["name"]
                                + "): "
                                + result["status"]
                            )
                            sys.exit(1)
                        video_ids = []
                else:
                    self._add_to_lost_and_found(
                        "song", f"{song['name']} by {song['artists'][0]['name']}"
                    )
            if len(video_ids) > 0:
                print(
                    f"Adding the above {len(video_ids)} songs to {playlist['name']} playlist... 👆"
                )
                result = self.ytmusicapi.add_playlist_items(
                    playlist_id, video_ids, None, True
                )
                if result["status"] == "STATUS_SUCCEEDED":
                    print("...✅")
                else:
                    print(
                        "❌ Error while adding songs to playlist ("
                        + playlist["name"]
                        + "): "
                        + result["status"]
                    )
                    print(
                        result["actions"][0]["confirmDialogEndpoint"]["content"][
                            "confirmDialogRenderer"
                        ]["dialogMessages"][0]["runs"][0]["text"]
                    )
                    sys.exit(1)
            print(f"Added {added_songs_counter} songs to {playlist['name']}.")

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
            found = False
            for yt_album_candidate in yt_album_candidates:
                if not yt_album_candidate["playlistId"]:
                    print(
                        "🚨 No playlist ID found in data returned from search! Cannot add and album to library without a valid playlist ID for a given album."
                    )
                    sys.exit(1)
                if yt_album_candidate["title"] == album["name"]:
                    print(yt_album_candidate)
                    self.ytmusicapi.rate_playlist(
                        yt_album_candidate["playlistId"], "LIKE"
                    )
                    print(
                        f'💿 Added album: {yt_album_candidate["title"]} - {album["artists"][0]["name"]}'
                    )
                    found = True
                    break
            if not found:
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
                print("Found song! 🙂 (" + song[0]["title"] + ")")
                return song[0]
        self._add_to_lost_and_found("song", f"{track_name} by {artist_name}")
        return None

    def _add_to_lost_and_found(self, type, value):
        print(f"🤷 Could not find (adding to lost and found): {type} | {value}")
        lost_and_found_path = "data/lost_and_found.txt"
        with open(lost_and_found_path, "a") as file:
            file.write(f"{type} - {value}\n")
