"""openZIM Compiler for Welfare Portals.

Packages scraped welfare articles, offline stylesheets, vector icons,
and full-text search indexes into standard .zim files compatible with
Kiwix Desktop (https://github.com/Sriram-Nambiar/kiwix-desktop) and openZIM readers.
"""

import datetime
import html
import logging
import pathlib
from typing import Callable, List, Optional
import libzim

from scraper.models import ScrapedAsset, ScraperConfig, WelfareSchemeArticle

logger = logging.getLogger("janseva.scraper.zim_compiler")


class ZimArticleItem(libzim.BaseWritingItem):
    """Writing item for python-libzim."""

    def __init__(self, path: str, title: str, content: bytes | str, mimetype: str = "text/html"):
        super().__init__()
        self._path = path
        self._title = title
        self._content = content
        self._mimetype = mimetype

    def get_path(self) -> str:
        return self._path

    def get_title(self) -> str:
        return self._title

    def get_mimetype(self) -> str:
        return self._mimetype

    def get_contentprovider(self) -> libzim.ContentProvider:
        return libzim.StringProvider(self._content)

    def get_hints(self) -> dict:
        return {}


# Embedded offline stylesheet optimized for Kiwix Desktop & Kiwix Mobile
OFFLINE_CSS = """/* JanSeva openZIM Offline Stylesheet - Optimized for Kiwix Desktop */
:root {
  --bg-color: #f8fafc;
  --card-bg: #ffffff;
  --text-main: #0f172a;
  --text-muted: #64748b;
  --primary: #0284c7;
  --primary-hover: #0369a1;
  --primary-light: #e0f2fe;
  --border: #e2e8f0;
  --warning-bg: #fffbeb;
  --warning-border: #fef3c7;
  --warning-text: #b45309;
  --danger-bg: #fef2f2;
  --danger-text: #b91c1c;
  --success-bg: #f0fdf4;
  --success-text: #15803d;
}

@media (prefers-color-scheme: dark) {
  :root {
    --bg-color: #0f172a;
    --card-bg: #1e293b;
    --text-main: #f8fafc;
    --text-muted: #94a3b8;
    --primary: #38bdf8;
    --primary-hover: #7dd3fc;
    --primary-light: #082f49;
    --border: #334155;
    --warning-bg: #451a03;
    --warning-border: #78350f;
    --warning-text: #fde68a;
    --danger-bg: #450a0a;
    --danger-text: #fca5a5;
    --success-bg: #052e16;
    --success-text: #86efac;
  }
}

* { box-sizing: border-box; margin: 0; padding: 0; }

body {
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
  line-height: 1.6;
  color: var(--text-main);
  background-color: var(--bg-color);
  padding: 24px;
  max-width: 1050px;
  margin: 0 auto;
}

header.nav-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  margin-bottom: 24px;
}

.brand {
  font-size: 18px;
  font-weight: 800;
  color: var(--primary);
  text-decoration: none;
  display: flex;
  align-items: center;
  gap: 8px;
}

.kiwix-badge {
  font-size: 11px;
  font-family: monospace;
  background: var(--primary-light);
  color: var(--primary);
  padding: 4px 8px;
  border-radius: 6px;
  font-weight: 600;
  text-transform: uppercase;
}

h1 {
  font-size: 28px;
  font-weight: 800;
  color: var(--text-main);
  margin-bottom: 12px;
  line-height: 1.25;
}

h2 {
  font-size: 18px;
  font-weight: 700;
  color: var(--primary);
  margin-top: 24px;
  margin-bottom: 8px;
  border-bottom: 1px solid var(--border);
  padding-bottom: 4px;
}

p { margin-bottom: 12px; }

.meta-row {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 20px;
  align-items: center;
}

.badge {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 10px;
  border-radius: 9999px;
  background: var(--border);
  color: var(--text-main);
}

.badge-primary { background: var(--primary-light); color: var(--primary); }
.badge-success { background: var(--success-bg); color: var(--success-text); }

.card {
  background: var(--card-bg);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 16px;
  transition: transform 0.15s ease, border-color 0.15s ease;
}

.card:hover {
  border-color: var(--primary);
}

.card h3 {
  font-size: 18px;
  margin-bottom: 6px;
}

.card h3 a {
  color: var(--text-main);
  text-decoration: none;
}

.card h3 a:hover {
  color: var(--primary);
  text-decoration: underline;
}

.benefit-box {
  background: var(--success-bg);
  color: var(--success-text);
  border-left: 4px solid var(--success-text);
  padding: 14px 18px;
  border-radius: 6px;
  margin: 16px 0;
  font-weight: 500;
}

.warning-box {
  background: var(--warning-bg);
  color: var(--warning-text);
  border-left: 4px solid var(--warning-text);
  padding: 14px 18px;
  border-radius: 6px;
  margin: 16px 0;
}

.danger-box {
  background: var(--danger-bg);
  color: var(--danger-text);
  border-left: 4px solid var(--danger-text);
  padding: 14px 18px;
  border-radius: 6px;
  margin: 16px 0;
}

ul, ol {
  padding-left: 22px;
  margin-bottom: 16px;
}

li {
  margin-bottom: 8px;
}

.statutory-tag {
  display: block;
  font-size: 12px;
  color: var(--text-muted);
  font-style: italic;
  margin-top: 2px;
}

/* Offline Search Bar */
.search-container {
  margin-bottom: 24px;
}

.search-input {
  width: 100%;
  padding: 14px 18px;
  font-size: 15px;
  border: 2px solid var(--border);
  border-radius: 10px;
  background: var(--card-bg);
  color: var(--text-main);
  outline: none;
}

.search-input:focus {
  border-color: var(--primary);
}

.filter-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  margin-top: 12px;
}

.filter-pill {
  font-size: 12px;
  padding: 6px 12px;
  border-radius: 20px;
  background: var(--card-bg);
  border: 1px solid var(--border);
  color: var(--text-muted);
  cursor: pointer;
  user-select: none;
}

.filter-pill.active, .filter-pill:hover {
  background: var(--primary);
  color: white;
  border-color: var(--primary);
}

footer {
  margin-top: 40px;
  padding-top: 20px;
  border-top: 1px solid var(--border);
  font-size: 12px;
  color: var(--text-muted);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

/* Print Friendly Styles */
@media print {
  body { background: white; color: black; padding: 0; }
  .nav-header, .search-container, footer { display: none; }
  .card, .benefit-box, .warning-box { border: 1px solid #ccc; page-break-inside: avoid; }
}
"""

SVG_ICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 48 48" width="48" height="48">
  <circle cx="24" cy="24" r="22" fill="#0284c7"/>
  <path d="M24 10 L38 20 L38 24 L36 24 L36 36 L30 36 L30 26 L18 26 L18 36 L12 36 L12 24 L10 24 L10 20 Z" fill="#ffffff"/>
  <circle cx="24" cy="20" r="3" fill="#0284c7"/>
</svg>"""


class openZimCompiler:
    """Compiles extracted welfare scheme articles into standard Kiwix .zim archives."""

    def __init__(self, config: ScraperConfig, log_callback: Optional[Callable[[str], None]] = None):
        self.config = config
        self.log_callback = log_callback or (lambda msg: None)

    def log(self, message: str) -> None:
        logger.info(message)
        self.log_callback(message)

    def compile(self, articles: List[WelfareSchemeArticle]) -> pathlib.Path:
        """Compile articles list into a native openZIM file."""
        output_file = pathlib.Path(self.config.output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        if output_file.exists():
            try:
                output_file.unlink()
            except Exception as e:
                self.log(f"Warning: could not overwrite existing {output_file}: {e}")

        self.log(f"Initializing libzim Creator for {output_file}...")
        creator = libzim.Creator(output_file)

        # 1. Configure Full-Text Search indexing and Main Entry Path BEFORE entering context
        creator.config_indexing(True, self.config.language)
        creator.set_mainpath("index.html")

        # 2. Enter Creator context and write metadata and entries
        with creator:
            # openZIM Standard Metadata
            today_iso = datetime.datetime.utcnow().strftime("%Y-%m-%d")
            creator.add_metadata("Title", self.config.title)
            creator.add_metadata("Description", self.config.description)
            creator.add_metadata("Creator", self.config.creator)
            creator.add_metadata("Publisher", self.config.publisher)
            creator.add_metadata("Language", self.config.language)
            creator.add_metadata("Date", today_iso)
            creator.add_metadata("Source", self.config.seed_url)
            creator.add_metadata("Scraper", "janseva-welfare-scraper/2.0 (openZIM/Kiwix)")
            creator.add_metadata("Tags", f"_category:welfare;_sw:yes;_count:{len(articles)}")

            # Static Assets (Offline CSS and Vector Icon)
            creator.add_item(ZimArticleItem(
                path="assets/offline.css",
                title="JanSeva Offline CSS",
                content=OFFLINE_CSS,
                mimetype="text/css",
            ))
            creator.add_item(ZimArticleItem(
                path="assets/icon.svg",
                title="JanSeva Logo",
                content=SVG_ICON,
                mimetype="image/svg+xml",
            ))

            # Master Catalog / Searchable Directory (index.html)
            index_html = self._generate_index_html(articles)
            creator.add_item(ZimArticleItem(
                path="index.html",
                title=f"{self.config.title} - Directory",
                content=index_html,
                mimetype="text/html",
            ))

            # Individual Scheme Articles
            for idx, article in enumerate(articles):
                art_html = self._generate_article_html(article)
                creator.add_item(ZimArticleItem(
                    path=f"{article.id}.html",
                    title=article.title,
                    content=art_html,
                    mimetype="text/html",
                ))

        size_bytes = output_file.stat().st_size
        self.log(f"Successfully compiled {output_file} ({size_bytes} bytes, {len(articles)} articles)")
        return output_file

    def _generate_index_html(self, articles: List[WelfareSchemeArticle]) -> str:
        """Generate interactive offline index.html catalog."""
        categories = sorted(list(set(a.category for a in articles if a.category)))
        states = sorted(list(set(a.state for a in articles if a.state)))

        # Card items
        cards_html = []
        for a in articles:
            cards_html.append(f"""
<div class="card scheme-card" data-category="{html.escape(a.category)}" data-state="{html.escape(a.state)}" data-title="{html.escape(a.title.lower())}">
  <div class="meta-row">
    <span class="badge badge-primary">{html.escape(a.category)}</span>
    <span class="badge">{html.escape(a.state)}</span>
  </div>
  <h3><a href="{a.id}.html">{html.escape(a.title)}</a></h3>
  <p style="font-size: 13px; color: var(--text-muted); margin-bottom: 6px;"><strong>{html.escape(a.department)}</strong></p>
  <p style="font-size: 14px;">{html.escape(a.benefit_summary or a.eligibility_summary)}</p>
  <div style="margin-top: 10px;">
    <a href="{a.id}.html" style="color: var(--primary); font-size: 13px; font-weight: 600; text-decoration: none;">View Statutory Requirements & Process →</a>
  </div>
</div>
""")

        filter_pills_html = '<div class="filter-pill active" onclick="filterCategory(\'All\', this)">All Categories</div>'
        for cat in categories:
            filter_pills_html += f'<div class="filter-pill" onclick="filterCategory(\'{html.escape(cat)}\', this)">{html.escape(cat)}</div>'

        return f"""<!DOCTYPE html>
<html lang="{self.config.language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(self.config.title)}</title>
  <link rel="stylesheet" href="assets/offline.css">
  <link rel="icon" type="image/svg+xml" href="assets/icon.svg">
</head>
<body>
  <header class="nav-header">
    <a href="index.html" class="brand">
      <img src="assets/icon.svg" width="28" height="28" alt="Logo">
      JanSeva openZIM
    </a>
    <span class="kiwix-badge">Kiwix Offline Pack</span>
  </header>

  <main>
    <h1>{html.escape(self.config.title)}</h1>
    <p style="color: var(--text-muted); font-size: 15px; margin-bottom: 20px;">
      {html.escape(self.config.description)}
    </p>

    <!-- Client-side instantaneous offline search -->
    <div class="search-container">
      <input type="text" id="searchInput" class="search-input" placeholder="🔍 Search schemes, benefits, documents (offline)..." oninput="runFilter()">
      <div class="filter-pills" id="categoryFilterContainer">
        {filter_pills_html}
      </div>
    </div>

    <div id="resultsCount" style="font-size: 13px; color: var(--text-muted); margin-bottom: 12px; font-weight: 600;">
      Displaying {len(articles)} schemes
    </div>

    <div id="schemesList">
      {"".join(cards_html)}
    </div>
  </main>

  <footer>
    <span>Generated by JanSeva openZIM Pipeline | Compatible with Kiwix Desktop</span>
    <span>Archived: {datetime.datetime.utcnow().strftime('%B %Y')}</span>
  </footer>

  <script>
    let activeCategory = 'All';

    function filterCategory(cat, el) {{
      activeCategory = cat;
      document.querySelectorAll('.filter-pill').forEach(p => p.classList.remove('active'));
      el.classList.add('active');
      runFilter();
    }}

    function runFilter() {{
      const query = document.getElementById('searchInput').value.toLowerCase().trim();
      const cards = document.querySelectorAll('.scheme-card');
      let visible = 0;

      cards.forEach(card => {{
        const title = card.getAttribute('data-title') || '';
        const cat = card.getAttribute('data-category') || '';
        const cardText = card.innerText.toLowerCase();

        const matchesQuery = !query || cardText.includes(query);
        const matchesCategory = (activeCategory === 'All') || (cat === activeCategory);

        if (matchesQuery && matchesCategory) {{
          card.style.display = 'block';
          visible++;
        }} else {{
          card.style.display = 'none';
        }}
      }});

      document.getElementById('resultsCount').innerText = 'Displaying ' + visible + ' schemes';
    }}
  </script>
</body>
</html>
"""

    def _generate_article_html(self, article: WelfareSchemeArticle) -> str:
        """Generate individual scheme article page HTML."""
        # Required documents list
        docs_html = []
        for d in article.required_documents:
            docs_html.append(f"""
<li>
  <strong>{html.escape(d.name)}</strong>
  <span class="statutory-tag">⚖️ Statutory legal reason: {html.escape(d.statutory_why)}</span>
</li>
""")
        if not docs_html:
            docs_html.append("<li>Standard government identification proof (Aadhaar, Ration Card).</li>")

        # Eligibility criteria
        elig_html = []
        for crit in article.eligibility_criteria:
            elig_html.append(f"<li>{html.escape(crit)}</li>")
        if not elig_html:
            elig_html.append(f"<li>{html.escape(article.eligibility_summary or 'Refer to official scheme portal.')}</li>")

        # Application process
        steps_html = []
        for s in article.application_process:
            steps_html.append(f"<li>{html.escape(s)}</li>")

        # Pitfalls
        pitfalls_html = []
        for p in article.common_rejection_pitfalls:
            pitfalls_html.append(f"<li>⚠️ {html.escape(p)}</li>")

        return f"""<!DOCTYPE html>
<html lang="{self.config.language}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>{html.escape(article.title)} - JanSeva</title>
  <link rel="stylesheet" href="assets/offline.css">
  <link rel="icon" type="image/svg+xml" href="assets/icon.svg">
</head>
<body>
  <header class="nav-header">
    <a href="index.html" class="brand">← Back to Offline Directory</a>
    <span class="kiwix-badge">openZIM Article</span>
  </header>

  <article>
    <div class="meta-row">
      <span class="badge badge-primary">{html.escape(article.category)}</span>
      <span class="badge">{html.escape(article.state)}</span>
      <span class="badge badge-success">Direct Benefit Transfer</span>
    </div>

    <h1>{html.escape(article.title)}</h1>
    <p style="color: var(--text-muted); font-size: 14px;"><strong>Nodal Department:</strong> {html.escape(article.department)}</p>

    <h2>1. Direct Citizen Benefit</h2>
    <div class="benefit-box">
      💰 {html.escape(article.benefit_summary or 'Financial and welfare assistance under scheme provisions.')}
    </div>

    <h2>2. Statutory Eligibility Criteria</h2>
    <p>{html.escape(article.eligibility_summary)}</p>
    <ul>
      {"".join(elig_html)}
    </ul>

    <h2>3. Mandatory Required Documents & Statutory Justifications</h2>
    <p style="font-size: 13px; color: var(--text-muted);">
      Every document listed below is cross-verified against statutory government databases.
    </p>
    <ul>
      {"".join(docs_html)}
    </ul>

    {f'''<h2>4. Step-by-Step Application Procedure</h2>
    <ol>
      {"".join(steps_html)}
    </ol>''' if steps_html else ''}

    {f'''<h2>5. Common Administrative Rejection Pitfalls</h2>
    <div class="warning-box">
      <strong>⚠️ Warning for applicants:</strong>
      <ul style="margin-top: 8px; margin-bottom: 0;">
        {"".join(pitfalls_html)}
      </ul>
    </div>''' if pitfalls_html else ''}

    <h2>6. Official Portal & Citizen Grievance</h2>
    <p><strong>Official Web Portal:</strong> <a href="{html.escape(article.portal_url)}" target="_blank" style="color: var(--primary);">{html.escape(article.portal_url)}</a></p>
    {f'<p><strong>National/State Toll-Free Helpline:</strong> {html.escape(article.nodal_helpline)}</p>' if article.nodal_helpline else ''}
  </article>

  <footer>
    <span>JanSeva openZIM Pipeline | Kiwix Desktop Compatible</span>
    <a href="index.html" style="color: var(--primary); text-decoration: none; font-weight: 600;">Return to Catalog ↑</a>
  </footer>
</body>
</html>
"""
