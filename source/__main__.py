import customtkinter as ctk

from source.UI.mainFrame import MainFrame
from source.UI.style import get_theme
from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler
from source.core.storeHandler import StoreHandler

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.geometry("1400x880")
        self.minsize(1100, 720)
        self.title("Python Music Player")
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.store_handler = StoreHandler()
        self.library_handler = LibraryHandler(self.store_handler)
        self.music_handler = MusicHandler(self.store_handler, library_handler=self.library_handler)

        self.frame = MainFrame(self, library_handler=self.library_handler, music_handler=self.music_handler)
        self.frame.grid(row=0, column=0, sticky="nsew")

if __name__ == "__main__":
    store_handler = StoreHandler()
    library_handler = LibraryHandler(store_handler)
    settings = library_handler.get_settings()
    ctk.set_appearance_mode(settings.get("appearance_mode", "System"))
    ctk.set_default_color_theme("blue")
    app = App()
    app.configure(fg_color=get_theme(settings.get("color_theme")).background)
    app.mainloop()