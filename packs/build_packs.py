"""ZIM Archive Pack Builder.

Compiles JanSeva Welfare Knowledge Packs into native `.zim` archives using `libzim.Creator`.
These archives can be opened offline in Kiwix or queried by JanSeva's Model Harness.
"""

import os
import pathlib
import sys

# Ensure repository root is in sys.path
sys.path.insert(0, str(pathlib.Path(__file__).parent.parent))

from core.zim_engine import BASELINE_REJECTIONS, BASELINE_SCHEMES, LIBZIM_AVAILABLE

if not LIBZIM_AVAILABLE:
    print("libzim is not installed; cannot compile .zim archives.")
    sys.exit(1)

import libzim


class SimpleZimItem(libzim.BaseWritingItem):
    """Writing item for libzim."""

    def __init__(self, path: str, title: str, html_content: str, mimetype: str = "text/html"):
        super().__init__()
        self._path = path
        self._title = title
        self._content = html_content
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


def build_welfare_schemes_zim(output_path: pathlib.Path) -> None:
    """Compile welfare schemes into welfare_schemes.zim."""
    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    print(f"Building {output_path}...")
    creator = libzim.Creator(output_path)
    creator.config_indexing(True, "eng")
    creator.set_mainpath("index.html")

    with creator:
        # 1. Main index page
        index_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>JanSeva Welfare Knowledge Pack</title>
<style>
body { font-family: system-ui, sans-serif; margin: 40px; line-height: 1.6; color: #1e293b; background: #f8fafc; }
h1 { color: #0284c7; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.badge { display: inline-block; background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
a { color: #0284c7; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<h1>🏛️ JanSeva Welfare Knowledge Pack (openZIM)</h1>
<p>Complete offline reference for Indian Central & State Welfare Schemes with statutory requirement guides.</p>
"""
        for s in BASELINE_SCHEMES:
            index_html += f"""
<div class="card">
  <span class="badge">{s['category']}</span>
  <h3><a href="{s['id']}.html">{s['title']}</a></h3>
  <p><strong>Benefit:</strong> {s['benefit']}</p>
  <p><strong>Eligibility:</strong> {s['eligibility_summary']}</p>
</div>
"""
        index_html += "</body></html>"
        creator.add_item(SimpleZimItem("index.html", "JanSeva Welfare Directory", index_html))

        # 2. Individual Scheme Articles
        for s in BASELINE_SCHEMES:
            docs_html = "".join([
                f"<li><strong>{doc['name']}</strong>: <em>{doc['statutory_why']}</em></li>"
                for doc in s["required_documents"]
            ])
            pitfalls_html = "".join([f"<li>⚠️ {p}</li>" for p in s["common_rejection_pitfalls"]])

            article_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{s['title']}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 30px; line-height: 1.6; color: #1e293b; background: #ffffff; }}
h1 {{ color: #0f172a; border-bottom: 2px solid #0284c7; padding-bottom: 8px; }}
h2 {{ color: #0369a1; margin-top: 24px; }}
.badge {{ background: #e0f2fe; color: #0369a1; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
ul {{ padding-left: 20px; }}
li {{ margin-bottom: 8px; }}
.back {{ margin-bottom: 20px; display: inline-block; }}
</style>
</head>
<body>
<a class="back" href="index.html">← Back to Welfare Directory</a>
<h1>{s['title']}</h1>
<p><span class="badge">{s['category']}</span> | <strong>State:</strong> {s['state']}</p>
<h2>Direct Benefit</h2>
<p>{s['benefit']}</p>
<h2>Statutory Eligibility Criteria</h2>
<p>{s['eligibility_summary']}</p>
<h2>Required Documents & Statutory Justifications</h2>
<ul>{docs_html}</ul>
<h2>Common Rejection Pitfalls</h2>
<ul>{pitfalls_html}</ul>
<h2>Official Portal</h2>
<p><a href="{s['portal_url']}">{s['portal_url']}</a></p>
</body>
</html>
"""
            creator.add_item(SimpleZimItem(f"{s['id']}.html", s["title"], article_html))

    print(f"Successfully compiled {output_path} ({output_path.stat().st_size} bytes)")


def build_rejection_dictionary_zim(output_path: pathlib.Path) -> None:
    """Compile rejection codes into rejection_dictionary.zim."""
    if output_path.exists():
        try:
            output_path.unlink()
        except Exception:
            pass

    print(f"Building {output_path}...")
    creator = libzim.Creator(output_path)
    creator.config_indexing(True, "eng")
    creator.set_mainpath("index.html")

    with creator:
        index_html = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>JanSeva Kyun Reject Hua? Dictionary</title>
<style>
body { font-family: system-ui, sans-serif; margin: 40px; line-height: 1.6; color: #1e293b; background: #f8fafc; }
h1 { color: #dc2626; }
.card { background: white; border: 1px solid #e2e8f0; border-radius: 8px; padding: 20px; margin-bottom: 16px; }
.code { display: inline-block; background: #fee2e2; color: #b91c1c; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
a { color: #dc2626; text-decoration: none; font-weight: bold; }
</style>
</head>
<body>
<h1>📑 JanSeva Rejection Dictionary (openZIM)</h1>
<p>Offline remedial guide for decoding Indian welfare application rejection notices & error codes.</p>
"""
        for r in BASELINE_REJECTIONS:
            index_html += f"""
<div class="card">
  <span class="code">{r['code']}</span>
  <h3><a href="{r['code']}.html">{r['title']}</a></h3>
  <p><strong>Issuing System:</strong> {r['portal']}</p>
  <p>{r['what_happened']}</p>
</div>
"""
        index_html += "</body></html>"
        creator.add_item(SimpleZimItem("index.html", "JanSeva Rejection Dictionary", index_html))

        for r in BASELINE_REJECTIONS:
            plan_html = "".join([f"<li>{step}</li>" for step in r["layman_action_plan"]])
            docs_html = "".join([f"<li>📄 {doc}</li>" for doc in r["documents_required"]])

            article_html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>{r['code']}: {r['title']}</title>
<style>
body {{ font-family: system-ui, sans-serif; margin: 30px; line-height: 1.6; color: #1e293b; background: #ffffff; }}
h1 {{ color: #b91c1c; border-bottom: 2px solid #ef4444; padding-bottom: 8px; }}
h2 {{ color: #0f172a; margin-top: 24px; }}
.code {{ background: #fee2e2; color: #b91c1c; padding: 4px 8px; border-radius: 4px; font-weight: bold; }}
ol, ul {{ padding-left: 20px; }}
li {{ margin-bottom: 8px; }}
.back {{ margin-bottom: 20px; display: inline-block; }}
</style>
</head>
<body>
<a class="back" href="index.html">← Back to Rejection Dictionary</a>
<h1>{r['title']}</h1>
<p><span class="code">{r['code']}</span> | <strong>Issuing Portal:</strong> {r['portal']}</p>
<h2>1. What Happened</h2>
<p>{r['what_happened']}</p>
<h2>2. The Root Cause</h2>
<p>{r['root_cause']}</p>
<h2>3. Remedial Action Plan (Exact Steps)</h2>
<ol>{plan_html}</ol>
<h2>Mandatory Supporting Documents</h2>
<ul>{docs_html}</ul>
</body>
</html>
"""
            creator.add_item(SimpleZimItem(f"{r['code']}.html", r["title"], article_html))

    print(f"Successfully compiled {output_path} ({output_path.stat().st_size} bytes)")


if __name__ == "__main__":
    packs_dir = pathlib.Path(__file__).parent
    build_welfare_schemes_zim(packs_dir / "welfare_schemes.zim")
    build_rejection_dictionary_zim(packs_dir / "rejection_dictionary.zim")
    print("All ZIM packs built successfully!")
