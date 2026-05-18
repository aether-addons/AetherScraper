from __future__ import annotations

from aetherscraper.config import ProviderConfig
from aetherscraper.models import SourceResult
from aetherscraper.provider import BaseProvider


class ExampleProvider(BaseProvider):
    config = ProviderConfig(
        id="example",
        name="Example Public Provider",
        enabled=False,
        priority=999,
        provider_type="direct",
        pack_capable=False,
        has_movies=True,
        has_episodes=False,
        media_types=["movie"],
        base_url="https://example.com",
    )

    def search(self, query, options):
        if not query.title:
            return []
        return [
            SourceResult(
                provider=self.id,
                title=query.title,
                url="https://example.com/replace-with-legal-source.mp4",
                quality="unknown",
                media_type=query.media_type,
                score=0.1,
                direct=True,
            )
        ]
