from __future__ import annotations

import copy
import os
from collections import Counter, defaultdict
from datetime import datetime
from threading import Lock
from typing import Any, Optional

from .models import Track
from .storeHandler import StoreHandler
from .utils import make_track_from_file

class LibraryHandler:
    _io_lock = Lock()

    def __init__(self, storeHandler: Optional[StoreHandler] = None):
        self.handler = storeHandler or StoreHandler()
        self.library_data = self._load_library()
        self.track_index: dict[str, Track] = {}
        self.artist_index: dict[str, list[Track]] = {}
        self.album_index: dict[str, list[Track]] = {}
        self.genre_index: dict[str, list[Track]] = {}
        self.track_tree: dict[str, dict[str, list[Track]]] = {}
        self.index_tracks()

    @staticmethod
    def _default_settings() -> dict[str, Any]:
        return {
            "volume": 0.5,
            "last_playlist": None,
            "appearance_mode": "System",
            "color_theme": "blue",
            "spatial_balance": 0.0,
        }

    @classmethod
    def _empty_library(cls) -> dict[str, Any]:
        return {
            "tracks": [],
            "playlists": {},
            "history": [],
            "play_counts": {},
            "settings": cls._default_settings(),
        }

    def _normalize_track_entry(self, data: dict[str, Any], play_counts: Optional[dict[str, Any]] = None) -> Track:
        track = Track.from_dict(data)
        if not track.path:
            raise ValueError("Track entry requires a path")

        effective_play_counts = play_counts
        if effective_play_counts is None:
            effective_play_counts = getattr(self, "library_data", {}).get("play_counts", {})

        play_count = effective_play_counts.get(track.path)
        if play_count is not None:
            track.play_count = int(play_count)
        return track

    def _normalize_playlists(self, playlists: Any) -> dict[str, dict[str, Any]]:
        normalized: dict[str, dict[str, Any]] = {}
        if not isinstance(playlists, dict):
            return normalized

        for name, playlist in playlists.items():
            musics = playlist.get("musics", []) if isinstance(playlist, dict) else []
            normalized[str(name)] = {
                "musics": [
                    self._normalize_track_entry(item).to_dict()
                    for item in musics
                    if isinstance(item, dict)
                ],
                "created_at": (
                    playlist.get("created_at")
                    if isinstance(playlist, dict)
                    else datetime.utcnow().isoformat()
                ) or datetime.utcnow().isoformat(),
            }
        return normalized

    def _normalize_history(self, history: Any) -> list[dict[str, Any]]:
        if not isinstance(history, list):
            return []

        normalized: list[dict[str, Any]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            try:
                track = Track.from_dict(item)
                normalized.append(
                    {
                        **track.to_dict(),
                        "played_at": item.get("played_at") or datetime.utcnow().isoformat(),
                    }
                )
            except Exception:
                continue
        return normalized

    def _load_library(self) -> dict[str, Any]:
        with self._io_lock:
            loaded = self.handler._load_store() if hasattr(self.handler, "_load_store") else {}

        data = self._empty_library()
        if isinstance(loaded, dict):
            data.update({key: value for key, value in loaded.items() if key in data})

        settings = data.get("settings", {}) if isinstance(data.get("settings"), dict) else {}
        data["settings"] = {**self._default_settings(), **settings}
        data["play_counts"] = data.get("play_counts", {}) if isinstance(data.get("play_counts"), dict) else {}
        play_counts = data["play_counts"]
        data["playlists"] = self._normalize_playlists(data.get("playlists", {}))
        data["history"] = self._normalize_history(data.get("history", []))

        raw_tracks = data.get("tracks", []) if isinstance(data.get("tracks"), list) else []
        normalized_tracks: list[dict[str, Any]] = []
        for item in raw_tracks:
            if not isinstance(item, dict):
                continue
            try:
                normalized_tracks.append(self._normalize_track_entry(item, play_counts=play_counts).to_dict())
            except ValueError:
                continue

        if not normalized_tracks:
            seen_paths: set[str] = set()
            for playlist in data["playlists"].values():
                for item in playlist.get("musics", []):
                    path = str(item.get("path") or "")
                    if not path or path in seen_paths:
                        continue
                    normalized_tracks.append(Track.from_dict(item).to_dict())
                    seen_paths.add(path)

        data["tracks"] = normalized_tracks
        self.handler.store_data = copy.deepcopy(data)
        return data

    def _save_library(self) -> bool:
        try:
            serializable = {
                "tracks": [self._normalize_track_entry(track).to_dict() for track in self.library_data.get("tracks", [])],
                "playlists": self._normalize_playlists(self.library_data.get("playlists", {})),
                "history": self._normalize_history(self.library_data.get("history", [])),
                "play_counts": dict(self.library_data.get("play_counts", {})),
                "settings": {**self._default_settings(), **self.library_data.get("settings", {})},
            }
            with self._io_lock:
                self.handler.store_data = copy.deepcopy(serializable)
                return self.handler._save_store()
        except Exception as error:
            print(f"Erro ao salvar biblioteca: {error}")
            return False

    def index_tracks(self) -> None:
        self.track_index = {}
        artist_index: dict[str, list[Track]] = defaultdict(list)
        album_index: dict[str, list[Track]] = defaultdict(list)
        genre_index: dict[str, list[Track]] = defaultdict(list)
        tree: dict[str, dict[str, list[Track]]] = defaultdict(lambda: defaultdict(list))

        normalized_tracks: list[dict[str, Any]] = []
        for item in self.library_data.get("tracks", []):
            if not isinstance(item, dict):
                continue
            try:
                track = self._normalize_track_entry(item)
            except ValueError:
                continue

            normalized_tracks.append(track.to_dict())
            self.track_index[track.path] = track
            artist_index[track.artist.casefold()].append(track)
            album_index[track.album.casefold()].append(track)
            genre_index[track.genre.casefold()].append(track)
            tree[track.artist][track.album].append(track)

        self.library_data["tracks"] = normalized_tracks
        self.artist_index = dict(artist_index)
        self.album_index = dict(album_index)
        self.genre_index = dict(genre_index)
        self.track_tree = {artist: dict(albums) for artist, albums in tree.items()}

    def get_tracks(self) -> list[Track]:
        return list(self.track_index.values())

    def search(
        self,
        query: str = "",
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        favorites_only: bool = False,
    ) -> list[Track]:
        normalized_query = query.casefold().strip()
        tracks = self.get_tracks()

        def matches(track: Track) -> bool:
            if normalized_query:
                haystack = " ".join([track.title, track.artist, track.album, track.genre]).casefold()
                if normalized_query not in haystack:
                    return False
            if artist and track.artist.casefold() != artist.casefold():
                return False
            if album and track.album.casefold() != album.casefold():
                return False
            if genre and track.genre.casefold() != genre.casefold():
                return False
            if favorites_only and not track.is_favorite:
                return False
            return True

        return [track for track in tracks if matches(track)]

    def add_track(
        self,
        path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> Optional[Track]:
        if not path:
            return None

        base_track = make_track_from_file(path)
        track = Track(
            path=base_track.path,
            title=title or base_track.title,
            artist=artist or base_track.artist,
            album=album or base_track.album,
            genre=genre or base_track.genre,
            duration=base_track.duration,
            is_favorite=self.track_index.get(base_track.path, base_track).is_favorite if base_track.path in self.track_index else False,
            play_count=int(self.library_data.get("play_counts", {}).get(base_track.path, 0)),
        )

        existing_paths = {item.get("path") for item in self.library_data.get("tracks", []) if isinstance(item, dict)}
        if track.path in existing_paths:
            self.library_data["tracks"] = [
                track.to_dict() if item.get("path") == track.path else item
                for item in self.library_data.get("tracks", [])
                if isinstance(item, dict)
            ]
        else:
            self.library_data.setdefault("tracks", []).append(track.to_dict())

        self.index_tracks()
        self._save_library()
        return self.track_index.get(track.path)

    def update_track(self, path: str, **changes: Any) -> Optional[Track]:
        updated = None
        tracks = []
        for item in self.library_data.get("tracks", []):
            if not isinstance(item, dict):
                continue
            if item.get("path") == path:
                merged = {**item, **changes}
                updated = Track.from_dict(merged)
                tracks.append(updated.to_dict())
            else:
                tracks.append(item)
        self.library_data["tracks"] = tracks
        if updated is None:
            return None
        self.index_tracks()
        self._save_library()
        return self.track_index.get(path)

    def toggle_favorite(self, path: str) -> Optional[Track]:
        track = self.track_index.get(path)
        if track is None:
            return None
        return self.update_track(path, is_favorite=not track.is_favorite)

    def create_playlist(self, playlist_name: str) -> bool:
        if not playlist_name or playlist_name in self.library_data.get("playlists", {}):
            return False
        self.library_data.setdefault("playlists", {})[playlist_name] = {
            "musics": [],
            "created_at": datetime.utcnow().isoformat(),
        }
        return self._save_library()

    def add_music_to_playlist(
        self,
        playlist_name: str,
        music_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
    ) -> bool:
        if playlist_name not in self.library_data.get("playlists", {}):
            return False

        track = self.add_track(music_path, title=title, artist=artist, album=album, genre=genre)
        if track is None:
            return False

        playlist = self.library_data["playlists"][playlist_name]
        playlist.setdefault("musics", []).append(track.to_dict())
        return self._save_library()

    def remove_music_from_playlist(self, playlist_name: str, music_index: int) -> bool:
        playlist = self.library_data.get("playlists", {}).get(playlist_name)
        if not playlist:
            return False
        musics = playlist.get("musics", [])
        if not (0 <= music_index < len(musics)):
            return False
        musics.pop(music_index)
        return self._save_library()

    def reorder_music(self, playlist_name: str, old_index: int, new_index: int) -> bool:
        playlist = self.library_data.get("playlists", {}).get(playlist_name)
        if not playlist:
            return False
        musics = playlist.get("musics", [])
        if not (0 <= old_index < len(musics) and 0 <= new_index < len(musics)):
            return False
        track = musics.pop(old_index)
        musics.insert(new_index, track)
        return self._save_library()

    def get_playlist(self, playlist_name: str) -> Optional[dict[str, Any]]:
        playlist = self.library_data.get("playlists", {}).get(playlist_name)
        return copy.deepcopy(playlist) if playlist else None

    def get_all_playlists(self) -> list[str]:
        return list(self.library_data.get("playlists", {}).keys())

    def delete_playlist(self, playlist_name: str) -> bool:
        playlists = self.library_data.get("playlists", {})
        if playlist_name not in playlists:
            return False
        del playlists[playlist_name]
        return self._save_library()

    def get_playlist_musics(self, playlist_name: str) -> list[dict[str, Any]]:
        playlist = self.get_playlist(playlist_name)
        return playlist.get("musics", []) if playlist else []

    def get_available_artists(self) -> list[str]:
        return sorted({track.artist for track in self.get_tracks()})

    def get_available_albums(self) -> list[str]:
        return sorted({track.album for track in self.get_tracks()})

    def get_available_genres(self) -> list[str]:
        return sorted({track.genre for track in self.get_tracks()})

    def update_settings(self, **settings: Any) -> dict[str, Any]:
        self.library_data["settings"] = {
            **self._default_settings(),
            **self.library_data.get("settings", {}),
            **settings,
        }
        self._save_library()
        return copy.deepcopy(self.library_data["settings"])

    def get_settings(self) -> dict[str, Any]:
        return copy.deepcopy(self.library_data.get("settings", {}))

    def get_history(self) -> list[dict[str, Any]]:
        return copy.deepcopy(self.library_data.get("history", []))

    def record_play(self, track_path: str) -> Optional[Track]:
        track = self.track_index.get(track_path)
        if track is None:
            return None

        play_counts = self.library_data.setdefault("play_counts", {})
        play_counts[track_path] = int(play_counts.get(track_path, 0)) + 1
        self.library_data.setdefault("history", []).append(
            {
                **track.to_dict(),
                "played_at": datetime.utcnow().isoformat(),
            }
        )
        updated = self.update_track(track_path, play_count=play_counts[track_path])
        self._save_library()
        return updated

    def get_profile_metrics(self) -> dict[str, Any]:
        tracks = self.get_tracks()
        total_seconds = sum(track.duration * track.play_count for track in tracks if track.duration and track.play_count > 0)
        top_genres = Counter()
        for track in tracks:
            if track.play_count > 0:
                top_genres[track.genre] += track.play_count
        return {
            "total_hours_listened": round(total_seconds / 3600, 2),
            "favorite_tracks_count": sum(1 for track in tracks if track.is_favorite),
            "top_genres": top_genres.most_common(3),
            "tracks_count": len(tracks),
            "playlists_count": len(self.library_data.get("playlists", {})),
        }
