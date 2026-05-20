from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from .models import Track

if TYPE_CHECKING:
    from .libraryHandler import LibraryHandler


class Recommender:
    def __init__(self, library_handler: "LibraryHandler"):
        self.library_handler = library_handler
        self.adjacency: dict[str, dict[str, int]] = {}
        self.rebuild()

    def rebuild(self) -> None:
        history = self.library_handler.get_history()
        graph: dict[str, dict[str, int]] = defaultdict(lambda: defaultdict(int))

        previous_path: str | None = None
        for item in history:
            current_path = str(item.get("path") or item.get("filePath") or "")
            if not current_path:
                continue
            if previous_path and previous_path != current_path:
                graph[previous_path][current_path] += 1
                graph[current_path][previous_path] += 1
            previous_path = current_path

        self.adjacency = {node: dict(neighbors) for node, neighbors in graph.items()}

    def recommend(self, track_path: str | None, limit: int = 5) -> list[Track]:
        if not track_path:
            return []

        neighbors = self.adjacency.get(track_path, {})
        ordered_paths = sorted(neighbors, key=lambda path: neighbors[path], reverse=True)
        recommendations: list[Track] = []
        for path in ordered_paths[:limit]:
            track = self.library_handler.track_index.get(path)
            if track is not None:
                recommendations.append(track)
        return recommendations

    def recommend_from_recent_history(self, limit: int = 5) -> list[Track]:
        history = self.library_handler.get_history()
        if not history:
            return []
        current_path = str(history[-1].get("path") or history[-1].get("filePath") or "")
        return self.recommend(current_path, limit=limit)