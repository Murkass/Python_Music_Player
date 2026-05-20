from __future__ import annotations

import customtkinter as ctk

from source.core.libraryHandler import LibraryHandler
from source.core.musicHandler import MusicHandler
from .style import UITheme, button_tokens, get_theme


class CurrentPlayingFrame(ctk.CTkFrame):
    def __init__(self, master, musicHandler: MusicHandler, library_handler: LibraryHandler):
        super().__init__(master, corner_radius=18)
        self.handler = musicHandler
        self.library_handler = library_handler
        self.theme = get_theme(self.library_handler.get_settings().get("color_theme"))

        self.grid_columnconfigure(0, weight=2)
        self.grid_columnconfigure(1, weight=3)
        self.grid_columnconfigure(2, weight=2)

        self.track_title = ctk.CTkLabel(self, text="Nenhuma faixa em reprodução", anchor="w", font=("Bahnschrift", 20, "bold"))
        self.track_title.grid(row=0, column=0, sticky="ew", padx=14, pady=(12, 2))

        self.track_meta = ctk.CTkLabel(self, text="", anchor="w")
        self.track_meta.grid(row=1, column=0, sticky="ew", padx=14, pady=(0, 12))

        self.controls = ctk.CTkFrame(self, fg_color="transparent")
        self.controls.grid(row=0, column=1, rowspan=2, sticky="n", pady=12)

        self.prev_button = ctk.CTkButton(self.controls, text="<<", width=40, command=self.handler.playPrevious)
        self.prev_button.pack(side="left", padx=6)
        self.play_button = ctk.CTkButton(self.controls, text=">", width=40, command=self.handler.playPause)
        self.play_button.pack(side="left", padx=6)
        self.next_button = ctk.CTkButton(self.controls, text=">>", width=40, command=self.handler.playNext)
        self.next_button.pack(side="left", padx=6)

        self.side_controls = ctk.CTkFrame(self, fg_color="transparent")
        self.side_controls.grid(row=0, column=2, rowspan=2, sticky="e", padx=14, pady=12)

        self.favorite_button = ctk.CTkButton(self.side_controls, text="*", width=40, command=self._toggle_favorite)
        self.favorite_button.pack(anchor="e", pady=(0, 8))

        self.time_label = ctk.CTkLabel(self.side_controls, text="0:00 / 0:00", anchor="e")
        self.time_label.pack(anchor="e")

        self.progress = ctk.CTkProgressBar(self)
        self.progress.grid(row=2, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 10))
        self.progress.set(0)

        self.sliders = ctk.CTkFrame(self, fg_color="transparent")
        self.sliders.grid(row=3, column=0, columnspan=3, sticky="ew", padx=14, pady=(0, 14))
        self.sliders.grid_columnconfigure((1, 3), weight=1)

        self.volume_label = ctk.CTkLabel(self.sliders, text="Volume")
        self.volume_label.grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.volume_slider = ctk.CTkSlider(self.sliders, from_=0, to=1, command=self.handler.setVol)
        self.volume_slider.grid(row=0, column=1, sticky="ew", padx=(0, 16))

        self.balance_label = ctk.CTkLabel(self.sliders, text="Balanço Espacial")
        self.balance_label.grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.balance_slider = ctk.CTkSlider(self.sliders, from_=-1, to=1, command=self.handler.update_spatial_balance)
        self.balance_slider.grid(row=0, column=3, sticky="ew")

        self.bind("<Motion>", self._handle_pointer_motion)
        self.volume_slider.set(self.handler.getVol())
        self.balance_slider.set(self.handler.get_spatial_state()["balance"])
        self.apply_theme(self.theme)
        self._sync_from_handler()

    def apply_theme(self, theme: UITheme) -> None:
        self.theme = theme
        self.configure(fg_color=theme.surface, border_width=1, border_color=theme.border)
        self.track_title.configure(text_color=theme.text)
        self.track_meta.configure(text_color=theme.text_muted)
        self.time_label.configure(text_color=theme.text_muted)
        self.volume_label.configure(text_color=theme.text)
        self.balance_label.configure(text_color=theme.text)
        self.prev_button.configure(corner_radius=14, height=32, **button_tokens(theme, "ghost"))
        self.play_button.configure(corner_radius=14, height=32, **button_tokens(theme, "selected"))
        self.next_button.configure(corner_radius=14, height=32, **button_tokens(theme, "ghost"))
        self.favorite_button.configure(corner_radius=14, height=32, **button_tokens(theme, "secondary"))
        self.progress.configure(progress_color=theme.accent, fg_color=theme.accent_soft)
        self.volume_slider.configure(progress_color=theme.accent, button_color=theme.accent, button_hover_color=theme.accent_hover)
        self.balance_slider.configure(progress_color=theme.accent, button_color=theme.accent, button_hover_color=theme.accent_hover)

    def _format_time(self, seconds: float) -> str:
        total_seconds = max(0, int(seconds))
        minutes, remainder = divmod(total_seconds, 60)
        return f"{minutes}:{remainder:02d}"

    def _handle_pointer_motion(self, event) -> None:
        self.handler.update_sound_parallax_from_pointer(event.x, max(self.winfo_width(), 1))

    def _toggle_favorite(self) -> None:
        current = self.handler.currentPlaying
        if current is None:
            return
        updated = self.library_handler.toggle_favorite(current.path)
        if updated is None:
            return
        self.handler.sync_current_track_from_library()
        self.handler.broadcast_state("track_updated")
        self._sync_from_handler()

    def _sync_from_handler(self) -> None:
        track = self.handler.currentPlaying
        if track is None:
            self.track_title.configure(text="Nenhuma faixa em reprodução")
            self.track_meta.configure(text="")
            self.favorite_button.configure(text="*")
            self.time_label.configure(text="0:00 / 0:00")
            self.play_button.configure(text=">")
            self.progress.set(0)
            return

        self.track_title.configure(text=track.title)
        self.track_meta.configure(text=f"{track.artist} | {track.album} | {track.genre}")
        favorite_variant = "danger" if track.is_favorite else "secondary"
        self.favorite_button.configure(text="**" if track.is_favorite else "*", **button_tokens(self.theme, favorite_variant))
        self.play_button.configure(text=">" if self.handler.paused else "||")
        self.volume_slider.set(self.handler.getVol())
        self.balance_slider.set(self.handler.get_spatial_state()["balance"])

        position = self.handler.getCurrentPosition()
        duration = track.duration
        progress = min(1.0, position / duration) if duration > 0 else 0.0
        self.progress.set(progress)
        self.time_label.configure(text=f"{self._format_time(position)} / {self._format_time(duration)}")

    def handle_player_event(self, event: str, payload: dict) -> None:
        if event in {"track_changed", "play_pause", "position_update", "track_updated", "spatial_update", "volume_changed"}:
            self._sync_from_handler()

    
