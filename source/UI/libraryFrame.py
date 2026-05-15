import customtkinter as ctk
from PIL import Image, ImageTk
from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler


class LibraryFrame(LibraryHandler, ctk.CTkFrame):
    def __init__(self, master, musicHandler: MusicHandler):
        LibraryHandler.__init__(self)  # Inicializa handler
        ctk.CTkFrame.__init__(self, master)  # Inicializa frame
        self.handler = musicHandler
        self._build_ui()

    def _build_ui(self):
        playlists = self.get_all_playlists()
        for playlist in playlists:
            btn = ctk.CTkButton(self, text=playlist, command=lambda p=playlist: self._on_playlist_click(p))
            btn.pack(fill="x", padx=8, pady=4)

    def _on_playlist_click(self, playlist_name):
        # Notifica o MainArea (se presente) para mostrar a playlist selecionada
        try:
            if hasattr(self.master, 'mainArea') and getattr(self.master, 'mainArea') is not None:
                self.master.mainArea.select_playlist(playlist_name)
        except Exception as e:
            print(f"Error notifying main area about playlist selection: {e}")