import customtkinter as ctk
from .libraryFrame import LibraryFrame
from .playingQueueFrame import PlayingQueueFrame
from .currentPlayingFrame import CurrentPlayingFrame
from .main_area import MainAreaFrame

from source.core.musicHandler import MusicHandler
from source.core.libraryHandler import LibraryHandler

mHandler = MusicHandler()
libHandler = LibraryHandler()


class MainFrame(ctk.CTkFrame):
    def __init__(self, master, data=None):
        super().__init__(master)
        self.master = master
        self.data = data or {}

        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self.libraryFrame = LibraryFrame(self, musicHandler=mHandler)
        self.libraryFrame.grid(row=0, column=0, rowspan=1, padx=10, pady=10, sticky="nsew")

        self.mainArea = MainAreaFrame(self, music_handler=mHandler, library_handler=libHandler)
        self.mainArea.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.playingQueueFrame = PlayingQueueFrame(self, mHandler)
        self.playingQueueFrame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")

        self.currentPlaying = CurrentPlayingFrame(self, mHandler)
        self.currentPlaying.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")
