from __future__ import annotations

from pathlib import Path
from typing import Any

import mutagen

from .models import Track


def _extract_tag(tags: Any, *keys: str, default: str) -> str:
	if not tags:
		return default

	for key in keys:
		if key not in tags:
			continue

		value = tags.get(key)
		if isinstance(value, (list, tuple)):
			if value:
				return str(value[0])
			continue

		text = getattr(value, "text", None)
		if isinstance(text, (list, tuple)) and text:
			return str(text[0])

		return str(value)

	return default


def make_track_from_file(path: str) -> Track:
	file_path = str(Path(path))
	title = Path(file_path).stem
	artist = "Unknown Artist"
	album = "Unknown Album"
	genre = "Unknown Genre"
	duration = 0.0

	try:
		audio = mutagen.File(file_path, easy=True)
		if audio is not None:
			tags = getattr(audio, "tags", None)
			title = _extract_tag(tags, "title", default=title)
			artist = _extract_tag(tags, "artist", default=artist)
			album = _extract_tag(tags, "album", default=album)
			genre = _extract_tag(tags, "genre", default=genre)

			info = getattr(audio, "info", None)
			length = getattr(info, "length", 0.0)
			duration = float(length or 0.0)
	except Exception:
		pass

	return Track(
		path=file_path,
		title=title,
		artist=artist,
		album=album,
		genre=genre,
		duration=duration,
	)
