import _tkinter
import os
import threading
import tkinter
from tkinter import *

import PIL.Image
import customtkinter

import downloader
import music_fetcher


# Copied from https://www.reddit.com/r/learnpython/comments/k5lgyd/tkinter_how_do_i_make_ctrlbackspace_work_like/
class BetterEntry(customtkinter.CTkEntry):
    """This class supports control-backspace deletion of an entire word"""

    def __init__(self, master=None, **kwargs):
        super().__init__(master, **kwargs)
        self.bind('<Control-BackSpace>', self.delete_proceeding_word)

    def delete_proceeding_word(self, event):
        blinker_index = self.index(tkinter.INSERT)
        deletion_begin_index = self.get().rfind(" ", None, blinker_index)
        self.select_range(deletion_begin_index, blinker_index)


def download_action():
    """Starts a thread that tries to find and download the mp3 that the user requested through the inputs."""

    def download_playlist():
        disable_gui()

        if link_entry.get().find("spotify.com") != -1:
            song_list = music_fetcher.get_spotify_playlist_songs(link_entry.get(), status_printer=set_status_text)
            if song_list is None:
                enable_gui("playlist")
                return
            for i in range(len(song_list)):
                song = song_list[i]
                url = music_fetcher.find_youtube_url(song["title"], song["artists"], status_printer=set_status_text)
                if url is None:
                    break
                downloaded_mp3_location = downloader.download_audio(url, download_location_entry.get(), set_status_text)
                if downloaded_mp3_location is not None:
                    downloader.set_mp3_tags(downloaded_mp3_location, song["title"], song["artists"], song["album"],
                                            song["album art url"], status_printer=set_status_text)
                playlist_progress_bar.set(float(i + 1) / float(len(song_list)))
            playlist_progress_bar.set(0)
            set_status_text("Status: Idle")

        elif link_entry.get().find("youtube.com") != -1:
            song_url_list = music_fetcher.get_youtube_playlist_songs_urls(link_entry.get(),
                                                                          status_printer=set_status_text)
            for i in range(len(song_url_list)):
                song_url = song_url_list[i]
                downloaded_mp3_location = downloader.download_audio(song_url, download_location_entry.get(),
                                                                    set_status_text)
                if downloaded_mp3_location is not None:
                    title, artists = music_fetcher.get_youtube_video_information(song_url, set_status_text)
                    album, album_art_url = music_fetcher.get_album_from_song(title, artists)
                    downloader.set_mp3_tags(downloaded_mp3_location, title, [artists], album,
                                            album_art_url, status_printer=set_status_text)
                playlist_progress_bar.set(float(i + 1) / float(len(song_url_list)))
            playlist_progress_bar.set(0)
            set_status_text("Status: Idle")
        else:
            set_status_text("Error: Bad URL", is_error=True)

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
    link_entry.configure(state="disabled", fg_color="#202020")
    song_title_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    song_artist_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    song_album_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    download_location_entry.configure(state="disabled", fg_color="#202020")
    download_button.configure(state="disabled", fg_color="#7d5773", hover=False)
    playlist_radiobutton.configure(state="disabled")
    song_radiobutton.configure(state="disabled")
    # Remove the focus from any of the entries
    title_label.focus()


def enable_gui(input_setting: str):
    """Enables all GUI widgets. Meant to be used after the program is done finding/downloading."""
    if input_setting == "playlist":
        link_entry.configure(state="normal", fg_color="#363636", placeholder_text="Spotify or YouTube Playlist Link")
        song_title_entry.configure(placeholder_text="")
        song_artist_entry.configure(placeholder_text="")
        song_album_entry.configure(placeholder_text="")
        song_title_entry.configure(state="disabled", fg_color="#202020")
        song_artist_entry.configure(state="disabled", fg_color="#202020")
        song_album_entry.configure(state="disabled", fg_color="#202020")
        entry_directions_label.place_forget()
        playlist_progress_bar.place(relx=0.5, y=356, anchor=CENTER)

    elif input_setting == "song":
        link_entry.configure(state="normal", fg_color="#363636", placeholder_text="Spotify or YouTube Song Link")
        song_title_entry.configure(state="normal", fg_color="#363636")
        song_artist_entry.configure(state="normal", fg_color="#363636")
        song_album_entry.configure(state="normal", fg_color="#363636")
        entry_directions_label.place(relx=0.5, y=356, anchor=CENTER)
        playlist_progress_bar.place_forget()
    else:
        raise NotImplementedError
    download_location_entry.configure(state="normal", fg_color="#363636")
    download_button.configure(state="normal", fg_color="#80005d", hover=True)
    playlist_radiobutton.configure(state="normal")
    song_radiobutton.configure(state="normal")
    # Remove the focus from any of the entries (if the focus is still on the link entry, then it'll screw up the
    # placeholder text
    title_label.focus()


def set_status_text(text: str, is_error: bool = False):
    """Sets the status text. The status text will be red if the is_error boolean is set to True."""
    status_label.configure(text=text)
    if is_error:
        status_label.configure(text_color="#ff4747")
    else:
        status_label.configure(text_color="gray84")


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
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("dark-blue")
    window = customtkinter.CTk()
    window.geometry("520x370")
    window.title("marcato")
    window.resizable(False, False)
    try:
        window.iconbitmap("icon.ico")
    except _tkinter.TclError:
        pass
    window.update()

    # Add contents
    gui_font = ("Segoe UI", 16, "bold")
    input_font = ("Segoe UI", 12)

    title_label = customtkinter.CTkLabel(window, text="marcato", font=("Segoe UI", 45, "bold"), )

    entry_frame = customtkinter.CTkFrame(window, bg_color="transparent", fg_color="transparent", width=399, height=399)

    link_frame = customtkinter.CTkFrame(window)
    link_label = customtkinter.CTkLabel(entry_frame, text="URL Address: ", font=gui_font)
    link_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=183)

    song_title_frame = customtkinter.CTkFrame(window)
    song_title_label = customtkinter.CTkLabel(entry_frame, text="Title: ", font=gui_font)
    song_title_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)

    song_artist_frame = customtkinter.CTkFrame(window)
    song_artist_label = customtkinter.CTkLabel(entry_frame, text="Artist: ", font=gui_font)
    song_artist_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)

    song_album_frame = customtkinter.CTkFrame(window)
    song_album_label = customtkinter.CTkLabel(entry_frame, text="Album: ", font=gui_font, anchor="e")
    song_album_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)

    download_location_frame = customtkinter.CTkFrame(window)
    download_location_label = customtkinter.CTkLabel(entry_frame, text="Download Location: ",
                                                     font=gui_font)
    download_location_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=200)
    download_location_entry.insert(0, f"{os.getcwd()}\\marcato music")

    download_button = customtkinter.CTkButton(window, text="Find and Download", command=download_action,
                                              font=("Segoe UI", 14), fg_color="#80005d", hover_color="#590041")

    status_label = customtkinter.CTkLabel(window, text="Status: Idle", font=("Segoe UI", 13, "italic"))

    radiobutton_frame = customtkinter.CTkFrame(window, bg_color="transparent", fg_color="transparent")
    input_setting_var = StringVar()
    input_setting_var.set("playlist")
    playlist_radiobutton = customtkinter.CTkRadioButton(radiobutton_frame, text="Playlist", variable=input_setting_var,
                                                        value="playlist", command=lambda: (enable_gui("playlist")),
                                                        font=("Segoe UI", 12),
                                                        radiobutton_width=12,
                                                        radiobutton_height=12,
                                                        hover=False,
                                                        border_width_checked=3,
                                                        fg_color="#80005d")
    song_radiobutton = customtkinter.CTkRadioButton(radiobutton_frame, text="Individual Song",
                                                    variable=input_setting_var, value="song",
                                                    command=lambda: (enable_gui("song")),
                                                    font=("Segoe UI", 12),
                                                    radiobutton_width=12,
                                                    radiobutton_height=12,
                                                    hover=False,
                                                    border_width_checked=3,
                                                    fg_color="#80005d")

    entry_directions_label = customtkinter.CTkLabel(window, text="marcato will automatically fill in the title, "
                                                                 "artists, or album when they are left blank",
                                                    font=("Segoe UI", 12))

    playlist_progress_bar = customtkinter.CTkProgressBar(window, orientation="horizontal", progress_color="#b50084")
    playlist_progress_bar.set(0)

    title_label.place(relx=0.5, y=60, anchor=CENTER)

    entry_frame.place(relx=0.5, y=90, anchor="n")
    begin_y = 20
    separation = 32
    link_label.place(relx=0.5, y=begin_y, anchor="e")
    link_entry.place(relx=0.5, y=begin_y, anchor="w")
    song_title_label.place(relx=0.5, y=begin_y + separation, anchor="e")
    song_title_entry.place(relx=0.5, y=begin_y + separation, anchor="w")
    song_artist_label.place(relx=0.5, y=begin_y + separation * 2, anchor="e")
    song_artist_entry.place(relx=0.5, y=begin_y + separation * 2, anchor="w")
    song_album_label.place(relx=0.5, y=begin_y + separation * 3, anchor="e")
    song_album_entry.place(relx=0.5, y=begin_y + separation * 3, anchor="w")
    download_location_label.place(relx=0.5, y=begin_y + separation * 4, anchor="e")
    download_location_entry.place(relx=0.5, y=begin_y + separation * 4, anchor="w")

    download_button.place(relx=0.5, y=280, anchor=CENTER)
    status_label.place(relx=0.5, y=308, anchor=CENTER)
    radiobutton_frame.place(relx=0.5, y=333, anchor=CENTER)
    playlist_radiobutton.pack(side=LEFT)
    song_radiobutton.pack(side=RIGHT)

    playlist_progress_bar.place(relx=0.5, y=356, anchor=CENTER)

    window.update()

    # Initiate the window
    enable_gui("playlist")
    window.mainloop()
