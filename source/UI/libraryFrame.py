import customtkinter as ctk
from PIL import Image, ImageTk
from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler


class LibraryFrame(LibraryHandler, ctk.CTkFrame):
    def __init__(self, master, musicHandler: MusicHandler):
        LibraryHandler.__init__(self)  # Inicializa handler
        ctk.CTkFrame.__init__(self, master)  # Inicializa frame
        self.handler = musicHandler
        
        # Agora pode usar: self.add_music_to_playlist(), etc
        playlists = self.get_all_playlists()
        for playlist in playlists:
            btn = ctk.CTkButton(self, text=playlist, 
                              command=lambda p=playlist: self.get_playlist(p))
            btn.pack()

    def get_playlist(self, playlist_name):
        playlist = super().get_playlist(playlist_name)
        self.handler.selectPlaylist()
        return 