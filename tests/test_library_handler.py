from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from source.core.libraryHandler import LibraryHandler
from source.core.storeHandler import StoreHandler


def _make_handler(tmp_path: Path) -> LibraryHandler:
    store_path = tmp_path / "library.json"
    return LibraryHandler(StoreHandler(str(store_path)))


def test_indexes_and_tree_after_bulk_load(tmp_path: Path) -> None:
    handler = _make_handler(tmp_path)
    handler.create_playlist("Bulk")

    tracks = [
        ("/tmp/track-a.mp3", "Track A", "Artist 1", "Album X", "Rock"),
        ("/tmp/track-b.mp3", "Track B", "Artist 1", "Album X", "Rock"),
        ("/tmp/track-c.mp3", "Track C", "Artist 1", "Album Y", "Jazz"),
        ("/tmp/track-d.mp3", "Track D", "Artist 2", "Album Z", "Pop"),
    ]
    for path, title, artist, album, genre in tracks:
        handler.add_track(path, title=title, artist=artist, album=album, genre=genre)
        handler.add_music_to_playlist("Bulk", path, title=title, artist=artist, album=album, genre=genre)

    handler.index_tracks()

    assert len(handler.track_index) == 4
    assert len(handler.artist_index["artist 1"]) == 3
    assert len(handler.album_index["album x"]) == 2
    assert len(handler.genre_index["rock"]) == 2
    assert len(handler.track_tree["Artist 1"]["Album X"]) == 2


def test_concurrent_writes_preserve_valid_json(tmp_path: Path) -> None:
    handler = _make_handler(tmp_path)
    handler.create_playlist("Concurrency")

    def write_track(index: int) -> None:
        path = f"/tmp/concurrency-{index}.mp3"
        handler.add_track(path, title=f"Track {index}", artist="Worker", album="Batch", genre="Test")
        handler.add_music_to_playlist("Concurrency", path, title=f"Track {index}", artist="Worker", album="Batch", genre="Test")
        handler.update_settings(last_playlist="Concurrency", color_theme="green")

    with ThreadPoolExecutor(max_workers=8) as executor:
        list(executor.map(write_track, range(25)))

    store_file = tmp_path / "library.json"
    data = json.loads(store_file.read_text(encoding="utf-8"))

    assert len(data["tracks"]) == 25
    assert len(data["playlists"]["Concurrency"]["musics"]) == 25
    assert data["settings"]["last_playlist"] == "Concurrency"
    assert data["settings"]["color_theme"] == "green"


def test_ui_theme_settings_are_persisted(tmp_path: Path) -> None:
    handler = _make_handler(tmp_path)

    settings = handler.update_settings(appearance_mode="Dark", color_theme="dark-blue", volume=0.7)

    reloaded = _make_handler(tmp_path)

    assert settings["appearance_mode"] == "Dark"
    assert settings["color_theme"] == "dark-blue"
    assert reloaded.get_settings()["appearance_mode"] == "Dark"
    assert reloaded.get_settings()["color_theme"] == "dark-blue"
    assert reloaded.get_settings()["volume"] == 0.7