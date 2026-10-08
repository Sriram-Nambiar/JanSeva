"""Data models for JanSeva openZIM Welfare Portal Scraper.

Defines schemas for extracted articles, statutory requirements,
downloaded assets, scraper configuration, and openZIM metadata.
"""

from dataclasses import dataclass, field
import datetime
import pathlib
from typing import Any, Dict, List, Optional


@dataclass
class SchemeDocumentRequirement:
    """Document requirement with legal/statutory justification."""
    name: str
    statutory_why: str = "Mandatory identification and verification under scheme administrative guidelines."

    def to_dict(self) -> Dict[str, str]:
        return {
            "name": self.name,
            "statutory_why": self.statutory_why,
        }


@dataclass
class ScrapedAsset:
    """A static asset (CSS, image, icon, SVG) to store in the ZIM archive."""
    path: str               # e.g. "assets/style.css" or "assets/logo.png"
    data: bytes | str       # Binary or string content
    mimetype: str           # MIME type, e.g. "text/css", "image/png", "image/svg+xml"
    title: str = ""         # Human-readable title for libzim item index


@dataclass
class WelfareSchemeArticle:
    """Structured representation of a scraped welfare scheme article."""
    id: str                                                 # URL-safe slug, e.g. 'pm-kisan-samman-nidhi'
    title: str                                              # Full scheme title
    portal_url: str                                         # Source portal URL
    department: str = "Government of India"                 # Nodal department / ministry
    state: str = "All India"                                # State or 'All India'
    category: str = "General Welfare"                       # Scheme category (Agriculture, Health, etc.)
    benefit_summary: str = ""                               # Concise benefit description
    eligibility_summary: str = ""                           # Who is eligible
    eligibility_criteria: List[str] = field(default_factory=list)  # Bulleted eligibility rules
    required_documents: List[SchemeDocumentRequirement] = field(default_factory=list)
    application_process: List[str] = field(default_factory=list)
    common_rejection_pitfalls: List[str] = field(default_factory=list)
    nodal_helpline: str = ""                                # Toll-free or helpline
    raw_html: str = ""                                      # Sanitized article HTML
    tags: List[str] = field(default_factory=list)
    scraped_at: str = field(default_factory=lambda: datetime.datetime.utcnow().isoformat() + "Z")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "portal_url": self.portal_url,
            "department": self.department,
            "state": self.state,
            "category": self.category,
            "benefit_summary": self.benefit_summary,
            "eligibility_summary": self.eligibility_summary,
            "eligibility_criteria": self.eligibility_criteria,
            "required_documents": [d.to_dict() for d in self.required_documents],
            "application_process": self.application_process,
            "common_rejection_pitfalls": self.common_rejection_pitfalls,
            "nodal_helpline": self.nodal_helpline,
            "tags": self.tags,
            "scraped_at": self.scraped_at,
        }


@dataclass
class ScraperConfig:
    """Configuration options for crawler and ZIM compilation."""
    seed_url: str = "https://myscheme.gov.in"
    output_path: pathlib.Path = field(default_factory=lambda: pathlib.Path("packs/welfare_scraped.zim"))
    title: str = "JanSeva Welfare Schemes Archive"
    description: str = "Complete offline openZIM directory of Indian welfare schemes with statutory eligibility guides."
    creator: str = "JanSeva openZIM Scraper Pipeline"
    publisher: str = "JanSeva / Kiwix Community"
    language: str = "eng"                                   # ISO 639-3 ('eng', 'hin', 'kan', etc.)
    max_pages: int = 50                                     # Maximum scheme pages to crawl
    max_depth: int = 2                                      # Maximum link discovery depth
    timeout_seconds: int = 10                               # HTTP request timeout
    rate_limit_delay: float = 0.5                           # Polite crawl delay between requests
    download_images: bool = True                            # Bundle remote images into ZIM
    offline_fallback: bool = True                           # Fallback to curated dataset if portal is down/blocked
