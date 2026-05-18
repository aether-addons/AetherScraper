from __future__ import annotations

import json
import os

from aetherscraper.config import ProviderConfig
from aetherscraper.provider import BaseProvider
from aetherscraper.torrent import normalize_torrent_item, torrent_to_source


class TorrentJsonProvider(BaseProvider):
    """Search legal, user-supplied torrent entries from JSON.

    Expected JSON:
    {
      "items": [
        {"title": "Big Buck Bunny", "magnet": "magnet:?xt=...", "quality": "1080p", "seeders": 10}
      ]
    }
    """

    config = ProviderConfig(
        id="torrent_json",
        name="Torrent JSON Provider",
        enabled=True,
        priority=100,
        provider_type="torrent",
        pack_capable=True,
        has_movies=True,
        has_episodes=True,
        media_types=["movie", "episode", "season", "show"],
    )

    def __init__(self, path=None, config=None, settings=None):
        super().__init__(config=config, settings=settings)
        self.path = path or self.config.params.get("data_file")

    def search(self, query, options):
        terms = [query.title.lower(), *[alias.lower() for alias in query.aliases]]
        items = self._load_items()
        results = []
        for data in items:
            item = normalize_torrent_item(data)
            title = item.title
            if not title or not any(term in title.lower() for term in terms if term):
                continue
            results.append(torrent_to_source(self.id, item))
        return results

    def _load_items(self):
        if not self.path or not os.path.exists(self.path):
            return []
        with open(self.path, encoding="utf-8") as handle:
            data = json.load(handle)
        return data.get("items", [])
