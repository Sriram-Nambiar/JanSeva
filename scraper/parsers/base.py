"""Base parser interface for welfare portals."""

import abc
from typing import Optional
from scraper.models import WelfareSchemeArticle


class BaseSchemeParser(abc.ABC):
    """Abstract base class for welfare scheme parsers."""

    @abc.abstractmethod
    def can_parse(self, url: str, html: str) -> bool:
        """Check if this parser can handle the provided URL and HTML content."""
        pass

    @abc.abstractmethod
    def parse(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        """Parse raw HTML and extract a structured WelfareSchemeArticle."""
        pass
