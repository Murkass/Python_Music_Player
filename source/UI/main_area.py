from __future__ import annotations

from pathlib import Path
from tkinter import filedialog
from typing import Callable, Optional

import customtkinter as ctk

from source.core.libraryHandler import LibraryHandler
from source.core.models import Track
from source.core.musicHandler import MusicHandler
from source.core.recommender import Recommender
from .profileFrame import ProfileFrame
from .style import UITheme, button_tokens, get_theme


class MainAreaFrame(ctk.CTkFrame):
    def __init__(
        self,
        master,
        music_handler: MusicHandler,
        library_handler: LibraryHandler,
        recommender: Recommender,
        on_preferences_changed: Optional[Callable[[], None]] = None,
    ):
        super().__init__(master, fg_color="transparent")
        self.handler = music_handler
        self.library = library_handler
        self.recommender = recommender
        self.on_preferences_changed = on_preferences_changed
        self.theme = get_theme(self.library.get_settings().get("color_theme"))
        self.selected_playlist: Optional[str] = None
        self.search_after_id = None
        self.current_library_results: list[Track] = []
        self.dragged_playlist_index: Optional[int] = None
        self.drag_source_row: ctk.CTkFrame | None = None
        self.drag_hover_row: ctk.CTkFrame | None = None

        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)
        self._build_ui()
        self.refresh_all()

    def _build_ui(self) -> None:
        self.tabview = ctk.CTkTabview(self)
        self.tabview.grid(row=0, column=0, sticky="nsew")

        for tab_name in ("Biblioteca", "Playlists", "Recomendações", "Perfil do Usuário"):
            self.tabview.add(tab_name)

        self._build_library_tab()
        self._build_playlists_tab()
        self._build_recommendations_tab()
        self.profile_frame = ProfileFrame(
            self.tabview.tab("Perfil do Usuário"),
            self.library,
            self.handler,
            on_preferences_changed=self._handle_preferences_changed,
        )
        self.profile_frame.pack(fill="both", expand=True, padx=4, pady=4)
        self.apply_theme(self.theme)

    def _handle_preferences_changed(self) -> None:
        self.refresh_all()
        if self.on_preferences_changed is not None:
            self.on_preferences_changed()

    def _build_library_tab(self) -> None:
        tab = self.tabview.tab("Biblioteca")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.library_tab = tab
        self.library_controls = ctk.CTkFrame(tab)
        self.library_controls.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.library_controls.grid_columnconfigure(0, weight=2)
        self.library_controls.grid_columnconfigure((1, 2, 3), weight=1)
        self.library_controls.grid_columnconfigure(4, weight=0)

        self.search_entry = ctk.CTkEntry(self.library_controls, placeholder_text="Buscar por faixa, artista, álbum ou gênero")
        self.search_entry.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.search_entry.bind("<KeyRelease>", self._schedule_library_refresh)

        self.artist_filter = ctk.CTkOptionMenu(self.library_controls, values=["Todos"], command=lambda _: self.refresh_library_tab())
        self.artist_filter.grid(row=0, column=1, sticky="ew", padx=8, pady=8)
        self.album_filter = ctk.CTkOptionMenu(self.library_controls, values=["Todos"], command=lambda _: self.refresh_library_tab())
        self.album_filter.grid(row=0, column=2, sticky="ew", padx=8, pady=8)
        self.genre_filter = ctk.CTkOptionMenu(self.library_controls, values=["Todos"], command=lambda _: self.refresh_library_tab())
        self.genre_filter.grid(row=0, column=3, sticky="ew", padx=8, pady=8)

        self.import_button = ctk.CTkButton(self.library_controls, text="+", width=34, command=self.prompt_import_tracks)
        self.import_button.grid(row=0, column=4, sticky="e", padx=(0, 8), pady=8)

        self.library_results = ctk.CTkScrollableFrame(tab)
        self.library_results.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _build_playlists_tab(self) -> None:
        tab = self.tabview.tab("Playlists")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.playlists_tab = tab
        self.playlists_header = ctk.CTkFrame(tab)
        self.playlists_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.playlists_header.grid_columnconfigure(0, weight=1)

        self.playlist_label = ctk.CTkLabel(self.playlists_header, text="Selecione uma playlist", anchor="w", font=("Bahnschrift", 18, "bold"))
        self.playlist_label.grid(row=0, column=0, sticky="w", padx=8, pady=8)
        self.play_playlist_button = ctk.CTkButton(self.playlists_header, text=">", width=34, command=self._play_selected_playlist)
        self.play_playlist_button.grid(row=0, column=1, sticky="e", padx=8, pady=8)
        self.add_playlist_track_button = ctk.CTkButton(self.playlists_header, text="+", width=34, command=self.prompt_add_tracks_to_playlist)
        self.add_playlist_track_button.grid(row=0, column=2, sticky="e", padx=8, pady=8)
        self.delete_playlist_button = ctk.CTkButton(self.playlists_header, text="-", width=34, command=self._delete_selected_playlist)
        self.delete_playlist_button.grid(row=0, column=3, sticky="e", padx=(0, 8), pady=8)

        self.playlist_results = ctk.CTkScrollableFrame(tab)
        self.playlist_results.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def _build_recommendations_tab(self) -> None:
        tab = self.tabview.tab("Recomendações")
        tab.grid_columnconfigure(0, weight=1)
        tab.grid_rowconfigure(1, weight=1)

        self.recommendations_tab = tab
        self.recommendations_header = ctk.CTkFrame(tab)
        self.recommendations_header.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        self.recommendations_header.grid_columnconfigure(0, weight=1)
        self.recommendations_label = ctk.CTkLabel(self.recommendations_header, text="Faixas Correlacionadas", anchor="w", font=("Bahnschrift", 18, "bold"))
        self.recommendations_label.grid(
            row=0, column=0, sticky="w", padx=8, pady=8
        )
        self.refresh_recommendations_button = ctk.CTkButton(self.recommendations_header, text="[]", width=40, command=self.refresh_recommendations_tab)
        self.refresh_recommendations_button.grid(
            row=0, column=1, sticky="e", padx=8, pady=8
        )

        self.recommendation_results = ctk.CTkScrollableFrame(tab)
        self.recommendation_results.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 8))

    def refresh_all(self) -> None:
        self.theme = get_theme(self.library.get_settings().get("color_theme"))
        self.apply_theme(self.theme)
        self._refresh_filter_values()
        self.refresh_library_tab()
        self.refresh_playlists_tab()
        self.refresh_recommendations_tab()
        self.profile_frame.refresh()

    def apply_theme(self, theme: UITheme) -> None:
        self.theme = theme
        self.configure(fg_color="transparent")
        self.tabview.configure(
            fg_color=theme.panel,
            segmented_button_fg_color=theme.surface,
            segmented_button_selected_color=theme.accent,
            segmented_button_selected_hover_color=theme.accent_hover,
            segmented_button_unselected_color=theme.elevated,
            segmented_button_unselected_hover_color=theme.accent_soft,
            text_color=theme.text,
            text_color_disabled=theme.text_muted,
            border_width=1,
            border_color=theme.border,
        )
        for frame in (self.library_controls, self.playlists_header, self.recommendations_header):
            frame.configure(fg_color=theme.surface, border_width=1, border_color=theme.border)
        for frame in (self.library_results, self.playlist_results, self.recommendation_results):
            frame.configure(fg_color=theme.panel, border_width=0)
        self.search_entry.configure(
            fg_color=theme.elevated,
            border_color=theme.border,
            text_color=theme.text,
            placeholder_text_color=theme.text_muted,
        )
        for option in (self.artist_filter, self.album_filter, self.genre_filter):
            option.configure(
                fg_color=theme.elevated,
                button_color=theme.accent,
                button_hover_color=theme.accent_hover,
                text_color=theme.text,
            )
        self.playlist_label.configure(text_color=theme.text)
        self.recommendations_label.configure(text_color=theme.text)
        self.import_button.configure(corner_radius=12, height=30, **button_tokens(theme, "secondary"))
        self.play_playlist_button.configure(corner_radius=12, height=30, **button_tokens(theme, "primary"))
        self.add_playlist_track_button.configure(corner_radius=12, height=30, **button_tokens(theme, "secondary"))
        self.delete_playlist_button.configure(corner_radius=12, height=30, **button_tokens(theme, "danger"))
        self.refresh_recommendations_button.configure(corner_radius=12, height=30, **button_tokens(theme, "ghost"))
        self.profile_frame.apply_theme(theme)

    def _refresh_filter_values(self) -> None:
        artists = ["Todos", *self.library.get_available_artists()]
        albums = ["Todos", *self.library.get_available_albums()]
        genres = ["Todos", *self.library.get_available_genres()]

        self.artist_filter.configure(values=artists)
        self.album_filter.configure(values=albums)
        self.genre_filter.configure(values=genres)

        if self.artist_filter.get() not in artists:
            self.artist_filter.set("Todos")
        if self.album_filter.get() not in albums:
            self.album_filter.set("Todos")
        if self.genre_filter.get() not in genres:
            self.genre_filter.set("Todos")

    def _schedule_library_refresh(self, _event=None) -> None:
        if self.search_after_id is not None:
            self.after_cancel(self.search_after_id)
        self.search_after_id = self.after(220, self.refresh_library_tab)

    def _clear_scrollable(self, frame: ctk.CTkScrollableFrame) -> None:
        for widget in list(frame.winfo_children()):
            widget.destroy()

    def _render_track_row(self, container: ctk.CTkScrollableFrame, track: Track, play_command, queue_command, extra_command=None, extra_text="Favoritar") -> None:
        row = ctk.CTkFrame(container, fg_color=self.theme.surface, border_width=1, border_color=self.theme.border, corner_radius=18)
        row.pack(fill="x", padx=4, pady=4)
        row.grid_columnconfigure(0, weight=1)

        title_label = ctk.CTkLabel(
            row,
            text=track.title,
            anchor="w",
            font=("Bahnschrift", 15, "bold"),
            text_color=self.theme.text,
        )
        title_label.grid(row=0, column=0, sticky="w", padx=10, pady=(8, 2))
        meta_label = ctk.CTkLabel(
            row,
            text=f"{track.artist} | {track.album} | {track.genre} | {Path(track.path).name}",
            anchor="w",
            justify="left",
            wraplength=640,
            text_color=self.theme.text_muted,
        )
        meta_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=1, rowspan=2, sticky="e", padx=10)
        play_button = ctk.CTkButton(actions, text=">", width=34, command=play_command)
        play_button.configure(corner_radius=12, height=32, **button_tokens(self.theme, "primary"))
        play_button.pack(side="left", padx=4)
        queue_button = ctk.CTkButton(actions, text="+Q", width=46, command=queue_command)
        queue_button.configure(corner_radius=12, height=32, **button_tokens(self.theme, "ghost"))
        queue_button.pack(side="left", padx=4)
        if extra_command is not None:
            compact_text = extra_text
            if "Favorito" in extra_text:
                compact_text = "**" if extra_text.startswith("Remover") else "*"
            elif extra_text == "Remover":
                compact_text = "-"
            extra_button = ctk.CTkButton(actions, text=compact_text, width=40, command=extra_command)
            variant = "danger" if extra_text == "Remover" else "secondary"
            extra_button.configure(corner_radius=12, height=32, **button_tokens(self.theme, variant))
            extra_button.pack(side="left", padx=4)

    def _highlight_drag_row(self, row: ctk.CTkFrame | None, active: bool) -> None:
        if row is None:
            return
        row.configure(border_color=self.theme.accent if active else self.theme.border, fg_color=self.theme.elevated if active else self.theme.surface)

    def _start_playlist_drag(self, index: int, row: ctk.CTkFrame) -> None:
        self.dragged_playlist_index = index
        self.drag_source_row = row
        self._highlight_drag_row(row, True)

    def _hover_playlist_drag(self, row: ctk.CTkFrame) -> None:
        if self.dragged_playlist_index is None:
            return
        if self.drag_hover_row is not None and self.drag_hover_row is not row and self.drag_hover_row is not self.drag_source_row:
            self._highlight_drag_row(self.drag_hover_row, False)
        self.drag_hover_row = row
        if row is not self.drag_source_row:
            self._highlight_drag_row(row, True)

    def _finish_playlist_drag(self, index: int) -> None:
        if self.selected_playlist is not None and self.dragged_playlist_index is not None and self.dragged_playlist_index != index:
            self.library.reorder_music(self.selected_playlist, self.dragged_playlist_index, index)
        if self.drag_source_row is not None:
            self._highlight_drag_row(self.drag_source_row, False)
        if self.drag_hover_row is not None:
            self._highlight_drag_row(self.drag_hover_row, False)
        self.dragged_playlist_index = None
        self.drag_source_row = None
        self.drag_hover_row = None
        self.refresh_playlists_tab()

    def _bind_playlist_drag(self, widget, index: int, row: ctk.CTkFrame) -> None:
        widget.bind("<ButtonPress-1>", lambda _event, value=index, target=row: self._start_playlist_drag(value, target))
        widget.bind("<Enter>", lambda _event, target=row: self._hover_playlist_drag(target))
        widget.bind("<ButtonRelease-1>", lambda _event, value=index: self._finish_playlist_drag(value))

    def _render_playlist_track_row(self, track: Track, index: int, tracks: list[Track]) -> None:
        row = ctk.CTkFrame(self.playlist_results, fg_color=self.theme.surface, border_width=1, border_color=self.theme.border, corner_radius=18)
        row.pack(fill="x", padx=4, pady=4)
        row.grid_columnconfigure(1, weight=1)

        handle = ctk.CTkLabel(row, text="::", width=22, anchor="center", text_color=self.theme.text_muted, font=("Consolas", 14, "bold"))
        handle.grid(row=0, column=0, rowspan=2, sticky="ns", padx=(10, 4))

        title = ctk.CTkLabel(row, text=track.title, anchor="w", font=("Bahnschrift", 15, "bold"), text_color=self.theme.text)
        title.grid(row=0, column=1, sticky="w", padx=6, pady=(8, 2))
        meta = ctk.CTkLabel(
            row,
            text=f"{track.artist} | {track.album} | {track.genre}",
            anchor="w",
            justify="left",
            text_color=self.theme.text_muted,
        )
        meta.grid(row=1, column=1, sticky="w", padx=6, pady=(0, 8))

        actions = ctk.CTkFrame(row, fg_color="transparent")
        actions.grid(row=0, column=2, rowspan=2, sticky="e", padx=10)

        play_button = ctk.CTkButton(actions, text=">", width=34, command=lambda value=index, values=tracks: self.handler.load_queue(values, start_index=value))
        play_button.configure(corner_radius=12, height=30, **button_tokens(self.theme, "primary"))
        play_button.pack(side="left", padx=4)
        queue_button = ctk.CTkButton(actions, text="+Q", width=46, command=lambda value=track: self.handler.enqueue_track(value))
        queue_button.configure(corner_radius=12, height=30, **button_tokens(self.theme, "ghost"))
        queue_button.pack(side="left", padx=4)
        remove_button = ctk.CTkButton(actions, text="-", width=34, command=lambda value=index: self._remove_from_selected_playlist(value))
        remove_button.configure(corner_radius=12, height=30, **button_tokens(self.theme, "danger"))
        remove_button.pack(side="left", padx=4)

        for widget in (row, handle, title, meta):
            self._bind_playlist_drag(widget, index, row)

    def prompt_import_tracks(self) -> None:
        selected_paths = filedialog.askopenfilenames(
            title="Importar músicas",
            filetypes=[("Áudio", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("Todos", "*.*")],
        )
        if not selected_paths:
            return
        for path in selected_paths:
            self.library.add_track(path)
        self.refresh_all()

    def prompt_add_tracks_to_playlist(self) -> None:
        if not self.selected_playlist:
            return
        selected_paths = filedialog.askopenfilenames(
            title="Adicionar músicas à playlist",
            filetypes=[("Áudio", "*.mp3 *.wav *.flac *.ogg *.m4a"), ("Todos", "*.*")],
        )
        if not selected_paths:
            return
        for path in selected_paths:
            self.library.add_music_to_playlist(self.selected_playlist, path)
        self.refresh_all()

    def refresh_library_tab(self) -> None:
        query = self.search_entry.get().strip() if hasattr(self, "search_entry") else ""
        artist = None if self.artist_filter.get() == "Todos" else self.artist_filter.get()
        album = None if self.album_filter.get() == "Todos" else self.album_filter.get()
        genre = None if self.genre_filter.get() == "Todos" else self.genre_filter.get()
        self.current_library_results = self.library.search(query=query, artist=artist, album=album, genre=genre)

        self._clear_scrollable(self.library_results)
        if not self.current_library_results:
            ctk.CTkLabel(self.library_results, text="Nenhuma faixa encontrada.", anchor="w").pack(fill="x", padx=8, pady=8)
            return

        for index, track in enumerate(self.current_library_results):
            self._render_track_row(
                self.library_results,
                track,
                play_command=lambda value=index: self.handler.load_queue(self.current_library_results, start_index=value),
                queue_command=lambda value=track: self.handler.enqueue_track(value),
                extra_command=lambda value=track.path: self._toggle_favorite(value),
                extra_text="Remover Favorito" if track.is_favorite else "Favoritar",
            )

    def refresh_playlists_tab(self) -> None:
        self._clear_scrollable(self.playlist_results)
        if not self.selected_playlist:
            playlists = self.library.get_all_playlists()
            self.selected_playlist = playlists[0] if playlists else None

        if not self.selected_playlist:
            self.playlist_label.configure(text="Selecione uma playlist")
            ctk.CTkLabel(self.playlist_results, text="Nenhuma playlist disponível.", anchor="w").pack(fill="x", padx=8, pady=8)
            return

        playlist = self.library.get_playlist(self.selected_playlist)
        if playlist is None:
            self.selected_playlist = None
            self.refresh_playlists_tab()
            return

        self.playlist_label.configure(text=f"Playlist: {self.selected_playlist}")
        tracks = [Track.from_dict(item) for item in playlist.get("musics", [])]
        if not tracks:
            ctk.CTkLabel(self.playlist_results, text="Playlist vazia.", anchor="w").pack(fill="x", padx=8, pady=8)
            return

        for index, track in enumerate(tracks):
            self._render_playlist_track_row(track, index, tracks)

    def refresh_recommendations_tab(self) -> None:
        self.recommender.rebuild()
        self._clear_scrollable(self.recommendation_results)
        current_path = self.handler.currentPlaying.path if self.handler.currentPlaying else None
        recommendations = self.recommender.recommend(current_path) if current_path else self.recommender.recommend_from_recent_history()
        if not recommendations:
            ctk.CTkLabel(self.recommendation_results, text="Ainda não há correlações suficientes no histórico.", anchor="w").pack(
                fill="x", padx=8, pady=8
            )
            return

        for index, track in enumerate(recommendations):
            self._render_track_row(
                self.recommendation_results,
                track,
                play_command=lambda value=index, values=recommendations: self.handler.load_queue(values, start_index=value),
                queue_command=lambda value=track: self.handler.enqueue_track(value),
            )

    def _toggle_favorite(self, track_path: str) -> None:
        self.library.toggle_favorite(track_path)
        self.handler.sync_current_track_from_library()
        self.handler.broadcast_state("track_updated")
        self.refresh_library_tab()
        self.refresh_playlists_tab()
        self.profile_frame.refresh()

    def prompt_create_playlist(self) -> None:
        dialog = ctk.CTkInputDialog(text="Nome da playlist", title="Criar Playlist")
        name = dialog.get_input()
        if not name:
            return
        self.library.create_playlist(name)
        self.selected_playlist = name
        if hasattr(self.master, "libraryFrame"):
            self.master.libraryFrame.refresh_playlists()
            self.master.libraryFrame.set_active_playlist(name)
        self.refresh_playlists_tab()

    def select_playlist(self, playlist_name: str) -> None:
        self.selected_playlist = playlist_name
        self.library.update_settings(last_playlist=playlist_name)
        self.show_tab("Playlists")
        if hasattr(self.master, "libraryFrame"):
            self.master.libraryFrame.set_active_playlist(playlist_name)
        self.refresh_playlists_tab()

    def show_tab(self, tab_name: str) -> None:
        self.tabview.set(tab_name)

    def _play_selected_playlist(self) -> None:
        if not self.selected_playlist:
            return
        playlist = self.library.get_playlist(self.selected_playlist)
        if playlist is None:
            return
        self.handler.selectPlaylist(playlist)

    def _remove_from_selected_playlist(self, index: int) -> None:
        if not self.selected_playlist:
            return
        self.library.remove_music_from_playlist(self.selected_playlist, index)
        self.refresh_playlists_tab()

    def _delete_selected_playlist(self) -> None:
        if not self.selected_playlist:
            return
        self.library.delete_playlist(self.selected_playlist)
        self.selected_playlist = None
        if hasattr(self.master, "libraryFrame"):
            self.master.libraryFrame.refresh_playlists()
            self.master.libraryFrame.set_active_playlist(None)
        self.refresh_playlists_tab()

    def handle_player_event(self, event: str, payload: dict) -> None:
        if event in {"track_changed", "track_updated", "play_next", "play_previous"}:
            self.refresh_recommendations_tab()
            self.profile_frame.refresh()
