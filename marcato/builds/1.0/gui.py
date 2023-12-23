import os
import threading
import tkinter
from tkinter import *

import downloader
import music_fetcher


# Copied from https://www.reddit.com/r/learnpython/comments/k5lgyd/tkinter_how_do_i_make_ctrlbackspace_work_like/
class BetterEntry(tkinter.Entry):
    """This class supports control-backspace deletion of an entire word"""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Control-BackSpace>', self.delete_proceeding_word)

    def delete_proceeding_word(self, event):
        blinker_index = self.index(tkinter.INSERT)
        deletion_begin_index = self.get().rfind(" ", None, blinker_index)
        self.selection_range(deletion_begin_index, blinker_index)


def download_action():
    """Starts a thread that tries to find and download the mp3 that the user requested through the inputs."""

    def download_playlist():
        disable_gui()

        if link_entry.get().find("spotify.com") != -1:
            song_list = music_fetcher.get_spotify_playlist_songs(link_entry.get(), status_printer=set_status_text)
            if song_list is None:
                enable_gui("playlist")
                return
            for song in song_list:
                url = music_fetcher.find_youtube_url(song["title"], song["artists"], status_printer=set_status_text)
                if url is None:
                    break
                downloaded_mp3_location = downloader.download_audio(url, download_location_entry.get(), set_status_text)
                if downloaded_mp3_location is not None:
                    downloader.set_mp3_tags(downloaded_mp3_location, song["title"], song["artists"], song["album"],
                                            song["album art url"], status_printer=set_status_text)
        elif link_entry.get().find("youtube.com") != -1:
            song_url_list = music_fetcher.get_youtube_playlist_songs_urls(link_entry.get(),
                                                                          status_printer=set_status_text)
            for song_url in song_url_list:
                downloaded_mp3_location = downloader.download_audio(song_url, download_location_entry.get(),
                                                                    set_status_text)
                if downloaded_mp3_location is not None:
                    title, artists = music_fetcher.get_youtube_video_information(song_url, set_status_text)
                    album, album_art_url = music_fetcher.get_album_from_song(title, artists)
                    downloader.set_mp3_tags(downloaded_mp3_location, title, [artists], album,
                                            album_art_url, status_printer=set_status_text)

        set_status_text("Status: Idle")
        enable_gui("playlist")

    def download_song():
        disable_gui()

        # Get the user's inputted information
        title_tag = song_title_entry.get()
        artists_tag = song_artist_entry.get()
        album_tag = song_artist_entry.get()

        if link_entry.get().find("spotify.com") != -1:
            # Download the song using the Spotify link
            song_info = music_fetcher.get_spotify_song_info(song_url=link_entry.get(), status_printer=set_status_text)
            downloaded_mp3_location = downloader.download_audio(
                music_fetcher.find_youtube_url(song_info["title"], song_info["artists"]),
                download_location_entry.get(),
                set_status_text)
            # Replace the fields that the user didn't input anything in with the data that the program found
            if title_tag == "":
                title_tag = song_info["title"]
            if artists_tag == "":
                artists_tag = music_fetcher.artists_list_tostring(song_info["artists"])
            if album_tag == "":
                album_tag = song_info["album"]
            album_art_url = music_fetcher.get_album_art_url(album_tag, artists_tag[0])
            # Set the ID3 tags if it downloaded
            if downloaded_mp3_location is not None:
                downloader.set_mp3_tags(mp3_location=downloaded_mp3_location,
                                        title=title_tag,
                                        artists=[artists_tag],
                                        album=album_tag,
                                        album_art_url=album_art_url,
                                        status_printer=set_status_text)
                set_status_text("Status: Idle")

        elif link_entry.get().find("youtube.com") != -1:
            # Download the song using the YouTube link
            downloaded_mp3_location = downloader.download_audio(link_entry.get(), download_location_entry.get(),
                                                                set_status_text)
            if downloaded_mp3_location is None:
                enable_gui("song")
                return

            # Replace the fields that the user didn't input anything in with the data that the program found
            youtube_video_info = music_fetcher.get_youtube_video_information(link_entry.get(), set_status_text)
            if title_tag == "":
                title_tag = youtube_video_info[0]
            if artists_tag == "":
                artists_tag = youtube_video_info[1]
            album_info = music_fetcher.get_album_from_song(title_tag, [artists_tag])
            if album_tag == "":
                album_tag = album_info[0]
            album_art_url = album_info[1]
            # Set the ID3 tags if it downloaded
            downloader.set_mp3_tags(mp3_location=downloaded_mp3_location,
                                    title=title_tag,
                                    artists=[artists_tag],
                                    album=album_tag,
                                    album_art_url=album_art_url,
                                    status_printer=set_status_text)
            set_status_text("Status: Idle")
        else:
            set_status_text("Error: Bad URL", is_error=True)

        enable_gui("song")

    if input_setting_var.get() == "playlist":
        downloader_thread = threading.Thread(target=download_playlist)
    elif input_setting_var.get() == "song":
        downloader_thread = threading.Thread(target=download_song)
    else:
        raise NotImplementedError

    downloader_thread.start()


def disable_gui():
    """Disables all GUI widgets. Meant to be used while the program is finding/downloading."""
    link_entry.config(state="disabled")
    song_title_entry.config(state="disabled")
    song_artist_entry.config(state="disabled")
    song_album_entry.config(state="disabled")
    download_location_entry.config(state="disabled")
    download_button.config(state="disabled")
    playlist_radiobutton.config(state="disabled")
    song_radiobutton.config(state="disabled")


def enable_gui(input_setting: str):
    """Enables all GUI widgets. Meant to be used after the program is done finding/downloading."""
    if input_setting == "playlist":
        link_entry.config(state="normal")
        song_title_entry.config(state="disabled")
        song_artist_entry.config(state="disabled")
        song_album_entry.config(state="disabled")
    elif input_setting == "song":
        link_entry.config(state="normal")
        song_title_entry.config(state="normal")
        song_artist_entry.config(state="normal")
        song_album_entry.config(state="normal")
    else:
        raise NotImplementedError
    download_location_entry.config(state="normal")
    download_button.config(state="normal")
    playlist_radiobutton.config(state="normal")
    song_radiobutton.config(state="normal")


def set_status_text(text: str, is_error: bool = False):
    """Sets the status text. The status text will be red if the is_error boolean is set to True."""
    status_label.config(text=text)
    if is_error:
        status_label.config(fg="#FF0000")
    else:
        status_label.config(fg="#000000")


def place_user_input_widgets(rely: float, frame: Frame, widget1: Widget, widget2: Widget):
    """Places two widgets within a frame, and then places the frame in the window."""
    frame.place(relx=0.5, rely=rely, anchor=CENTER)
    widget1.pack(side=LEFT)
    widget2.pack(side=RIGHT)


if __name__ == "__main__":

    # Make sure that there is a marcato music folder
    if not os.path.exists(f"{os.getcwd()}\\marcato music"):
        os.mkdir(f"{os.getcwd()}\\marcato music")

    # Set the window up
    window = Tk()
    window.geometry("520x350")
    window.title("Marcato")
    window.iconphoto(True, PhotoImage(file="/icon.png"))
    window.resizable(False, False)

    # Add contents
    gui_font = ("Segoe UI", 12, "bold")
    input_font = ("Segoe UI", 12)

    title_label = Label(window, text="marcato", font=("Segoe UI", 36, "bold"), padx=0, pady=0)

    link_frame = Frame(window)
    link_label = Label(link_frame, text="URL Address: ", font=gui_font)
    link_entry = BetterEntry(link_frame, font=input_font)

    song_title_frame = Frame(window)
    song_title_label = Label(song_title_frame, text="Title: ", font=gui_font)
    song_title_entry = BetterEntry(song_title_frame, font=input_font)

    song_artist_frame = Frame(window)
    song_artist_label = Label(song_artist_frame, text="Artist: ", font=gui_font)
    song_artist_entry = BetterEntry(song_artist_frame, font=input_font)

    song_album_frame = Frame(window)
    song_album_label = Label(song_album_frame, text="Album: ", font=gui_font)
    song_album_entry = BetterEntry(song_album_frame, font=input_font)

    download_location_frame = Frame(window)
    download_location_label = Label(download_location_frame, text="Download Location: ", font=gui_font)
    download_location_entry = BetterEntry(download_location_frame, font=input_font)
    download_location_entry.insert(0, f"{os.getcwd()}\\marcato music")

    download_button = Button(window, text="Find and Download", command=download_action)

    status_label = Label(window, text="Status: Idle", font=("Segoe UI", 8), fg="#000000")

    radiobutton_frame = Frame(window)
    input_setting_var = StringVar()
    input_setting_var.set("playlist")
    playlist_radiobutton = Radiobutton(radiobutton_frame, text="Playlist", variable=input_setting_var, value="playlist",
                                       command=lambda: (enable_gui("playlist")))
    song_radiobutton = Radiobutton(radiobutton_frame, text="Individual Song", variable=input_setting_var, value="song",
                                   command=lambda: (enable_gui("song")))

    title_label.place(relx=0.5, rely=0.16, anchor=CENTER)
    place_user_input_widgets(0.30, link_frame, link_label, link_entry)
    place_user_input_widgets(0.39, song_title_frame, song_title_label, song_title_entry)
    place_user_input_widgets(0.48, song_artist_frame, song_artist_label, song_artist_entry)
    place_user_input_widgets(0.57, song_album_frame, song_album_label, song_album_entry)
    place_user_input_widgets(0.66, download_location_frame, download_location_label, download_location_entry)
    download_button.place(relx=0.5, rely=0.77, anchor=CENTER)
    status_label.place(relx=0.5, rely=0.85, anchor=CENTER)
    place_user_input_widgets(0.935, radiobutton_frame, playlist_radiobutton, song_radiobutton)
    window.update()

    # Initiate the window
    enable_gui("playlist")
    window.mainloop()
