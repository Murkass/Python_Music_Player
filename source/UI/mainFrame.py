from __future__ import annotations

import customtkinter as ctk

from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler
from source.core.recommender import Recommender

from .currentPlayingFrame import CurrentPlayingFrame
from .libraryFrame import LibraryFrame
from .main_area import MainAreaFrame
from .playingQueueFrame import PlayingQueueFrame
from .style import button_tokens, get_theme


class MainFrame(ctk.CTkFrame):
    def __init__(self, master, library_handler: LibraryHandler, music_handler: MusicHandler):
        super().__init__(master, fg_color="transparent")
        self.library_handler = library_handler
        self.music_handler = music_handler
        self.recommender = Recommender(library_handler)
        self.sidebar_collapsed = False
        self.queue_collapsed = False
        self.theme = get_theme(self.library_handler.get_settings().get("color_theme"))

        self.grid_columnconfigure(0, weight=0, minsize=260)
        self.grid_columnconfigure(1, weight=0, minsize=30)
        self.grid_columnconfigure(2, weight=1)
        self.grid_columnconfigure(3, weight=0, minsize=30)
        self.grid_columnconfigure(4, weight=0, minsize=280)
        self.grid_rowconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=0)

        self.libraryFrame = LibraryFrame(
            self,
            library_handler=self.library_handler,
            on_tab_selected=self.show_tab,
            on_playlist_selected=self.select_playlist,
            on_create_playlist=self._create_playlist,
        )
        self.libraryFrame.grid(row=0, column=0, sticky="nsew", padx=(10, 4), pady=10)

        self.leftRail = ctk.CTkFrame(self, width=30, corner_radius=16)
        self.leftRail.grid(row=0, column=1, sticky="ns", padx=(0, 4), pady=10)
        self.leftRail.grid_rowconfigure(1, weight=1)
        self.leftToggleButton = ctk.CTkButton(self.leftRail, text="<", width=24, height=30, command=self.toggle_sidebar)
        self.leftToggleButton.grid(row=0, column=0, padx=3, pady=6)

        self.mainArea = MainAreaFrame(
            self,
            music_handler=self.music_handler,
            library_handler=self.library_handler,
            recommender=self.recommender,
            on_preferences_changed=self.apply_theme,
        )
        self.mainArea.grid(row=0, column=2, sticky="nsew", padx=4, pady=10)

        self.rightRail = ctk.CTkFrame(self, width=30, corner_radius=16)
        self.rightRail.grid(row=0, column=3, sticky="ns", padx=4, pady=10)
        self.rightRail.grid_rowconfigure(1, weight=1)
        self.rightToggleButton = ctk.CTkButton(self.rightRail, text=">", width=24, height=30, command=self.toggle_queue_sidebar)
        self.rightToggleButton.grid(row=0, column=0, padx=3, pady=6)

        self.playingQueueFrame = PlayingQueueFrame(self, self.music_handler)
        self.playingQueueFrame.grid(row=0, column=4, sticky="nsew", padx=(4, 10), pady=10)

        self.currentPlaying = CurrentPlayingFrame(self, self.music_handler, self.library_handler)
        self.currentPlaying.grid(row=1, column=0, columnspan=5, sticky="ew", padx=10, pady=(0, 10))

        self.music_handler.add_listener(self.currentPlaying)
        self.music_handler.add_listener(self.playingQueueFrame)
        self.music_handler.add_listener(self.mainArea)
        self.music_handler.add_listener(self.mainArea.profile_frame)

        self.apply_theme()

        settings = self.library_handler.get_settings()
        last_playlist = settings.get("last_playlist")
        if last_playlist:
            self.select_playlist(last_playlist)
        else:
            self.show_tab("Biblioteca")

    def _create_playlist(self) -> None:
        self.mainArea.prompt_create_playlist()
        self.libraryFrame.refresh_playlists()
        self.libraryFrame.set_active_playlist(self.mainArea.selected_playlist)

    def show_tab(self, tab_name: str) -> None:
        self.mainArea.show_tab(tab_name)
        self.libraryFrame.set_active_tab(tab_name)

    def select_playlist(self, playlist_name: str) -> None:
        self.mainArea.select_playlist(playlist_name)
        self.libraryFrame.set_active_tab("Playlists")
        self.libraryFrame.set_active_playlist(playlist_name)
        self.libraryFrame.refresh_playlists()

    def toggle_sidebar(self) -> None:
        self.sidebar_collapsed = not self.sidebar_collapsed
        if self.sidebar_collapsed:
            self.libraryFrame.grid_remove()
            self.grid_columnconfigure(0, minsize=0)
            self.leftToggleButton.configure(text=">")
        else:
            self.libraryFrame.grid()
            self.grid_columnconfigure(0, minsize=260)
            self.leftToggleButton.configure(text="<")
        self.libraryFrame.set_collapsed(self.sidebar_collapsed)

    def toggle_queue_sidebar(self) -> None:
        self.queue_collapsed = not self.queue_collapsed
        if self.queue_collapsed:
            self.playingQueueFrame.grid_remove()
            self.grid_columnconfigure(4, minsize=0)
            self.rightToggleButton.configure(text="<")
        else:
            self.playingQueueFrame.grid()
            self.grid_columnconfigure(4, minsize=280)
            self.rightToggleButton.configure(text=">")

    def apply_theme(self) -> None:
        self.theme = get_theme(self.library_handler.get_settings().get("color_theme"))
        self.master.configure(fg_color=self.theme.background)
        self.configure(fg_color="transparent")
        self.leftRail.configure(fg_color=self.theme.panel, border_width=1, border_color=self.theme.border)
        self.rightRail.configure(fg_color=self.theme.panel, border_width=1, border_color=self.theme.border)
        self.leftToggleButton.configure(corner_radius=12, **button_tokens(self.theme, "secondary"))
        self.rightToggleButton.configure(corner_radius=12, **button_tokens(self.theme, "secondary"))
        self.libraryFrame.apply_theme(self.theme)
        self.mainArea.apply_theme(self.theme)
        self.playingQueueFrame.apply_theme(self.theme)
        self.currentPlaying.apply_theme(self.theme)

    def destroy(self):
        self.music_handler.shutdown()
        super().destroy()
