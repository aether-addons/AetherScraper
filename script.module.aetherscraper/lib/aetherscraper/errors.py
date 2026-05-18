class ScraperError(Exception):
    """Base scraper module error."""


class ProviderError(ScraperError):
    """Provider failed during search."""

    def __init__(self, provider_id, message):
        super().__init__(f"{provider_id}: {message}")
        self.provider_id = provider_id
