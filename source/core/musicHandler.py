from __future__ import annotations

import math
from collections import deque
from threading import Event, Lock, Thread
from time import monotonic
from typing import Any, Optional, Protocol

import numpy as np
import pygame.mixer as mixer
import soundfile as sf

from .libraryHandler import LibraryHandler
from .models import Track
from .storeHandler import StoreHandler
from .utils import make_track_from_file


class AudioBackend(Protocol):
    def load(self, path: str) -> None: ...
    def play(self) -> None: ...
    def pause(self) -> None: ...
    def unpause(self) -> None: ...
    def stop(self) -> None: ...
    def set_volume(self, volume: float) -> None: ...
    def get_volume(self) -> float: ...
    def get_pos(self) -> int: ...
    def set_stereo_volume(self, left: float, right: float) -> None: ...


class SilentAudioBackend:
    def __init__(self) -> None:
        self._volume = 0.5
        self._position_ms = 0
        self._stereo = (1.0, 1.0)

    def load(self, path: str) -> None:
        self._position_ms = 0

    def play(self) -> None:
        self._position_ms = 0

    def pause(self) -> None:
        return None

    def unpause(self) -> None:
        return None

    def stop(self) -> None:
        self._position_ms = 0

    def set_volume(self, volume: float) -> None:
        self._volume = float(volume)

    def get_volume(self) -> float:
        return self._volume

    def get_pos(self) -> int:
        return self._position_ms

    def set_stereo_volume(self, left: float, right: float) -> None:
        self._stereo = (left, right)


class PygameAudioBackend:
    def __init__(self) -> None:
        mixer.init()
        mixer.music.set_volume(0.5)

    def load(self, path: str) -> None:
        mixer.music.load(path)

    def play(self) -> None:
        mixer.music.play()

    def pause(self) -> None:
        mixer.music.pause()

    def unpause(self) -> None:
        mixer.music.unpause()

    def stop(self) -> None:
        mixer.music.stop()

    def set_volume(self, volume: float) -> None:
        mixer.music.set_volume(volume)

    def get_volume(self) -> float:
        return mixer.music.get_volume()

    def get_pos(self) -> int:
        return mixer.music.get_pos()

    def set_stereo_volume(self, left: float, right: float) -> None:
        mixer.music.set_volume((left + right) / 2)


class MusicHandler:
    def __init__(
        self,
        storeHandler: StoreHandler,
        library_handler: Optional[LibraryHandler] = None,
        audio_backend: Optional[AudioBackend] = None,
        poll_interval: float = 0.25,
        auto_start_monitor: bool = True,
    ):
        self.storeHandler = storeHandler
        self.library_handler = library_handler
        self.currentPlaying: Optional[Track] = None
        self.playingQueue: deque[Track] = deque()
        self.historic: deque[Track] = deque(maxlen=100)
        self._listeners: set[Any] = set()
        self._lock = Lock()
        self._listener_lock = Lock()
        self._monitor_stop = Event()
        self._monitor_thread: Optional[Thread] = None
        self._last_position_push = -1.0
        self._last_position_ts = monotonic()
        self.poll_interval = poll_interval
        self.paused = False
        self.left_gain = 1.0
        self.right_gain = 1.0

        settings = self.library_handler.get_settings() if self.library_handler else {}
        self.spatial_balance = float(settings.get("spatial_balance", 0.0))

        self.audio_backend = audio_backend or self._build_audio_backend()
        self.audio_backend.set_volume(float(settings.get("volume", 0.5)))
        self._load_historic()
        self._apply_spatial_state(self.spatial_balance, smoothing=1.0)

        if auto_start_monitor:
            self._start_monitor()

    def _build_audio_backend(self) -> AudioBackend:
        try:
            return PygameAudioBackend()
        except Exception:
            return SilentAudioBackend()

    def _load_historic(self) -> None:
        history = []
        if self.library_handler is not None:
            history = self.library_handler.get_history()
        else:
            history = getattr(self.storeHandler, "store_data", {}).get("history", []) or []

        tracks: list[Track] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            path = item.get("path") or item.get("filePath")
            if not path:
                continue
            tracks.append(Track.from_dict(item))
        self.historic = deque(reversed(tracks), maxlen=100)

    def _track_duration_label(self, track: Track) -> str:
        total_seconds = max(0, int(round(track.duration)))
        minutes, seconds = divmod(total_seconds, 60)
        return f"{minutes}:{seconds:02d}"

    def _track_payload(self, track: Optional[Track]) -> Optional[dict[str, Any]]:
        if track is None:
            return None
        return {
            **track.to_dict(),
            "time": self._track_duration_label(track),
        }

    def _queue_payload(self) -> list[dict[str, Any]]:
        payload = []
        for track in self.playingQueue:
            item = self._track_payload(track)
            if item is not None:
                payload.append(item)
        return payload

    def _history_payload(self) -> list[dict[str, Any]]:
        payload = []
        for track in self.historic:
            item = self._track_payload(track)
            if item is not None:
                payload.append(item)
        return payload

    def _current_event_payload(self) -> dict[str, Any]:
        position = self.getCurrentPosition()
        duration = self.currentPlaying.duration if self.currentPlaying else 0.0
        return {
            "track": self._track_payload(self.currentPlaying),
            "queue": self._queue_payload(),
            "history": self._history_payload(),
            "paused": self.paused,
            "position": position,
            "duration": duration,
            "progress": min(1.0, position / duration) if duration > 0 else 0.0,
            "spatial": self.get_spatial_state(),
        }

    def add_listener(self, listener: Any) -> None:
        with self._listener_lock:
            self._listeners.add(listener)

    def remove_listener(self, listener: Any) -> None:
        with self._listener_lock:
            self._listeners.discard(listener)

    def notify(self, event: str, payload: dict[str, Any]) -> None:
        with self._listener_lock:
            listeners = list(self._listeners)

        for listener in listeners:
            try:
                if hasattr(listener, "handle_player_event"):
                    listener.handle_player_event(event, payload)
                elif callable(listener):
                    listener(event, payload)
            except Exception:
                continue

    def broadcast_state(self, event: str = "state_updated") -> None:
        self.notify(event, self._current_event_payload())

    def sync_current_track_from_library(self) -> Optional[Track]:
        if self.currentPlaying is None or self.library_handler is None:
            return self.currentPlaying
        updated = self.library_handler.track_index.get(self.currentPlaying.path)
        if updated is not None:
            self.currentPlaying = updated
        return self.currentPlaying

    def _start_monitor(self) -> None:
        if self._monitor_thread and self._monitor_thread.is_alive():
            return
        self._monitor_stop.clear()
        self._monitor_thread = Thread(target=self._monitor_position, daemon=True)
        self._monitor_thread.start()

    def _monitor_position(self) -> None:
        while not self._monitor_stop.wait(self.poll_interval):
            if self.currentPlaying is None or self.paused:
                continue

            payload = self._current_event_payload()
            position = float(payload["position"])
            if math.isclose(position, self._last_position_push, abs_tol=0.02):
                continue

            self._last_position_push = position
            self.notify("position_update", payload)

    def shutdown(self) -> None:
        self._monitor_stop.set()
        if self._monitor_thread and self._monitor_thread.is_alive():
            self._monitor_thread.join(timeout=1.0)

    def enqueue_track(self, track: Track, auto_play: bool = False) -> Track:
        with self._lock:
            self.playingQueue.append(track)
        self.notify("queue_updated", self._current_event_payload())
        if auto_play and self.currentPlaying is None:
            self.playNext()
        return track

    def add_to_queue(
        self,
        file_path: str,
        title: Optional[str] = None,
        artist: Optional[str] = None,
        album: Optional[str] = None,
        genre: Optional[str] = None,
        auto_play: bool = True,
    ) -> Optional[Track]:
        if not file_path:
            return None

        if self.library_handler is not None:
            track = self.library_handler.add_track(
                file_path,
                title=title,
                artist=artist,
                album=album,
                genre=genre,
            )
        else:
            base = make_track_from_file(file_path)
            track = Track(
                path=base.path,
                title=title or base.title,
                artist=artist or base.artist,
                album=album or base.album,
                genre=genre or base.genre,
                duration=base.duration,
            )

        if track is None:
            return None
        return self.enqueue_track(track, auto_play=auto_play)

    def addToQueue(self, _filePath, _title, _artist):
        return self.add_to_queue(_filePath, title=_title, artist=_artist)

    def load_queue(self, tracks: list[Track], start_index: int = 0) -> Optional[dict[str, Any]]:
        with self._lock:
            self.playingQueue = deque(tracks)
            self.currentPlaying = None
        self.notify("queue_updated", self._current_event_payload())
        return self.selectTrack(start_index)

    def clearQueue(self):
        with self._lock:
            self.playingQueue.clear()
            self.historic.clear()
            self.currentPlaying = None
        self.paused = False
        self.audio_backend.stop()
        self.notify("queue_cleared", self._current_event_payload())

    def selectPlaylist(self, playlistObj):
        playlist_tracks = []
        for music in playlistObj.get("musics", []):
            if not isinstance(music, dict):
                continue
            playlist_tracks.append(Track.from_dict(music))
        if not playlist_tracks:
            self.clearQueue()
            return None
        return self.load_queue(playlist_tracks, start_index=0)

    def get_queue(self) -> list[Track]:
        return list(self.playingQueue)

    def getCurrentTrackInfo(self):
        if self.currentPlaying is None:
            return None
        payload = self._track_payload(self.currentPlaying) or {}
        return {
            "title": payload.get("title", "Unknown Title"),
            "artist": payload.get("artist", "Unknown Artist"),
            "time": payload.get("time", "0:00"),
            "album": payload.get("album", "Unknown Album"),
            "genre": payload.get("genre", "Unknown Genre"),
            "is_favorite": payload.get("is_favorite", False),
        }

    def _activate_track(self, track: Track, event_name: str, push_current: bool = True) -> Optional[dict[str, Any]]:
        with self._lock:
            if push_current and self.currentPlaying is not None:
                self.historic.appendleft(self.currentPlaying)
            self.currentPlaying = track
            self.paused = False
            self._last_position_push = -1.0
            self._last_position_ts = monotonic()

        try:
            self.audio_backend.load(track.path)
            self.audio_backend.play()
        except Exception:
            return None

        if self.library_handler is not None:
            updated = self.library_handler.record_play(track.path)
            if updated is not None:
                self.currentPlaying = updated
                track = updated

        self.notify("track_changed", self._current_event_payload())
        self.notify(event_name, self._current_event_payload())
        self.notify("queue_updated", self._current_event_payload())
        return self.getCurrentTrackInfo()

    def playNext(self):
        with self._lock:
            if not self.playingQueue:
                return None
            track = self.playingQueue.popleft()
        return self._activate_track(track, "play_next")

    def playPrevious(self):
        with self._lock:
            if not self.historic:
                return None
            if self.currentPlaying is not None:
                self.playingQueue.appendleft(self.currentPlaying)
            track = self.historic.popleft()
        return self._activate_track(track, "play_previous", push_current=False)

    def playPause(self):
        if self.currentPlaying is None:
            return None
        try:
            if self.paused:
                self.audio_backend.unpause()
                self.paused = False
            else:
                self.audio_backend.pause()
                self.paused = True
        except Exception:
            return None
        payload = self._current_event_payload()
        self.notify("play_pause", payload)
        return payload

    def selectTrack(self, index):
        with self._lock:
            if not (0 <= index < len(self.playingQueue)):
                return None
            queue_list = list(self.playingQueue)
            track = queue_list.pop(index)
            self.playingQueue = deque(queue_list)
        return self._activate_track(track, "select_track")

    def setVol(self, volume):
        clamped = max(0.0, min(float(volume), 1.0))
        self.audio_backend.set_volume(clamped)
        if self.library_handler is not None:
            self.library_handler.update_settings(volume=clamped)
        payload = self._current_event_payload()
        payload["volume"] = clamped
        self.notify("volume_changed", payload)
        return clamped

    def getVol(self):
        return float(self.audio_backend.get_volume())

    def getCurrentPosition(self):
        try:
            pos_ms = self.audio_backend.get_pos()
        except Exception:
            return 0.0
        if pos_ms is None or pos_ms < 0:
            return 0.0
        return float(pos_ms) / 1000.0

    def _apply_spatial_state(self, balance: float, smoothing: float = 0.18) -> dict[str, float]:
        pan = max(-1.0, min(balance, 1.0))
        angle = (pan + 1.0) * math.pi / 4.0
        target_left = math.cos(angle)
        target_right = math.sin(angle)
        alpha = max(0.0, min(smoothing, 1.0))
        self.left_gain += (target_left - self.left_gain) * alpha
        self.right_gain += (target_right - self.right_gain) * alpha
        try:
            self.audio_backend.set_stereo_volume(self.left_gain, self.right_gain)
        except Exception:
            pass
        return {
            "balance": pan,
            "left_gain": self.left_gain,
            "right_gain": self.right_gain,
        }

    def update_spatial_balance(self, balance: float) -> dict[str, float]:
        self.spatial_balance = max(-1.0, min(float(balance), 1.0))
        if self.library_handler is not None:
            self.library_handler.update_settings(spatial_balance=self.spatial_balance)
        payload = self._apply_spatial_state(self.spatial_balance)
        self.notify("spatial_update", {**self._current_event_payload(), "spatial": payload})
        return payload

    def update_sound_parallax_from_pointer(self, x_position: float, width: float) -> dict[str, float]:
        if width <= 0:
            return self.get_spatial_state()
        balance = ((x_position / width) * 2.0) - 1.0
        return self.update_spatial_balance(balance)

    def get_spatial_state(self) -> dict[str, float]:
        return {
            "balance": self.spatial_balance,
            "left_gain": self.left_gain,
            "right_gain": self.right_gain,
        }

    def getSpectrumData(self, filePath, window_ms: int = 200):
        try:
            info = sf.info(filePath)
            samplerate = info.samplerate
            pos_ms = self.audio_backend.get_pos()
            if pos_ms is None or pos_ms < 0:
                pos_ms = 0

            start_ms = max(0, int(pos_ms - window_ms // 2))
            start_frame = int(start_ms * samplerate / 1000)
            frames = int(window_ms * samplerate / 1000)

            data, _ = sf.read(filePath, start=start_frame, frames=frames, dtype="float32")
            if data is None or getattr(data, "size", 0) == 0:
                return np.array([])

            if data.ndim > 1:
                data = data.mean(axis=1)

            if len(data) > 1:
                data = data * np.hanning(len(data))

            return np.abs(np.fft.rfft(data))
        except Exception:
            return np.array([])