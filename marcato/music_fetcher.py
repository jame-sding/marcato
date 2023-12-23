import datetime
import traceback

import googleapiclient.discovery
import pytube
import pytube.exceptions

from spotipy import Spotify, SpotifyClientCredentials, SpotifyException


# NOTE: THIS WILL ONLY WORK FOR A PUBLIC PLAYLIST OF MAX SIZE 100
def get_spotify_playlist_songs(playlist_url: str, status_printer=print):
    """Returns a list of dicts for each song in a PUBLIC, 100 SONG MAXIMUM Spotify playlist. Each dict contains
    the song title, artist(s), album, and album art URL"""
    try:
        status_printer("Status: Connecting to Spotify")
        auth_manager = SpotifyClientCredentials(client_id="1c41bf31426e46a6a4c44d3f9bac1424",
                                                client_secret="bb9d381f22204bdabbf0418767ca3aaf")
        spotify = Spotify(auth_manager=auth_manager)
        status_printer("Status: Fetching playlist")
        playlist = spotify.playlist(playlist_id=playlist_url, fields="tracks(items), name")
        status_printer(f"Status: Finding songs from Spotify playlist \"{playlist['name']}\"")
        playlist_items = playlist["tracks"]["items"]
        playlist_song_list = []
        for playlist_item in playlist_items:
            if playlist_item["is_local"]:
                continue  # Do not add local songs

            curr_item_dict = {}
            # Add the song title
            curr_item_dict.update({"title": playlist_item["track"]["name"]})
            status_printer(f"Status: Finding song from Spotify ({playlist_item['track']['name']})")
            # Add the artists
            artists_list = []
            for artist in playlist_item["track"]["artists"]:
                artists_list.append(artist["name"])
            curr_item_dict.update({"artists": artists_list})
            # Add the album
            curr_item_dict.update({"album": playlist_item["track"]["album"]["name"]})
            # Add the album art URL
            curr_item_dict.update({"album art url": playlist_item["track"]["album"]["images"][0]["url"]})

            # Add this dict to the song list
            playlist_song_list.append(curr_item_dict)
        return playlist_song_list

    except SpotifyException as e:
        print_error_with_func("Error: Couldn't fetch Spotify playlist (make sure that it's private AND NOT a single "
                              "song)", status_printer)
        log_error(e)


def get_youtube_playlist_songs_urls(playlist_url: str, status_printer=print):

    try:
        status_printer("Status: Connecting to YouTube")
        playlist = pytube.Playlist(playlist_url)
        if len(playlist) == 0:
            return None
        url_list = []
        status_printer(f"Status: Finding songs in YouTube playlist {playlist.title}")
        for url in playlist.video_urls:
            url_list.append(url)
        return url_list
    except KeyError:
        print_error_with_func("Error: Couldn't fetch YouTube playlist (make sure it isn't private AND NOT a single "
                              "song", status_printer)


def get_spotify_playlist_name(playlist_url: str, status_printer=print):
    try:
        status_printer("Status: Connecting to Spotify")
        auth_manager = SpotifyClientCredentials(client_id="1c41bf31426e46a6a4c44d3f9bac1424",
                                                client_secret="bb9d381f22204bdabbf0418767ca3aaf")
        spotify = Spotify(auth_manager=auth_manager)
        status_printer("Status: Fetching playlist name")
        playlist = spotify.playlist(playlist_id=playlist_url, fields="tracks(items), name")
        return playlist["name"]
    except SpotifyException as e:
        print_error_with_func("Error: Couldn't fetch Spotify playlist (make sure that it's public AND NOT a single "
                              "song)", status_printer)
        log_error(e)


def get_spotify_song_info(song_url: str, status_printer=print):
    try:
        status_printer("Status: Connecting to Spotify")
        auth_manager = SpotifyClientCredentials(client_id="1c41bf31426e46a6a4c44d3f9bac1424",
                                                client_secret="bb9d381f22204bdabbf0418767ca3aaf")
        spotify = Spotify(auth_manager=auth_manager)
        status_printer(f"Status: Fetching {song_url}")
        _song = spotify.track(track_id=song_url)
        status_printer(f"Status: Finding information from {song_url}")
        song_dict = {}
        song_dict.update({"title": _song["name"]})
        artists_list = []
        for artist in _song["artists"]:
            artists_list.append(artist["name"])
        song_dict.update({"artists": artists_list})
        song_dict.update({"album": _song["album"]["name"]})
        song_dict.update({"album art url": _song["album"]["images"][0]["url"]})
        return song_dict
    except SpotifyException as e:
        print_error_with_func("Error: Couldn't fetch Spotify song (maybe you sent a playlist?)", status_printer)
        log_error(e)


def video_is_accessible(youtube_vid_info: dict):
    return youtube_vid_info["playabilityStatus"]["status"] == "OK"


def get_video_candidate_score(candidate_title: str, candidate_channel: str, candidate_id: str, candidate_index: int,
                              target_title: str, target_artist: str):
    print(f"Current Info: {candidate_title} ; {candidate_channel} ; https://youtube.com/watch?v={candidate_id} ; {candidate_index}")
    print(f"Target Info: {target_title} ; {target_artist}")

    def title_contains_target(video_title: str, _target_title: str):
        """Accepts minor variations in the YouTube video title"""
        return _target_title.replace(" ", "").lower() in video_title.replace(" ", "").lower()

    def title_suggests_music_video_or_edit(video_title: str, target_song_title: str = ""):
        """MV as in music video"""
        blacklisted_words = ["musicvideo", "officialvideo", "MTV", "1hour", "MV", "edit", "live", "slowed",
                             "reverb", "spedup", "ver", "remix", "cover"]
        video_title_without_spaces = video_title.replace(" ", "")
        for blacklisted_word in blacklisted_words:
            if blacklisted_word.islower():
                if (blacklisted_word in video_title_without_spaces.lower()) and \
                        (blacklisted_word not in target_song_title.lower()):
                    return True
            else:
                if (blacklisted_word in video_title_without_spaces) and (blacklisted_word not in target_song_title):
                    return True
        return False

    def channel_title_contains_target(channel_name: str, target_name: str):
        """Accepts minor variations in the YouTube video title"""
        return target_name.replace(" ", "").lower() in channel_name

    def description_contains_youtube_autogen(video_id: str):
        """Find if the video description says \"Auto-generated by YouTube\""""
        api_key = "AIzaSyAD9nBmQAZQKCyhXLQIh1mXpOhuWoARQVM"
        youtube = googleapiclient.discovery.build(serviceName="youtube", version="v3", developerKey=api_key)
        video_search_request = youtube.videos().list(id=video_id, part="snippet")
        video_search_response = video_search_request.execute()
        desc = video_search_response["items"][0]["snippet"]["description"]
        return "auto-generatedbyyoutube" in desc.replace(" ", "").lower()

    video_score = 0
    # If the search result item's video title doesn't even have the song name in it, then deduct a point
    # Please note that if the inputted title is very long, then a point will be deducted. This is just
    # a flaw that I will have to deal with. Hopefully it won't be that big of a deal.
    if not title_contains_target(candidate_title, target_title):
        print("-2 for title not containing target")
        video_score = video_score - 2

    # If the search result is the first one, then add more points to this video's score
    if candidate_index == 0:
        print("+2 for candidate being first result")
        video_score = video_score + 2

    # If the search result is close to being the first, then add one point
    if 3 >= candidate_index > 0:
        print("+1 for candidate being close to first result")
        video_score = video_score + 1

    # If the search result item is far away from the first result, then deduct a point
    if candidate_index >= 9:
        print("-1 for candidate being far from first result")
        video_score = video_score - 1

    # If the video is a music video or an edit, then deduct points (music videos may contain extraneous sounds)
    if title_suggests_music_video_or_edit(candidate_title, target_title):
        print("-3 for implying music video or edit")
        video_score = video_score - 3

    # If the video title contains the word "audio" or "lyrics"
    if title_contains_target(candidate_title, "audio") or title_contains_target(candidate_title, "lyric video")\
            or title_contains_target(candidate_title, "visualizer") or title_contains_target(candidate_title, "lyrics"):
        if title_contains_target(candidate_title, target_title):
            print("+3 for both implying audio/lyrics only AND having the correct title")
            video_score = video_score + 3
        else:
            print("+2 for implying audio only or lyrics")
            video_score = video_score + 2

    # If the video title features artists that weren't featured in the target title
    # if title_contains_feats_extraneous_artists(candidate_title, target_title):
        # print("-2 for title featuring extra/lacking featured artists")
        # video_score = video_score - 2

    # Check if the YouTube channel has the artist name in it.
    if channel_title_contains_target(candidate_channel.replace(" ", "").lower(), target_artist):
        print("+1 for channel containing artist name")
        video_score = video_score + 1
        if description_contains_youtube_autogen(candidate_id):
            # If the artist name is in the channel title, and the desc has "Auto-generated by YouTube"
            print("+1 for implying auto-generated by YouTube")
            video_score = video_score + 1
            pass
    elif title_contains_target(candidate_title, target_artist):
        # If the YouTube channel does not have the artist name in it, but the video title does, then add a point
        print("+1 for title containing artist name")
        video_score = video_score + 1

    print(f"Total score: {video_score}\n")
    return video_score


def find_youtube_url(title: str, artists: list, status_printer=print, blacklist: list = None):
    """Uses Google's YouTube API to look for a video that pertains to the title and artists.
    This does not use PyTube because PyTube has a crappy search function."""

    def get_info_from_official_youtube_api_item(item: dict):
        return item["id"]["videoId"], item["snippet"]["title"], item["snippet"]["channelTitle"]

    def get_info_from_pytube_item(item: dict):
        return item["video_id"], item["video_title"], item["channel_title"]

    def search_with_official_youtube_api(query: str):
        api_key = "AIzaSyAD9nBmQAZQKCyhXLQIh1mXpOhuWoARQVM"
        youtube = googleapiclient.discovery.build(serviceName="youtube", version="v3", developerKey=api_key)
        search_request = youtube.search().list(
            part="snippet",
            maxResults=25,
            q=query,
            type="video"  # Only look for videos
        )
        try:
            return search_request.execute()["items"]
        except Exception as ex:
            log_error(ex)
            raise PermissionError("youtube quota")

    def search_with_pytube(query: str):
        search_results = pytube.Search(query).results
        items = []
        for search_result in search_results:
            curr_item_dict = {"video_id": search_result.video_id, "video_title": search_result.title,
                              "channel_title": search_result.author}
            items.append(curr_item_dict)
        return items

    # Connect to YouTube, and search YouTube for the title and the artist
    is_using_pytube = True
    search_result_items = []
    try:
        # raise Exception
        status_printer(f"Status: Connecting to YouTube, searching for {title} {artists_list_tostring(artists)}")
        search_result_items = search_with_pytube(f"{title} {artists_list_tostring(artists)}")
    except Exception as e:
        print_error_with_func(str(e.args), status_printer)
        log_error(e)
        is_using_pytube = False
        try:
            status_printer(f"Status: Reconnecting to YouTube, searching for {title}, "
                           f"by {artists_list_tostring(artists)}")
            search_result_items = search_with_official_youtube_api(f"{title} {artists_list_tostring(artists)}")
        except PermissionError as perm_error:
            if perm_error.args[0] == "youtube quota":
                print_error_with_func(
                    "Error: Daily quota for YouTube API reached. Please try again tomorrow, or contact me."
                    , status_printer)
                return None

    # Look for potential candidates for the video. A scoring system for each video will be used
    # 1. Candidates should preferably have the artist's name somewhere in the channel title (+1 score)
    #   1a. Even more preferably should have "Auto-generated by YouTube" in the desc
    # 2. If the result is the first one, that should also be a good sign. (+1 score)
    status_printer("Status: Finding video candidates")
    video_candidates = []
    for search_result_item in search_result_items:
        # Get the search result item's information
        if is_using_pytube:
            curr_video_id, curr_video_title, curr_channel = get_info_from_pytube_item(search_result_item)
        else:
            curr_video_id, curr_video_title, curr_channel = get_info_from_official_youtube_api_item(search_result_item)
        if blacklist is not None and f"https://www.youtube.com/watch?v={curr_video_id}" in blacklist:
            break
        # Calculate the item's score and append to the list
        curr_video_score = get_video_candidate_score(curr_video_title, curr_channel, curr_video_id,
                                                     search_result_items.index(search_result_item), title, artists[0])
        video_candidates.append({"url": f"https://www.youtube.com/watch?v={curr_video_id}", "score": curr_video_score})

    # Find the URL of the highest scoring video
    status_printer("Status: Calculating best candidate")
    best_url = ""
    largest_score = -1
    for video_candidate in video_candidates:
        # print(f"{video_candidate['url']} {video_candidate['score']}")
        if video_candidate["score"] > largest_score:
            best_url = video_candidate["url"]
            largest_score = video_candidate["score"]

    return best_url


def artists_list_tostring(artists: list):
    artists_names_str = ""
    for artist in artists:
        artists_names_str += f"{artist}, "
    return artists_names_str[:-2]


def print_error_with_func(message: str, func):
    if func.__name__ == "set_status_text":
        func(message, is_error=True)
    else:
        func(message)


def get_album_art_url(album_title: str, album_lead_artist: str = ""):
    """Returns only the album art URL, given the album title and album's lead artist"""
    auth_manager = SpotifyClientCredentials(client_id="1c41bf31426e46a6a4c44d3f9bac1424",
                                            client_secret="bb9d381f22204bdabbf0418767ca3aaf")
    spotify = Spotify(auth_manager=auth_manager)
    album_results = spotify.search(q=f"{album_title} {album_lead_artist}", type="album")
    return album_results["albums"]["items"][0]["images"][0]["url"]


def get_album_from_song(title: str, artists: list):
    """Returns information about the album that the given song is in (a tuple of its title and then its art URL)"""
    auth_manager = SpotifyClientCredentials(client_id="1c41bf31426e46a6a4c44d3f9bac1424",
                                            client_secret="bb9d381f22204bdabbf0418767ca3aaf")
    spotify = Spotify(auth_manager=auth_manager)
    print(f"{title} {artists_list_tostring(artists)}")
    song_results = spotify.search(q=f"{title} {artists_list_tostring(artists)}", type="track")
    for song_result in song_results["tracks"]["items"]:
        print(f"{song_result['album']['name']} {song_result['artists'][0]['name']}")
    return (song_results["tracks"]["items"][0]["album"]["name"]), \
        (song_results["tracks"]["items"][0]["album"]["images"][0]["url"])


def get_youtube_video_information(url: str, status_printer=print):
    try:
        video = pytube.YouTube(url=url)
        return video.title, video.author
    except pytube.exceptions.VideoUnavailable as e:
        print_error_with_func("Error: Video was not found or is unavailable", status_printer)
        log_error(e)
        return None


def log_error(e: Exception):
    with open("marcato errors.log", "a") as file:
        file.write(f"{datetime.datetime.now()} {type(e)}\n{traceback.format_exc()}\n\n"
                   f"--------------------------------------------------------------------------------------------------"
                   f"---------------------------------------------------------------------------------------------\n\n")


if __name__ == "__main__":
    print(find_youtube_url("Limbo - Ghost Slowed", ["Freddie Dredd", "OG Ron C"]))
    print(find_youtube_url("Contact (feat. Tyga)", ["Wiz Khalifa", "Tyga"]))
    # print(title_contains_feats_extraneous_artists("Doja Cat - Kiss Me More (Official Video) ft. SZA", "Kiss Me More (feat. SZA) Doja Cat"))

    # print(get_album_from_song("Butter", ["BTS"]))
