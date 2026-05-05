from collections import deque
import time
import customtkinter as ctk

from .libraryFrame import LibraryFrame
from .playingQueueFrame import PlayingQueueFrame     
from .currentPlayingFrame import CurrentPlayingFrame       

class MainFrame(ctk.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master);
        self.master = master
        self.data = data

        self.grid_columnconfigure((0, 2), weight=1)
        self.grid_columnconfigure(1, weight=3)
        self.grid_rowconfigure(0, weight=3)
        self.grid_rowconfigure(1, weight=1)

        self.libraryFrame = LibraryFrame(self, self.data["library"])
        self.libraryFrame.grid(row=0, column=0, rowspan=1, padx=10, pady=10, sticky="nsew")

        self.mainArea = ctk.CTkFrame(self)
        self.mainArea.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")

        self.currentPlaying = CurrentPlayingFrame(self, self.data["current"])
        self.currentPlaying.grid(row=1, column=0, columnspan=3, padx=10, pady=10, sticky="nsew")

        self.playingQueueFrame = PlayingQueueFrame(self, self.data["queue"])
        self.playingQueueFrame.grid(row=0, column=2, padx=10, pady=10, sticky="nsew")
