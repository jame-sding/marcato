import datetime
import os
import traceback
import urllib.request
from http.client import HTTPResponse
from urllib.error import HTTPError

import moviepy.audio.io.AudioFileClip
import mutagen.id3
import pytube
import pytube.exceptions

import music_fetcher


def download_audio(youtube_url: str, directory: str, status_printer = print):
    """Downloads the audio from the YouTube URL at the given directory. Needs a print function."""
    if not os.path.exists(directory):
        print_error_with_func("Error: Directory doesn't exist", status_printer)
        return None

    final_file_location = None

    try:
        # Fetch the YouTube video.
        status_printer(f"Status: Finding YouTube video with url {youtube_url}")
        youtube_video = pytube.YouTube(youtube_url)

        # Get the video stream, and download the mp4. The mp4 is temporary.
        filename = make_filename_legal(youtube_video.title)
        status_printer(f"Status: Finding video stream for {youtube_video.title}")
        youtube_video_stream = youtube_video.streams.get_audio_only()
        status_printer(f"Status: Downloading {filename}.mp4")
        downloaded_mp4_location = youtube_video_stream.download(filename=filename)

        # Convert the mp4 into a mp3, and put the mp3 into the directory
        status_printer(f"Status: Converting to mp3")
        final_file_location = find_unique_file_location(filename, directory)
        convert_mp4_to_mp3(downloaded_mp4_location, final_file_location)

        # Remove the temporary mp4 file
        status_printer("Status: Removing temporary mp4 file")
        os.remove(downloaded_mp4_location)

    except pytube.exceptions.VideoUnavailable as e:
        print_error_with_func("Error: Video was not found or is unavailable", status_printer)
        log_error(e)
    except AttributeError as e:
        print_error_with_func(f"Error: Something internal went wrong", status_printer)
        log_error(e)
    except ValueError as e:
        # This exception can be thrown in the find_unique_file_location method
        # if the inputted file location wasn't valid
        print_error_with_func("Error: Invalid download location", status_printer)
        log_error(e)
    except Exception as e:
        print_error_with_func("Error: Something went wrong (perhaps a bad URL, or maybe wrong download setting?)",
                              status_printer)
        log_error(e)

    return final_file_location


def convert_mp4_to_mp3(mp4_location: str, mp3_location: str):
    """Converts the mp4 at the mp4 location to a mp3 that will be put in the mp3 location"""
    with moviepy.audio.io.AudioFileClip.AudioFileClip(filename=mp4_location) as mp4:
        # To prevent an exception from occurring when this program is executed as an exe file, we must prevent MoviePy
        # from attempting to log (there is no logger, and it'll throw an exception if it tries to log)
        mp4.write_audiofile(mp3_location, logger=None)


def set_mp3_tags(mp3_location: str, title: str = "", artists: list = None, album: str = "", album_art_url: str = "",
                 status_printer=print):
    """Sets the mp3 tags"""
    if artists is None:
        artists = []
    status_printer("Status: Adding ID3v2 tags to the mp3 file")
    audio_id3 = mutagen.id3.ID3(mp3_location)
    audio_id3.add(mutagen.id3.TIT2(encoding=3, text=title))
    audio_id3.add(mutagen.id3.TPE1(encoding=3, text=music_fetcher.artists_list_tostring(artists)))
    audio_id3.add(mutagen.id3.TALB(encoding=3, text=album))
    # If an album art URL wasn't given, then try to find one through Spotify.
    if album_art_url == "":
        if artists is not None:
            album_art_url = music_fetcher.get_album_art_url(album, artists[0])
    try:
        response: HTTPResponse = urllib.request.urlopen(album_art_url)
        audio_id3.add(mutagen.id3.APIC(encoding=3, mime="->", type=3, desc="Cover", data=response.read()))
    except HTTPError and ValueError as e:
        print_error_with_func("Error: Couldn't find album art URL (404 Not Found)", status_printer)
        log_error(e)
    audio_id3.save(v2_version=3)


def find_unique_file_location(file_name: str, file_directory: str, target_file_extension: str = "mp3"):
    """Adds the word \"Copy\" to the file name until the file name is unique in its parent directory"""
    unique_file_name: str = file_name
    while True:
        if os.path.exists(f"{file_directory}\\{unique_file_name}.{target_file_extension}"):
            unique_file_name += " Copy"
        else:
            return f"{file_directory}\\{unique_file_name}.{target_file_extension}"


def make_filename_legal(filename: str):
    """Removes characters that cannot be in file names on Windows"""
    return filename.replace("\\", '').replace("/", "").replace(":", "").replace("*", "").replace("?", "").replace("\"",
                                                                                                                  "") \
        .replace("<", "").replace(">", "").replace("|", "")


def print_error_with_func(message: str, func):
    if func.__name__ == "set_status_text":
        func(message, is_error=True)
    else:
        func(message)


def log_error(e: Exception):
    with open("marcato error log.log", "a") as file:
        file.write(f"{datetime.datetime.now()} {type(e)}\n{traceback.format_exc()}\n\n"
                   f"--------------------------------------------------------------------------------------------------"
                   f"---------------------------------------------------------------------------------------------\n\n")


if __name__ == "__main__":
    pass
