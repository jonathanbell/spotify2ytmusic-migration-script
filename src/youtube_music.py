import json
import os
import random
import sys
import time
from ytmusicapi import YTMusic


class YoutubeMusic:
    def __init__(self, max_retries=3, initial_delay=60):
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
        try:
            with open(spotify_library_path, "r") as file:
                spotify_library = json.load(file)
        except json.JSONDecodeError:
            print("Error: 'spotify_library.json' is not a valid JSON file.")
            sys.exit(1)
        required_keys = ["followed_artists", "liked_songs", "playlists", "saved_albums"]
        missing_keys = [key for key in required_keys if key not in spotify_library]
        if missing_keys:
            print(
                f"Error: The following required keys are missing in 'spotify_library.json': {', '.join(missing_keys)}"
            )
            sys.exit(1)
        self.spotify_data = type("SpotifyData", (object,), spotify_library)
        try:
            self.ytmusicapi = YTMusic(oauth_file_path)
        except Exception as e:
            print(f"Error initializing YTMusic: {str(e)}")
            sys.exit(1)
        self.max_retries = max_retries
        self.initial_delay = initial_delay

    def import_followed_artists(self, slow=False):
        print("Importing followed artists...")
        if len(self.spotify_data.followed_artists) == 0:
            print("No followed artists to import.")
            return
        for artist in self.spotify_data.followed_artists:
            try:
                yt_candidates = self.ytmusicapi.search(
                    query=artist["name"], filter="artists"
                )
                if len(yt_candidates) == 0:
                    self._add_to_lost_and_found("artist", artist["name"])
                    continue
                self.ytmusicapi.subscribe_artists([yt_candidates[0]["browseId"]])
                print(f"Subscribed to: {yt_candidates[0]['artist']}")
                if slow:
                    print("🐢 Slow motion enabled. Sleeping for 1-3 seconds.")
                    time.sleep(random.uniform(1, 3))
            except Exception as e:
                print(f"Error processing artist {artist['name']}: {str(e)}")
                continue

    def import_liked_songs(self, slow=False):
        print("Importing liked songs to Liked Music...")
        if self.spotify_data.liked_songs[0]["track_count"] == 0:
            print("No liked songs to import.")
            return
        print("Searching for liked songs...")
        counter = 1
        for song in reversed(self.spotify_data.liked_songs[0]["tracks"]):
            try:
                matched_yt_song = self._search_for_song(
                    song["name"], song["artists"][0]["name"], song["album"]["name"]
                )
                if slow:
                    print("🐢 Slow motion enabled. Sleeping for 1 second.")
                    time.sleep(1)
                if matched_yt_song:
                    artist_name = matched_yt_song['artists'][0]['name'] if matched_yt_song.get('artists') else 'Unknown Artist'
                    print(
                        f"Found on YT Music ({counter}/{len(self.spotify_data.liked_songs[0]['tracks'])}): {matched_yt_song['title']} - {artist_name}"
                    )
                    self.ytmusicapi.rate_song(matched_yt_song["videoId"], "LIKE")
                    print("...Liked 👍")
                    if slow:
                        print("🐢 Slow motion enabled. Sleeping for 1-3 seconds.")
                        time.sleep(random.uniform(1, 3))
                else:
                    self._add_to_lost_and_found(
                        "song", f"{song['name']} by {song['artists'][0]['name']}"
                    )
            except Exception as e:
                print(f"Error processing song {song.get('name', 'Unknown')}: {str(e)}")
                continue
            counter += 1
        print(f"Added {counter - 1} songs to Liked Music.")

    def import_playlists(self, playlist_names=None, slow=False):
        max_batch_size = 50
        print("Importing playlists...")
        if len(self.spotify_data.playlists) == 0:
            print("No playlists to import.")
            return
        if playlist_names:
            playlists = [playlist for playlist in self.spotify_data.playlists if playlist["name"] in playlist_names]
            if not playlists:
                print(f"🚨 No matching playlists found in spotify_library.json file.")
                return
        else:
            playlists = self.spotify_data.playlists

        for playlist in playlists:
            playlist_id = None
            retry_count = 0
            delay = self.initial_delay
            while retry_count <= self.max_retries:
                try:
                    # Check if playlist already exists
                    existing_playlists = self.ytmusicapi.get_library_playlists(limit=None)
                    existing_playlist = next((p for p in existing_playlists if p['title'] == playlist["name"]), None)
                    if existing_playlist:
                        print(f"Playlist '{playlist['name']}' already exists. Using existing playlist.")
                        playlist_id = existing_playlist['playlistId']
                        break

                    playlist_id = self.ytmusicapi.create_playlist(
                        playlist["name"], "Created by the Spotify to YTMusic Migration Script"
                    )
                    print(f"📝 Created playlist: {playlist_id} - {playlist['name']}")
                    
                    # If successful, break the retry loop
                    break
                except Exception as e:
                    if "You are creating too many playlists" in str(e) or "Server returned HTTP 400" in str(e):
                        retry_count += 1
                        if retry_count > self.max_retries:
                            print(f"Failed to create playlist '{playlist['name']}' after {self.max_retries} retries. Skipping.")
                            break
                        print(f"Rate limit reached. Retrying in {delay} seconds... (Attempt {retry_count}/{self.max_retries})")
                        time.sleep(delay)
                        delay *= 2  # Exponential backoff
                    else:
                        print(f"Error creating playlist '{playlist['name']}': {str(e)}")
                        break

            if playlist_id is None:
                print(f"Skipping song addition for playlist '{playlist['name']}' due to creation failure.")
                continue

            if slow:
                print("🐢 Slow motion enabled. Sleeping for 1-3 seconds.")
                time.sleep(random.uniform(1, 3))

            video_ids = []
            added_songs_counter = 0
            print(f"Searching for playlist songs... (Total: {len(playlist['tracks'])})")
            for song in playlist["tracks"]:
                if not song.get("artists"):
                    print(f"Skipping song without artist information: {song.get('name', 'Unknown')}")
                    continue
                try:
                    matched_yt_song = self._search_for_song(
                        song["name"], song["artists"][0]["name"], song.get("album", {}).get("name", "")
                    )
                    if slow:
                        print("🐢 Slow motion enabled. Sleeping for 1 second.")
                        time.sleep(1)
                    if matched_yt_song:
                        artist_name = matched_yt_song['artists'][0]['name'] if matched_yt_song.get('artists') else 'Unknown Artist'
                        print(f"Found on YT Music: {matched_yt_song['title']} - {artist_name}")
                        video_ids.append(matched_yt_song["videoId"])
                        added_songs_counter += 1
                        if len(video_ids) >= max_batch_size:
                            self._add_songs_to_playlist(playlist_id, video_ids, playlist['name'], slow)
                            video_ids = []
                    else:
                        self._add_to_lost_and_found(
                            "song", f"{song['name']} by {song['artists'][0]['name']}"
                        )
                except Exception as e:
                    print(f"Error processing song: {song.get('name', 'Unknown')} - {str(e)}")
                    continue
            if video_ids:
                self._add_songs_to_playlist(playlist_id, video_ids, playlist['name'], slow)
            
            # Check if all songs were added
            yt_playlist = self.ytmusicapi.get_playlist(playlist_id)
            yt_song_count = yt_playlist['trackCount']
            spotify_song_count = len(playlist['tracks'])
            print(f"Added {added_songs_counter} songs to {playlist['name']}.")
            print(f"YouTube Music playlist has {yt_song_count} songs, Spotify playlist had {spotify_song_count} songs.")
            if yt_song_count < spotify_song_count:
                print(f"⚠️ Warning: {spotify_song_count - yt_song_count} songs could not be added to the YouTube Music playlist.")

    def import_saved_albums(self, slow=False):
        print("Importing saved albums...")
        if len(self.spotify_data.saved_albums) == 0:
            print("No saved albums to import.")
            return
        for album in self.spotify_data.saved_albums:
            try:
                print(
                    "Searching for: " + album["name"] + " by " + album["artists"][0]["name"]
                )
                yt_album_candidates = self.ytmusicapi.search(
                    query=f'{album["name"]} by {album["artists"][0]["name"]}',
                    filter="albums",
                )
                if slow:
                    print("🐢 Slow motion enabled. Sleeping for 1 second.")
                    time.sleep(1)
                found = False
                for yt_album_candidate in yt_album_candidates:
                    if not yt_album_candidate.get("playlistId"):
                        print(
                            "🚨 No playlist ID found in data returned from search! Cannot add an album to library without a valid playlist ID for a given album."
                        )
                        continue
                    if yt_album_candidate["title"] == album["name"]:
                        print(yt_album_candidate)
                        self.ytmusicapi.rate_playlist(
                            yt_album_candidate["playlistId"], "LIKE"
                        )
                        print(
                            f'💿 Added album: {yt_album_candidate["title"]} - {album["artists"][0]["name"]}'
                        )
                        found = True
                        if slow:
                            print("🐢 Slow motion enabled. Sleeping for 1-3 seconds.")
                            time.sleep(random.uniform(1, 3))
                        break
                if not found:
                    self._add_to_lost_and_found(
                        "album", f"{album['name']} by {album['artists'][0]['name']}"
                    )
            except Exception as e:
                print(f"Error processing album {album.get('name', 'Unknown')}: {str(e)}")
                continue

    def list_importable_playlists(self):
        print("Importable playlists:")
        for playlist in self.spotify_data.playlists:
            print(playlist["name"])

    def _search_for_song(self, track_name: str, artist_name: str, album_name: str):
        try:
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
        except Exception as e:
            print(f"Error searching for song {track_name}: {str(e)}")
            return None

    def _add_songs_to_playlist(self, playlist_id, video_ids, playlist_name, slow):
        print(f"Adding {len(video_ids)} songs to {playlist_name} playlist... 👆")
        try:
            result = self.ytmusicapi.add_playlist_items(playlist_id, video_ids, None, True)
            if result["status"] == "STATUS_SUCCEEDED":
                print("...✅")
                if slow:
                    print("🐢 Slow motion enabled. Sleeping for 1-3 seconds.")
                    time.sleep(random.uniform(1, 3))
            else:
                print(f"❌ Error while adding songs to playlist ({playlist_name}): {result['status']}")
                if 'actions' in result and result['actions']:
                    print(result["actions"][0]["confirmDialogEndpoint"]["content"]["confirmDialogRenderer"]["dialogMessages"][0]["runs"][0]["text"])
        except Exception as e:
            print(f"Error adding songs to playlist {playlist_name}: {str(e)}")

    def _add_to_lost_and_found(self, type, value):
        print(f"🤷 Could not find (adding to lost and found): {type} | {value}")
        lost_and_found_path = "data/lost_and_found.txt"
        try:
            with open(lost_and_found_path, "a") as file:
                file.write(f"{type} - {value}\n")
        except IOError as e:
            print(f"Error writing to lost and found file: {str(e)}")