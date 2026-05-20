from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Track:
    path: str
    title: str
    artist: str = "Unknown Artist"
    album: str = "Unknown Album"
    genre: str = "Unknown Genre"
    duration: float = 0.0
    is_favorite: bool = False
    play_count: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "title": self.title,
            "artist": self.artist,
            "album": self.album,
            "genre": self.genre,
            "duration": self.duration,
            "is_favorite": self.is_favorite,
            "play_count": self.play_count,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Track":
        return cls(
            path=str(data.get("path") or data.get("filePath") or data.get("file_path") or ""),
            title=str(data.get("title") or "Unknown Title"),
            artist=str(data.get("artist") or "Unknown Artist"),
            album=str(data.get("album") or "Unknown Album"),
            genre=str(data.get("genre") or "Unknown Genre"),
            duration=float(data.get("duration") or 0.0),
            is_favorite=bool(data.get("is_favorite", data.get("favorite", False))),
            play_count=int(data.get("play_count") or 0),
        )