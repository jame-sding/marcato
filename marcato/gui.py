import _tkinter
import os
import threading
import tkinter
from tkinter import *

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
        disable_gui(True)

        if link_entry.get().find("spotify.com") != -1:
            # Get the playlist songs
            song_list = music_fetcher.get_spotify_playlist_songs(link_entry.get(), status_printer=set_status_text)
            if song_list is None:
                enable_gui("playlist")
                return
            # Create a folder for the playlist's mp3s
            playlist_folder = create_playlist_folder(music_fetcher.get_spotify_playlist_name(link_entry.get(),
                                                                                             status_printer=
                                                                                             set_status_text),
                                                     parent_dir=download_location_entry.get())
            # Download the songs through YouTube
            for i in range(len(song_list)):
                if user_has_cancelled[0]:
                    user_has_cancelled[0] = False
                    break
                song = song_list[i]
                try_again = True
                blacklist = []
                url = ""
                downloaded_mp3_location = ""
                while try_again:
                    url = music_fetcher.find_youtube_url(song["title"], song["artists"], status_printer=set_status_text
                                                         , blacklist=blacklist)
                    downloaded_mp3_location = downloader.download_audio(url, playlist_folder, set_status_text)
                    # In the case that the video is age restricted, and hence cannot be downloaded, we will find a
                    # different video.
                    if downloaded_mp3_location == "age restricted":
                        set_status_text(f"Status: Finding new YouTube video for {song['title']}")
                        blacklist.append(url)
                    else:
                        try_again = False
                if url is None:
                    break
                # Set ID3 tags
                if downloaded_mp3_location is not None:
                    playlist_progress_bar.set((i + 0.5) / float(len(song_list)))
                    downloader.set_mp3_tags(downloaded_mp3_location, song["title"], song["artists"], song["album"],
                                            song["album art url"], status_printer=set_status_text)
                playlist_progress_bar.set(float(i + 1) / float(len(song_list)))
            # Reset the GUI
            playlist_progress_bar.set(0)
            set_status_text("Status: Idle")

        elif link_entry.get().find("youtube.com") != -1:
            # Get the playlist songs
            song_url_list = music_fetcher.get_youtube_playlist_songs_urls(link_entry.get(),
                                                                          status_printer=set_status_text)
            if song_url_list is None:
                enable_gui("playlist")
                return
            # Create a folder for the playlist's mp3s
            playlist_folder = create_playlist_folder(music_fetcher.get_spotify_playlist_name(link_entry.get(),
                                                                                             status_printer=
                                                                                             set_status_text),
                                                     parent_dir=download_location_entry.get())
            # Download the songs right off of YouTube
            for i in range(len(song_url_list)):

                if user_has_cancelled[0]:
                    user_has_cancelled[0] = False
                    break

                song_url = song_url_list[i]
                downloaded_mp3_location = downloader.download_audio(song_url, playlist_folder, set_status_text)
                # Set ID3 tags
                if downloaded_mp3_location is not None:
                    playlist_progress_bar.set((i + 0.5) / float(len(song_url_list)))
                    title, artists = music_fetcher.get_youtube_video_information(song_url, set_status_text)
                    album, album_art_url = music_fetcher.get_album_from_song(title, artists)
                    downloader.set_mp3_tags(downloaded_mp3_location, title, [artists], album,
                                            album_art_url, status_printer=set_status_text)
                playlist_progress_bar.set(float(i + 1) / float(len(song_url_list)))
            # Reset the GUI
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
        album_tag = song_album_entry.get()

        if link_entry.get().find("spotify.com") != -1:
            # Find the song on YouTube
            song_info = music_fetcher.get_spotify_song_info(song_url=link_entry.get(), status_printer=set_status_text)
            if song_info is None:
                enable_gui("song")
                return
            playlist_progress_bar.set(0.2)
            try_again = True
            blacklist = []
            downloaded_mp3_location = ""
            while try_again:
                url = music_fetcher.find_youtube_url(song_info["title"], song_info["artists"], blacklist=blacklist)
                downloaded_mp3_location = downloader.download_audio(url, download_location_entry.get(), set_status_text)
                # In case the song that we found was age restricted (and hence can't be downloaded), we must find a
                # different video.
                if downloaded_mp3_location == "age restricted":
                    set_status_text(f"Status: Finding new YouTube video for {song_info['title']}")
                    blacklist.append(url)
                else:
                    try_again = False
            playlist_progress_bar.set(0.6)
            # Replace the fields that the user didn't input anything in with the data that the program found
            if title_tag == "":
                title_tag = song_info["title"]
            if artists_tag == "":
                artists_tag = music_fetcher.artists_list_tostring(song_info["artists"])
            if album_tag == "":
                album_tag = song_info["album"]
            album_art_url = music_fetcher.get_album_art_url(album_tag, artists_tag[0])
            playlist_progress_bar.set(0.75)
            # Set ID3 tags
            if downloaded_mp3_location is not None:
                downloader.set_mp3_tags(mp3_location=downloaded_mp3_location,
                                        title=title_tag,
                                        artists=[artists_tag],
                                        album=album_tag,
                                        album_art_url=album_art_url,
                                        status_printer=set_status_text)
                set_status_text("Status: Idle")
            playlist_progress_bar.set(0)

        elif link_entry.get().find("youtube.com") != -1:
            playlist_progress_bar.set(0.17)
            # Download the song using the YouTube link
            downloaded_mp3_location = downloader.download_audio(link_entry.get(), download_location_entry.get(),
                                                                set_status_text)
            if downloaded_mp3_location is None:
                enable_gui("song")
                return
            playlist_progress_bar.set(0.5)
            # Replace the fields that the user didn't input anything in with the data that the program found
            youtube_video_info = music_fetcher.get_youtube_video_information(link_entry.get(), set_status_text)
            if title_tag == "":
                title_tag = youtube_video_info[0]
            if artists_tag == "":
                artists_tag = youtube_video_info[1]
            print(artists_tag)
            album_info = music_fetcher.get_album_from_song(title_tag, [artists_tag])
            if album_tag == "":
                album_tag = album_info[0]
            album_art_url = album_info[1]
            playlist_progress_bar.set(0.65)
            # Set ID3 tags
            downloader.set_mp3_tags(mp3_location=downloaded_mp3_location,
                                    title=title_tag,
                                    artists=[artists_tag],
                                    album=album_tag,
                                    album_art_url=album_art_url,
                                    status_printer=set_status_text)
            set_status_text("Status: Idle")
            playlist_progress_bar.set(0)
        else:
            set_status_text("Error: Bad URL", is_error=True)

        enable_gui("song")

    def download_video():
        disable_gui()

        # No, we actually haven't actually made any good progress, but we want to tell the user that the program is
        # beginning to work
        playlist_progress_bar.set(0.2)
        # Get the user's inputted information
        downloaded_mp4_location = downloader.download_video(link_entry.get(), download_location_entry.get(),
                                                            set_status_text)
        if downloaded_mp4_location is not None:
            set_status_text("Status: Idle")
        playlist_progress_bar.set(0)
        enable_gui("video")

    if input_setting_var.get() == "playlist":
        downloader_thread = threading.Thread(target=download_playlist)
    elif input_setting_var.get() == "song":
        downloader_thread = threading.Thread(target=download_song)
    elif input_setting_var.get() == "video":
        downloader_thread = threading.Thread(target=download_video)
    else:
        raise NotImplementedError

    downloader_thread.start()


def cancel_download():
    user_has_cancelled[0] = True
    action_button.configure(state="disabled", fg_color="#7d5773", hover=False)


def disable_gui(during_playlist: bool = False):
    """Disables all GUI widgets. Meant to be used while the program is finding/downloading."""
    link_entry.configure(state="disabled", fg_color="#202020")
    song_title_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    song_artist_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    song_album_entry.configure(state="disabled", fg_color="#202020", placeholder_text="")
    download_location_entry.configure(state="disabled", fg_color="#202020")
    if during_playlist:
        action_button.configure(text="Cancel", command=cancel_download)
    else:
        action_button.configure(state="disabled", fg_color="#7d5773", hover=False)
    playlist_radiobutton.configure(state="disabled")
    song_radiobutton.configure(state="disabled")
    video_radiobutton.configure(state="disabled")
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
        info_label.configure(text="*100-song limit for Spotify playlists. \n*A few songs on YouTube playlists might not"
                                  " get downloaded (technical reasons).")

    elif input_setting == "song":
        link_entry.configure(state="normal", fg_color="#363636", placeholder_text="Spotify or YouTube Song Link")
        song_title_entry.configure(state="normal", fg_color="#363636")
        song_artist_entry.configure(state="normal", fg_color="#363636")
        song_album_entry.configure(state="normal", fg_color="#363636")
        info_label.configure(text="marcato will automatically fill in the title, artists, or album when they are left "
                                  "blank")
    elif input_setting == "video":
        link_entry.configure(state="normal", fg_color="#363636", placeholder_text="YouTube Video Link")
        song_title_entry.configure(state="disabled", fg_color="#202020")
        song_artist_entry.configure(state="disabled", fg_color="#202020")
        song_album_entry.configure(state="disabled", fg_color="#202020")
        info_label.configure(text="Only YouTube videos are accepted")
    else:
        raise NotImplementedError
    download_location_entry.configure(state="normal", fg_color="#363636")
    action_button.configure(state="normal", fg_color="#80005d", hover=True, text="Find and Download",
                            command=download_action)
    playlist_radiobutton.configure(state="normal")
    song_radiobutton.configure(state="normal")
    video_radiobutton.configure(state="normal")
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


def create_playlist_folder(playlist_name: str, parent_dir: str):
    # Find a folder name that hasn't been taken yet
    folder_name = playlist_name
    count = 1
    while os.path.exists(f"{parent_dir}\\{folder_name}"):
        print("path exists")
        folder_name = f"{playlist_name}({count})"
        count = count + 1
    print(folder_name)
    # Create the directory
    os.mkdir(f"{parent_dir}\\{folder_name}")
    return f"{parent_dir}\\{folder_name}"


user_has_cancelled = [False]

if __name__ == "__main__":

    # Make sure that there is a marcato downloads folder
    if not os.path.exists(f"{os.getcwd()}\\marcato downloads"):
        os.mkdir(f"{os.getcwd()}\\marcato downloads")

    # Set the window up
    customtkinter.set_appearance_mode("dark")
    customtkinter.set_default_color_theme("dark-blue")
    window = customtkinter.CTk()
    window.geometry("520x399")
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
    link_label = customtkinter.CTkLabel(entry_frame, text="URL Address: ", font=gui_font)
    link_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=183)
    song_title_label = customtkinter.CTkLabel(entry_frame, text="Title: ", font=gui_font)
    song_title_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)
    song_artist_label = customtkinter.CTkLabel(entry_frame, text="Artist: ", font=gui_font)
    song_artist_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)
    song_album_label = customtkinter.CTkLabel(entry_frame, text="Album: ", font=gui_font, anchor="e")
    song_album_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=150)
    download_location_label = customtkinter.CTkLabel(entry_frame, text="Download Location: ",
                                                     font=gui_font)
    download_location_entry = BetterEntry(entry_frame, font=input_font, corner_radius=7, width=200)
    download_location_entry.insert(0, f"{os.getcwd()}\\marcato downloads")

    action_button = customtkinter.CTkButton(window, text="Find and Download", command=download_action,
                                            font=("Segoe UI", 14), fg_color="#80005d", hover_color="#590041")

    status_label = customtkinter.CTkLabel(window, text="Status: Idle", font=("Segoe UI", 13, "italic"))

    radiobutton_frame = customtkinter.CTkFrame(window, bg_color="transparent", fg_color="transparent", width=399,
                                               height=20)
    input_setting_var = StringVar()
    input_setting_var.set("playlist")
    playlist_radiobutton = customtkinter.CTkRadioButton(radiobutton_frame, text="Playlist", variable=input_setting_var,
                                                        value="playlist", command=lambda: (enable_gui("playlist")),
                                                        font=("Segoe UI", 12), radiobutton_width=12,
                                                        radiobutton_height=12, hover=False, border_width_checked=3,
                                                        fg_color="#80005d")
    song_radiobutton = customtkinter.CTkRadioButton(radiobutton_frame, text="Individual Audio",
                                                    variable=input_setting_var, value="song",
                                                    command=lambda: (enable_gui("song")), font=("Segoe UI", 12),
                                                    radiobutton_width=12, radiobutton_height=12, hover=False,
                                                    border_width_checked=3, fg_color="#80005d")
    video_radiobutton = customtkinter.CTkRadioButton(radiobutton_frame, text="Video", variable=input_setting_var,
                                                     value="video", command=lambda: (enable_gui("video")),
                                                     font=("Segoe UI", 12), radiobutton_width=12, radiobutton_height=12,
                                                     hover=False, border_width_checked=3, fg_color="#80005d")

    info_label = customtkinter.CTkLabel(window, font=("Segoe UI", 12))

    playlist_progress_bar = customtkinter.CTkProgressBar(window, orientation="horizontal",
                                                         progress_color="#b50084")
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

    action_button.place(relx=0.5, y=280, anchor=CENTER)

    status_label.place(relx=0.5, y=308, anchor=CENTER)
    radiobutton_frame.place(relx=0.5, y=333, anchor=CENTER)
    playlist_radiobutton.place(relx=0.25, rely=0.5, anchor=CENTER)
    song_radiobutton.place(relx=0.5, rely=0.5, anchor=CENTER)
    video_radiobutton.place(relx=0.85, rely=0.5, anchor=CENTER)
    radiobutton_frame.update()
    print(song_radiobutton.winfo_y(), song_radiobutton.winfo_x())
    print(playlist_radiobutton.winfo_y(), playlist_radiobutton.winfo_x())

    playlist_progress_bar.place(relx=0.5, y=356, anchor=CENTER)
    info_label.place(relx=0.5, y=379, anchor=CENTER)

    window.update()

    # Initiate the window
    enable_gui("playlist")
    window.mainloop()
