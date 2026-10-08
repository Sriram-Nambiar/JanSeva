"""JanSeva openZIM Welfare Portal Scraper & Compiler package."""

from scraper.crawler import WelfareCrawler
from scraper.models import (
    ScrapedAsset,
    ScraperConfig,
    SchemeDocumentRequirement,
    WelfareSchemeArticle,
)
from scraper.offline_dataset import CURATED_WELFARE_SCHEMES
from scraper.welfare_scraper import WelfareZimScraper
from scraper.zim_compiler import openZimCompiler

__all__ = [
    "WelfareCrawler",
    "ScrapedAsset",
    "ScraperConfig",
    "SchemeDocumentRequirement",
    "WelfareSchemeArticle",
    "CURATED_WELFARE_SCHEMES",
    "WelfareZimScraper",
    "openZimCompiler",
]
