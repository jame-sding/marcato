import os
import threading
import tkinter
from tkinter import *

import downloader


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
    def download_thread_action():
        disable_gui()
        downloaded_mp3_location = downloader.download_audio(song_link_entry.get(), download_location_entry.get(),
                                                            set_status_text)
        if downloaded_mp3_location is not None:
            downloader.set_mp3_tags(downloaded_mp3_location, song_title_entry.get(), song_artist_entry.get(),
                                    song_album_entry.get())
            set_status_text("Status: Idle")
        enable_gui()

    downloader_thread = threading.Thread(target=download_thread_action)
    downloader_thread.start()


def disable_gui():
    """Disables all GUI widgets. Meant to be used while the program is finding/downloading."""
    song_link_entry.config(state="disabled")
    song_title_entry.config(state="disabled")
    song_artist_entry.config(state="disabled")
    download_location_entry.config(state="disabled")
    download_button.config(state="disabled")


def enable_gui():
    """Enables all GUI widgets. Meant to be used after the program is done finding/downloading."""
    song_link_entry.config(state="normal")
    song_title_entry.config(state="normal")
    song_artist_entry.config(state="normal")
    download_location_entry.config(state="normal")
    download_button.config(state="normal")


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


# Set the window up
window = Tk()
window.geometry("520x320")
window.title("Music Downloader")
window.iconphoto(True, PhotoImage(file="/icon.png"))
window.resizable(False, False)


# Add contents
gui_font = ("Segoe UI", 12, "bold")
input_font = ("Segoe UI", 12)

title_label = Label(window, text="Music Downloader", font=("Segoe UI", 30, "bold"), padx=0, pady=0)

song_link_frame = Frame(window)
song_link_label = Label(song_link_frame, text="Song Link: ", font=gui_font)
song_link_entry = BetterEntry(song_link_frame, font=input_font)

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
download_location_entry.insert(0, os.getcwd())

download_button = Button(window, text="Find and Download", command=download_action)

status_label = Label(window, text="Status: Idle", font=("Segoe UI", 8), fg="#000000")

title_label.place(relx=0.5, rely=0.16, anchor=CENTER)
place_user_input_widgets(0.32, song_link_frame, song_link_label, song_link_entry)
place_user_input_widgets(0.42, song_title_frame, song_title_label, song_title_entry)
place_user_input_widgets(0.52, song_artist_frame, song_artist_label, song_artist_entry)
place_user_input_widgets(0.62, song_album_frame, song_album_label, song_album_entry)
place_user_input_widgets(0.72, download_location_frame, download_location_label, download_location_entry)
download_button.place(relx=0.5, rely=0.85, anchor=CENTER)
status_label.place(relx=0.5, rely=0.93, anchor=CENTER)

# Initiate the window
window.mainloop()
