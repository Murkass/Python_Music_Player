from __future__ import annotations

import time
from collections import deque
from pathlib import Path

from source.core.libraryHandler import LibraryHandler
from source.core.models import Track
from source.core.musicHandler import MusicHandler
from source.core.storeHandler import StoreHandler


class FakeAudioBackend:
    def __init__(self, positions: list[int] | None = None) -> None:
        self.loaded: list[str] = []
        self.volume = 0.5
        self.positions = deque(positions or [0, 120, 240, 360, 480])
        self.stereo_calls: list[tuple[float, float]] = []
        self.paused = False

    def load(self, path: str) -> None:
        self.loaded.append(path)

    def play(self) -> None:
        return None

    def pause(self) -> None:
        self.paused = True

    def unpause(self) -> None:
        self.paused = False

    def stop(self) -> None:
        return None

    def set_volume(self, volume: float) -> None:
        self.volume = volume

    def get_volume(self) -> float:
        return self.volume

    def get_pos(self) -> int:
        if len(self.positions) > 1:
            return self.positions.popleft()
        return self.positions[0]

    def set_stereo_volume(self, left: float, right: float) -> None:
        self.stereo_calls.append((left, right))


class Listener:
    def __init__(self) -> None:
        self.events: list[tuple[str, dict]] = []

    def handle_player_event(self, event: str, payload: dict) -> None:
        self.events.append((event, payload))


def _make_handler(tmp_path: Path, positions: list[int] | None = None, auto_start_monitor: bool = False):
    store = StoreHandler(str(tmp_path / "music.json"))
    library = LibraryHandler(store)
    backend = FakeAudioBackend(positions=positions)
    handler = MusicHandler(
        store,
        library_handler=library,
        audio_backend=backend,
        poll_interval=0.01,
        auto_start_monitor=auto_start_monitor,
    )
    return handler, backend, library


def test_notifies_multiple_listeners_and_manages_deque_queue(tmp_path: Path) -> None:
    handler, backend, _ = _make_handler(tmp_path)
    first = Listener()
    second = Listener()
    handler.add_listener(first)
    handler.add_listener(second)

    tracks = [
        Track(path="/tmp/a.mp3", title="A", artist="Artist", duration=120.0),
        Track(path="/tmp/b.mp3", title="B", artist="Artist", duration=150.0),
        Track(path="/tmp/c.mp3", title="C", artist="Artist", duration=180.0),
    ]

    for track in tracks:
        handler.enqueue_track(track)

    assert list(handler.playingQueue) == tracks

    handler.selectTrack(1)
    handler.playPause()
    handler.playPause()
    handler.playNext()

    event_names = [event for event, _ in first.events]
    assert "select_track" in event_names
    assert "play_pause" in event_names
    assert "play_next" in event_names
    assert len(first.events) == len(second.events)
    assert backend.loaded[0] == "/tmp/b.mp3"


def test_position_polling_thread_emits_position_updates(tmp_path: Path) -> None:
    handler, _, _ = _make_handler(tmp_path, positions=[0, 250, 500, 750, 1000], auto_start_monitor=True)
    listener = Listener()
    handler.add_listener(listener)
    handler.enqueue_track(Track(path="/tmp/poll.mp3", title="Poll", artist="Artist", duration=2.0))
    handler.playNext()

    deadline = time.time() + 0.3
    while time.time() < deadline:
        if any(event == "position_update" for event, _ in listener.events):
            break
        time.sleep(0.02)

    handler.shutdown()

    updates = [payload for event, payload in listener.events if event == "position_update"]
    assert updates
    assert updates[-1]["position"] >= 0.0
    assert 0.0 <= updates[-1]["progress"] <= 1.0


def test_spatial_balance_updates_stereo_attenuation(tmp_path: Path) -> None:
    handler, backend, _ = _make_handler(tmp_path)

    for _ in range(5):
        spatial = handler.update_spatial_balance(1.0)

    assert spatial["right_gain"] > spatial["left_gain"]
    assert backend.stereo_calls
    assert backend.stereo_calls[-1][1] > backend.stereo_calls[-1][0]