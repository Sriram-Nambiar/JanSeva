"""Polite, robust web crawler for welfare websites."""

import logging
import time
from typing import Callable, List, Optional, Set
import urllib.parse
from bs4 import BeautifulSoup
import requests

from scraper.models import ScraperConfig, WelfareSchemeArticle
from scraper.offline_dataset import CURATED_WELFARE_SCHEMES
from scraper.parsers import CentralDbtParser, GenericWelfareParser, MySchemeParser

logger = logging.getLogger("janseva.scraper.crawler")


class WelfareCrawler:
    """Polite crawler for extracting welfare scheme articles from portals."""

    DEFAULT_USER_AGENT = (
        "Mozilla/5.0 (compatible; JanSeva-openZIM-Scraper/2.0; "
        "+https://github.com/Sriram-Nambiar/JanSeva; Kiwix-Desktop-Integration)"
    )

    def __init__(self, config: ScraperConfig, log_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.log_callback = log_callback or (lambda msg: None)
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": self.DEFAULT_USER_AGENT,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,hi;q=0.8",
        })

        self.parsers = [
            MySchemeParser(),
            CentralDbtParser(),
            GenericWelfareParser(),
        ]

    def log(self, message: str) -> None:
        logger.info(message)
        self.log_callback(message)

    def crawl(self) -> List[WelfareSchemeArticle]:
        """Crawl from seed_url up to max_pages and max_depth."""
        seed = self.config.seed_url.strip()
        self.log(f"Starting crawl at seed URL: {seed}")

        articles: List[WelfareSchemeArticle] = []
        visited_urls: Set[str] = set()
        queue: List[tuple[str, int]] = [(seed, 0)]
        discovered_slugs: Set[str] = set()

        failed_fetch_count = 0

        while queue and len(articles) < self.config.max_pages:
            current_url, depth = queue.pop(0)
            norm_url = self._normalize_url(current_url)

            if norm_url in visited_urls:
                continue
            visited_urls.add(norm_url)

            self.log(f"[{len(articles)+1}/{self.config.max_pages}] Fetching: {norm_url} (depth={depth})")

            html = self._fetch_url(norm_url)
            if not html:
                failed_fetch_count += 1
                continue

            # Parse article
            article = self._parse_html(norm_url, html)
            if article and article.id not in discovered_slugs and len(article.title) > 3:
                discovered_slugs.add(article.id)
                articles.append(article)
                self.log(f"  -> Extracted Scheme: '{article.title}' ({article.category})")

            # Discover further links if within depth limit
            if depth < self.config.max_depth and len(articles) < self.config.max_pages:
                new_links = self._extract_links(norm_url, html)
                for link in new_links:
                    norm_link = self._normalize_url(link)
                    if norm_link not in visited_urls:
                        queue.append((norm_link, depth + 1))

            if self.config.rate_limit_delay > 0:
                time.sleep(self.config.rate_limit_delay)

        self.log(f"Crawl completed. Extracted {len(articles)} live articles.")

        # If live scraping extracted fewer than expected due to network/firewalls,
        # supplement with curated verified welfare schemes if fallback enabled
        if len(articles) < 3 and self.config.offline_fallback:
            self.log("Remote portal returned limited articles; hydrating with curated openZIM welfare registry...")
            for curated in CURATED_WELFARE_SCHEMES:
                if curated.id not in discovered_slugs and len(articles) < self.config.max_pages:
                    articles.append(curated)
                    discovered_slugs.add(curated.id)
            self.log(f"Total compiled scheme catalog: {len(articles)} articles.")

        return articles

    def _fetch_url(self, url: str) -> Optional[str]:
        """Fetch URL with timeout and error handling."""
        try:
            resp = self.session.get(url, timeout=self.config.timeout_seconds, allow_redirects=True)
            if resp.status_code == 200:
                return resp.text
            self.log(f"  HTTP {resp.status_code} for {url}")
            return None
        except Exception as e:
            self.log(f"  Fetch failed for {url}: {e}")
            return None

    def _parse_html(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        """Run through parser chain to extract scheme article."""
        for parser in self.parsers:
            if parser.can_parse(url, html):
                try:
                    res = parser.parse(url, html)
                    if res:
                        return res
                except Exception as e:
                    self.log(f"  Parser {parser.__class__.__name__} failed on {url}: {e}")
        return None

    def _extract_links(self, base_url: str, html: str) -> List[str]:
        """Extract candidate scheme hyperlinks from HTML."""
        soup = BeautifulSoup(html, "html.parser")
        base_domain = urllib.parse.urlparse(base_url).netloc
        links: List[str] = []

        for a in soup.find_all("a", href=True):
            href = a["href"].strip()
            if not href or href.startswith("#") or href.startswith("javascript:") or href.startswith("mailto:"):
                continue

            absolute_url = urllib.parse.urljoin(base_url, href)
            parsed = urllib.parse.urlparse(absolute_url)

            # Restrict to same domain or typical scheme paths
            if parsed.netloc == base_domain:
                path = parsed.path.lower()
                # Prioritize links likely to be scheme detail pages
                if any(k in path for k in ["/schemes/", "/scheme/", "/service/", "/details/", "/view/", "scheme_"]):
                    links.insert(0, absolute_url)
                elif len(links) < 30:
                    links.append(absolute_url)

        return links[:40]

    def _normalize_url(self, url: str) -> str:
        """Strip fragment and tracking query parameters."""
        parsed = urllib.parse.urlparse(url)
        clean = parsed._replace(fragment="")
        return urllib.parse.urlunparse(clean)
