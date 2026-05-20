from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["MusicHandler", "LibraryHandler", "StoreHandler", "Track", "make_track_from_file", "Recommender"]


def __getattr__(name: str) -> Any:
	if name == "MusicHandler":
		return import_module("source.core.musicHandler").MusicHandler
	if name == "LibraryHandler":
		return import_module("source.core.libraryHandler").LibraryHandler
	if name == "StoreHandler":
		return import_module("source.core.storeHandler").StoreHandler
	if name == "Track":
		return import_module("source.core.models").Track
	if name == "make_track_from_file":
		return import_module("source.core.utils").make_track_from_file
	if name == "Recommender":
		return import_module("source.core.recommender").Recommender
	raise AttributeError(name)