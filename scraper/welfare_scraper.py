"""Unified Welfare openZIM Scraper & Pipeline Orchestrator."""

import logging
import pathlib
import time
from typing import Any, Callable, Dict, List, Optional
import libzim

from scraper.crawler import WelfareCrawler
from scraper.models import ScraperConfig, WelfareSchemeArticle
from scraper.offline_dataset import CURATED_WELFARE_SCHEMES
from scraper.zim_compiler import openZimCompiler

logger = logging.getLogger("janseva.scraper")


class WelfareZimScraper:
    """End-to-end scraper and openZIM archive generator for welfare portals."""

    def __init__(self, log_callback: Optional[Callable[[str], None]] = None):
        self.log_callback = log_callback or (lambda msg: None)

    def log(self, message: str) -> None:
        logger.info(message)
        self.log_callback(message)

    def crawl_and_compile(self, config: ScraperConfig) -> Dict[str, Any]:
        """Crawl a target portal and compile the extracted content into a .zim file."""
        t0 = time.time()
        self.log(f"=== Starting openZIM Scraper Pipeline for {config.seed_url} ===")

        # 1. Crawl portal
        crawler = WelfareCrawler(config, log_callback=self.log_callback)
        articles = crawler.crawl()

        if not articles:
            raise RuntimeError(f"No welfare scheme articles could be extracted from {config.seed_url}.")

        # 2. Compile into ZIM
        self.log(f"Compiling {len(articles)} extracted articles into openZIM archive...")
        compiler = openZimCompiler(config, log_callback=self.log_callback)
        zim_file = compiler.compile(articles)

        elapsed = round(time.time() - t0, 2)
        size_bytes = zim_file.stat().st_size
        size_kb = round(size_bytes / 1024, 1)

        self.log(f"=== openZIM archive ready: {zim_file.name} ({size_kb} KB, {len(articles)} schemes in {elapsed}s) ===")

        return {
            "status": "success",
            "zim_path": str(zim_file.resolve()),
            "zim_filename": zim_file.name,
            "size_bytes": size_bytes,
            "size_kb": size_kb,
            "article_count": len(articles),
            "duration_seconds": elapsed,
            "articles": [a.to_dict() for a in articles],
        }

    def compile_schemes_to_zim(
        self,
        articles: List[WelfareSchemeArticle],
        config: ScraperConfig,
    ) -> pathlib.Path:
        """Compile an in-memory list of articles into a .zim archive."""
        compiler = openZimCompiler(config, log_callback=self.log_callback)
        return compiler.compile(articles)

    def generate_curated_welfare_zim(
        self,
        output_path: pathlib.Path,
        title: str = "JanSeva Comprehensive Welfare Schemes Directory",
        lang: str = "eng",
    ) -> pathlib.Path:
        """Compile verified Indian welfare registry into a .zim archive."""
        config = ScraperConfig(
            seed_url="https://myscheme.gov.in",
            output_path=output_path,
            title=title,
            description="Verified offline openZIM directory of Indian welfare schemes with statutory eligibility guides.",
            language=lang,
        )
        compiler = openZimCompiler(config, log_callback=self.log_callback)
        return compiler.compile(CURATED_WELFARE_SCHEMES)

    @staticmethod
    def inspect_zim(zim_path: str | pathlib.Path) -> Dict[str, Any]:
        """Inspect a .zim file using libzim and return its metadata and entries."""
        p = pathlib.Path(zim_path)
        if not p.exists():
            raise FileNotFoundError(f"ZIM file does not exist: {p}")

        arch = libzim.Archive(str(p))

        metadata: Dict[str, str] = {}
        for key in arch.metadata_keys:
            try:
                metadata[key] = arch.get_metadata(key)
            except Exception:
                pass

        # Sample entry listing
        entries = []
        count = min(arch.entry_count, 50)
        for i in range(count):
            try:
                entry = arch._get_entry_by_id(i)
                entries.append({
                    "path": entry.path,
                    "title": entry.title,
                    "is_redirect": entry.is_redirect,
                })
            except Exception:
                break

        return {
            "filename": p.name,
            "path": str(p.resolve()),
            "filesize_bytes": arch.filesize,
            "filesize_kb": round(arch.filesize / 1024, 1),
            "entry_count": arch.entry_count,
            "article_count": arch.article_count,
            "media_count": arch.media_count,
            "has_main_entry": arch.has_main_entry,
            "main_path": arch.main_entry.path if arch.has_main_entry else None,
            "has_fulltext_index": arch.has_fulltext_index,
            "has_title_index": arch.has_title_index,
            "metadata": metadata,
            "sample_entries": entries,
        }
