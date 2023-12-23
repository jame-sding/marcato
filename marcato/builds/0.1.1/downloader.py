import os

import moviepy.audio.io.AudioFileClip
import mutagen.easyid3
import pytube
import pytube.exceptions


def download_audio(youtube_url: str, directory: str, print_status):
    """Downloads the audio from the YouTube URL at the given directory. Needs a print function."""
    print(directory)

    if not os.path.exists(directory):
        print_status("Error: Directory doesn't exist", is_error=True)
        return None

    final_file_location = None

    try:
        # Fetch the YouTube video.
        print_status("Status: Finding YouTube Video")
        youtube_video = pytube.YouTube(youtube_url)

        # Get the video stream, and download the mp4. The mp4 is temporary.
        filename = make_filename_legal(youtube_video.title)
        print_status("Status: Finding video stream")
        youtube_video_stream = youtube_video.streams.get_audio_only()
        print_status(f"Status: Downloading {filename}.mp4")
        downloaded_mp4_location = youtube_video_stream.download(filename=filename)

        # Convert the mp4 into a mp3, and put the mp3 into the directory
        print_status(f"Status: Converting to mp3")
        final_file_location = find_unique_file_location(filename, directory)
        convert_mp4_to_mp3(downloaded_mp4_location, final_file_location)

        # Remove the temporary mp4 file
        print_status("Status: Removing temporary mp4 file")
        os.remove(downloaded_mp4_location)

    except pytube.exceptions.VideoUnavailable:
        print_status("Error: Video was not found or is unavailable", is_error=True)
        pass
    except AttributeError as e:
        print_status(f"Error: Something internal went wrong (DEBUG: {e})", is_error=True)
        pass
    except ValueError:
        # This exception can be thrown in the find_unique_file_location method
        # if the inputted file location wasn't valid
        print_status("Error: Invalid download location", is_error=True)
        pass
    except:
        print_status("Error: Something went wrong (perhaps a bad YouTube URL?)", is_error=True)

    return final_file_location


def convert_mp4_to_mp3(mp4_location: str, mp3_location: str):
    """Converts a mp4 at the mp4 location to an mp3 that will be put in the mp3 location"""
    print("MP3 LOCATION:" + mp3_location)
    with moviepy.audio.io.AudioFileClip.AudioFileClip(filename=mp4_location) as mp4:
        # To prevent an exception from occurring when this program is executed as an exe file, we must prevent MoviePy
        # from attempting to log (there is no logger, and it'll throw an exception if it tries to log)
        mp4.write_audiofile(mp3_location, logger=None)


def set_mp3_tags(mp3_location: str, title: str = "", artist: str = "", album: str = ""):
    """Sets the mp3 tags"""
    print(f"MP3 LOCATION: {mp3_location}")
    audio = mutagen.easyid3.EasyID3(mp3_location)
    audio["title"] = title
    audio["artist"] = artist
    audio["album"] = album
    audio.save()


def find_unique_file_location(file_name: str, file_location: str, target_file_extension: str = "mp3"):
    """Adds the word \"Copy\" to the file name until the file name is unique in its parent directory"""
    last_backslash_index = file_location.rindex("\\")
    file_parent_directory = file_location[:last_backslash_index + 1]
    unique_file_name: str = file_name

    while True:
        if os.path.exists(f"{file_parent_directory}{unique_file_name}.{target_file_extension}"):
            unique_file_name += " Copy"
        else:
            return f"{file_parent_directory}{unique_file_name}.{target_file_extension}"


def make_filename_legal(filename: str):
    """Removes characters that cannot be in file names on Windows"""
    return filename.replace("\\", '').replace("/", "").replace(":", "").replace("*", "").replace("?", "").replace("\"", "")\
        .replace("<", "").replace(">", "").replace("|", "")


# update_mp3_tags(download_audio("https://www.youtube.com/watch?v=dQw4w9WgXcQ"), "Never Gonna Give You Up",
# "Rick Astley", "Whenever You Need Somebody")

if __name__ == "__main__":
    download_audio("https://music.youtube.com/watch?v=ApXoWvfEYVU", os.getcwd(), print)

