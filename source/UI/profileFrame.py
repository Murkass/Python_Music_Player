from __future__ import annotations

from typing import Callable, Optional

import customtkinter as ctk

from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler
from .style import UITheme, available_theme_names, get_theme, resolve_theme_name


class ProfileFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        library_handler: LibraryHandler,
        music_handler: MusicHandler,
        on_preferences_changed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.library_handler = library_handler
        self.music_handler = music_handler
        self.on_preferences_changed = on_preferences_changed
        self.theme = get_theme(self.library_handler.get_settings().get("color_theme"))

        self.grid_columnconfigure((0, 1, 2), weight=1)
        self.grid_rowconfigure(1, weight=1)

        self.metric_cards: dict[str, ctk.CTkLabel] = {}
        self.metric_frames: list[ctk.CTkFrame] = []
        self._build_metrics()
        self._build_preferences()
        self.refresh()

    def _build_metrics(self) -> None:
        self.metrics_frame = ctk.CTkFrame(self)
        self.metrics_frame.grid(row=0, column=0, columnspan=3, sticky="ew", padx=8, pady=(8, 12))
        self.metrics_frame.grid_columnconfigure((0, 1, 2), weight=1)

        for column, title in enumerate(("Horas Ouvidas", "Favoritas", "Faixas")):
            card = ctk.CTkFrame(self.metrics_frame, corner_radius=16)
            card.grid(row=0, column=column, sticky="nsew", padx=8, pady=8)
            self.metric_frames.append(card)
            ctk.CTkLabel(card, text=title, anchor="w", font=("Bahnschrift", 14, "bold")).pack(
                fill="x", padx=14, pady=(14, 6)
            )
            value_label = ctk.CTkLabel(card, text="0", anchor="w", font=("Bahnschrift", 28, "bold"))
            value_label.pack(fill="x", padx=14, pady=(0, 14))
            self.metric_cards[title] = value_label

        self.genre_label = ctk.CTkLabel(self.metrics_frame, text="Gêneros mais reproduzidos: -", anchor="w")
        self.genre_label.grid(row=1, column=0, columnspan=3, sticky="ew", padx=12, pady=(0, 12))

    def _build_preferences(self) -> None:
        self.settings_frame = ctk.CTkFrame(self)
        self.settings_frame.grid(row=1, column=0, columnspan=3, sticky="nsew", padx=8, pady=(0, 8))
        self.settings_frame.grid_columnconfigure(1, weight=1)

        self.appearance_label = ctk.CTkLabel(self.settings_frame, text="Modo de Aparência", anchor="w")
        self.appearance_label.grid(
            row=0, column=0, sticky="w", padx=14, pady=(14, 8)
        )
        self.appearance_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=["System", "Light", "Dark"],
            command=self._change_appearance_mode,
        )
        self.appearance_menu.grid(row=0, column=1, sticky="ew", padx=14, pady=(14, 8))

        self.theme_label = ctk.CTkLabel(self.settings_frame, text="Paleta Base", anchor="w")
        self.theme_label.grid(
            row=1, column=0, sticky="w", padx=14, pady=8
        )
        self.theme_menu = ctk.CTkOptionMenu(
            self.settings_frame,
            values=available_theme_names(),
            command=self._change_color_theme,
        )
        self.theme_menu.grid(row=1, column=1, sticky="ew", padx=14, pady=8)

        self.preferences_hint = ctk.CTkLabel(
            self.settings_frame,
            text="As preferências são persistidas imediatamente e aplicadas em runtime.",
            anchor="w",
        )
        self.preferences_hint.grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=14, pady=(8, 14)
        )

    def _change_appearance_mode(self, value: str) -> None:
        self.library_handler.update_settings(appearance_mode=value)
        ctk.set_appearance_mode(value)
        if self.on_preferences_changed is not None:
            self.on_preferences_changed()

    def _change_color_theme(self, value: str) -> None:
        resolved = resolve_theme_name(value)
        self.library_handler.update_settings(color_theme=resolved)
        self.theme = get_theme(resolved)
        self.apply_theme(self.theme)
        if self.on_preferences_changed is not None:
            self.on_preferences_changed()

    def apply_theme(self, theme: UITheme) -> None:
        self.theme = theme
        self.configure(fg_color="transparent")
        self.metrics_frame.configure(fg_color="transparent")
        self.settings_frame.configure(fg_color=theme.surface, border_width=1, border_color=theme.border)
        for frame in self.metric_frames:
            frame.configure(fg_color=theme.surface, border_width=1, border_color=theme.border)
        for label in self.metric_cards.values():
            label.configure(text_color=theme.text)
        self.genre_label.configure(text_color=theme.text_muted)
        self.appearance_label.configure(text_color=theme.text)
        self.theme_label.configure(text_color=theme.text)
        self.preferences_hint.configure(text_color=theme.text_muted)
        self.appearance_menu.configure(
            fg_color=theme.elevated,
            button_color=theme.accent,
            button_hover_color=theme.accent_hover,
            text_color=theme.text,
        )
        self.theme_menu.configure(
            fg_color=theme.elevated,
            button_color=theme.accent,
            button_hover_color=theme.accent_hover,
            text_color=theme.text,
        )

    def refresh(self) -> None:
        metrics = self.library_handler.get_profile_metrics()
        self.metric_cards["Horas Ouvidas"].configure(text=str(metrics.get("total_hours_listened", 0)))
        self.metric_cards["Favoritas"].configure(text=str(metrics.get("favorite_tracks_count", 0)))
        self.metric_cards["Faixas"].configure(text=str(metrics.get("tracks_count", 0)))
        genres = metrics.get("top_genres", [])
        formatted_genres = ", ".join(f"{genre} ({count})" for genre, count in genres) if genres else "-"
        self.genre_label.configure(text=f"Gêneros mais reproduzidos: {formatted_genres}")

        settings = self.library_handler.get_settings()
        self.theme = get_theme(settings.get("color_theme"))
        self.appearance_menu.set(settings.get("appearance_mode", "System"))
        self.theme_menu.set(resolve_theme_name(settings.get("color_theme")))
        self.apply_theme(self.theme)

    def handle_player_event(self, event: str, payload: dict) -> None:
        if event in {"track_changed", "track_updated", "play_next", "play_previous"}:
            self.refresh()