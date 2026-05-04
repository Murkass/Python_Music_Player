from collections import deque
import time
import customtkinter

from .libraryFrame import LibraryFrame
from .currentPlayingFrame import CurrentPlayingFrame

class MainFrame(customtkinter.CTkFrame):
    def __init__(self, master, data):
        super().__init__(master);
        self.master = master
        self.data = data

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure((0, 1), weight=1)

        self.libraryFrame = LibraryFrame(self, self.data.library)
        self.libraryFrame.grid(row=0, column=0, rowspan=2, padx=10, pady=10, sticky="nse")

        self.mainArea = None
        self.mainArea.grid(row=0, column=1, padx=10, pady=10, sticky="new")

        self.playingQueue = None
        self.playingQueue.grid(row=1, column=1, padx=10, pady=10, sticky="sew")

        self.currentPlaying = CurrentPlayingFrame(self, self.data.currentPlaying)
        self.currentPlaying.grid(row=0, column=1, padx=10, pady=10, sticky="nsw")
