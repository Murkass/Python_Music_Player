from __future__ import annotations

import customtkinter as ctk

from source.core.musicHandler import MusicHandler
from .style import UITheme, button_tokens, get_theme


class PlayingQueueFrame(ctk.CTkScrollableFrame):
    def __init__(self, master, music_handler: MusicHandler):
        super().__init__(master, corner_radius=18)
        self.handler = music_handler
        self.theme = get_theme(getattr(getattr(master, "library_handler", None), "get_settings", lambda: {"color_theme": "Oceano"})().get("color_theme"))
        self.refresh()

    def _render_section_title(self, text: str) -> None:
        ctk.CTkLabel(self, text=text, anchor="w", font=("Bahnschrift", 14, "bold"), text_color=self.theme.text).pack(
            fill="x", padx=8, pady=(10, 6)
        )

    def refresh(self) -> None:
        self.configure(fg_color=self.theme.panel, border_width=1, border_color=self.theme.border)
        for widget in list(self.winfo_children()):
            widget.destroy()

        self._render_section_title("Tocando Agora")
        current = self.handler.currentPlaying
        if current is None:
            ctk.CTkLabel(self, text="Nenhuma faixa em reprodução.", anchor="w", text_color=self.theme.text_muted).pack(fill="x", padx=8, pady=(0, 10))
        else:
            ctk.CTkLabel(
                self,
                text=f"{current.title} - {current.artist}",
                anchor="w",
                justify="left",
                wraplength=220,
                text_color=self.theme.text,
            ).pack(fill="x", padx=8, pady=(0, 10))

        self._render_section_title("Histórico")
        history = list(self.handler.historic)[:5]
        if not history:
            ctk.CTkLabel(self, text="Sem histórico recente.", anchor="w", text_color=self.theme.text_muted).pack(fill="x", padx=8, pady=(0, 10))
        else:
            for track in history:
                ctk.CTkLabel(self, text=f"{track.title} - {track.artist}", anchor="w", justify="left", text_color=self.theme.text).pack(
                    fill="x", padx=8, pady=3
                )

        self._render_section_title("Próximas")
        queue = self.handler.get_queue()
        if not queue:
            ctk.CTkLabel(self, text="Fila vazia.", anchor="w", text_color=self.theme.text_muted).pack(fill="x", padx=8, pady=(0, 10))
        else:
            for index, track in enumerate(queue):
                button = ctk.CTkButton(
                    self,
                    text=f"{index + 1}. {track.title}",
                    anchor="w",
                    command=lambda value=index: self.handler.selectTrack(value),
                )
                button.configure(corner_radius=12, height=32, **button_tokens(self.theme, "ghost"))
                button.pack(fill="x", padx=8, pady=4)

    def apply_theme(self, theme: UITheme) -> None:
        self.theme = theme
        self.refresh()

    def handle_player_event(self, event: str, payload: dict) -> None:
        if event in {"track_changed", "queue_updated", "queue_cleared", "play_next", "play_previous", "track_updated"}:
            self.refresh()