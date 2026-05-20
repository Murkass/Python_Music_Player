from __future__ import annotations

from typing import Callable

import customtkinter as ctk

from source.core.libraryHandler import LibraryHandler
from .style import UITheme, button_tokens, get_theme


class LibraryFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        library_handler: LibraryHandler,
        on_tab_selected: Callable[[str], None],
        on_playlist_selected: Callable[[str], None],
        on_create_playlist: Callable[[], None],
    ):
        super().__init__(master, corner_radius=18)
        self.library_handler = library_handler
        self.on_tab_selected = on_tab_selected
        self.on_playlist_selected = on_playlist_selected
        self.on_create_playlist = on_create_playlist
        self.is_collapsed = False
        self.active_tab = "Biblioteca"
        self.active_playlist: str | None = None
        self.theme = get_theme(self.library_handler.get_settings().get("color_theme"))
        self.nav_buttons: dict[str, ctk.CTkButton] = {}
        self.playlist_buttons: list[ctk.CTkButton] = []
        self.playlist_button_map: dict[str, ctk.CTkButton] = {}

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1)

        self._build_ui()
        self.refresh_playlists()

    def _build_ui(self) -> None:
        self.header = ctk.CTkFrame(self, fg_color="transparent")
        self.header.grid(row=0, column=0, sticky="ew", padx=12, pady=(12, 8))
        self.header.grid_columnconfigure(0, weight=1)

        self.title_label = ctk.CTkLabel(self.header, text="Audio Hub", anchor="w", font=("Bahnschrift", 22, "bold"))
        self.title_label.grid(row=0, column=0, sticky="w")
        self.subtitle_label = ctk.CTkLabel(self.header, text="Biblioteca organizada e player espacial", anchor="w")
        self.subtitle_label.grid(row=1, column=0, sticky="w", pady=(2, 0))
        self.nav_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.nav_frame.grid(row=1, column=0, sticky="ew", padx=12, pady=8)
        self.nav_frame.grid_columnconfigure(0, weight=1)

        for row, tab_name in enumerate(("Biblioteca", "Playlists", "Recomendações", "Perfil do Usuário")):
            button = ctk.CTkButton(
                self.nav_frame,
                text=tab_name,
                anchor="w",
                command=lambda value=tab_name: self.on_tab_selected(value),
            )
            button.grid(row=row, column=0, sticky="ew", pady=4)
            self.nav_buttons[tab_name] = button

        self.playlists_frame = ctk.CTkFrame(self)
        self.playlists_frame.grid(row=2, column=0, sticky="nsew", padx=12, pady=(8, 12))
        self.playlists_frame.grid_columnconfigure(0, weight=1)
        self.playlists_frame.grid_rowconfigure(1, weight=1)

        self.playlists_label = ctk.CTkLabel(self.playlists_frame, text="Playlists", anchor="w", font=("Bahnschrift", 16, "bold"))
        self.playlists_label.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 6))
        self.create_playlist_button = ctk.CTkButton(self.playlists_frame, text="+", width=34, command=self.on_create_playlist)
        self.create_playlist_button.grid(row=0, column=1, sticky="e", padx=10, pady=(10, 6))

        self.playlists_list = ctk.CTkScrollableFrame(self.playlists_frame, fg_color="transparent")
        self.playlists_list.grid(row=1, column=0, columnspan=2, sticky="nsew", padx=4, pady=(0, 4))
        self.apply_theme(self.theme)

    def refresh_playlists(self) -> None:
        for button in self.playlist_buttons:
            button.destroy()
        self.playlist_buttons.clear()
        self.playlist_button_map.clear()

        for playlist_name in self.library_handler.get_all_playlists():
            button = ctk.CTkButton(
                self.playlists_list,
                text=playlist_name if not self.is_collapsed else playlist_name[:2].upper(),
                anchor="w",
                command=lambda value=playlist_name: self.on_playlist_selected(value),
            )
            button.pack(fill="x", padx=4, pady=4)
            self.playlist_buttons.append(button)
            self.playlist_button_map[playlist_name] = button

        self._update_selection_state()

    def apply_theme(self, theme: UITheme) -> None:
        self.theme = theme
        self.configure(fg_color=theme.panel, border_width=1, border_color=theme.border)
        self.playlists_frame.configure(fg_color=theme.surface, border_width=1, border_color=theme.border)
        self.title_label.configure(text_color=theme.text)
        self.subtitle_label.configure(text_color=theme.text_muted)
        self.playlists_label.configure(text_color=theme.text)
        self.create_playlist_button.configure(corner_radius=14, height=30, **button_tokens(theme, "secondary"))
        self.playlists_list.configure(fg_color="transparent")
        self._update_selection_state()

    def set_active_tab(self, tab_name: str) -> None:
        self.active_tab = tab_name
        self._update_selection_state()

    def set_active_playlist(self, playlist_name: str | None) -> None:
        self.active_playlist = playlist_name
        self._update_selection_state()

    def _update_selection_state(self) -> None:
        for tab_name, button in self.nav_buttons.items():
            variant = "selected" if tab_name == self.active_tab else "ghost"
            button.configure(anchor="w", corner_radius=14, height=36, **button_tokens(self.theme, variant))

        for playlist_name, button in self.playlist_button_map.items():
            variant = "selected" if playlist_name == self.active_playlist else "secondary"
            button.configure(anchor="w", corner_radius=12, height=32, **button_tokens(self.theme, variant))

    def set_collapsed(self, collapsed: bool) -> None:
        self.is_collapsed = collapsed
        self.title_label.configure(text="AH" if collapsed else "Audio Hub")
        self.subtitle_label.configure(text="" if collapsed else "Biblioteca organizada e player espacial")
        self.playlists_label.configure(text="PL" if collapsed else "Playlists")
        self.create_playlist_button.configure(text="+" if collapsed else "+")

        short_labels = {
            "Biblioteca": "Bib",
            "Playlists": "PL",
            "Recomendações": "Rec",
            "Perfil do Usuário": "Perfil",
        }
        for tab_name, button in self.nav_buttons.items():
            button.configure(text=short_labels[tab_name] if collapsed else tab_name)

        self.refresh_playlists()