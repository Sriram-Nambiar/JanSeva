"""Parser for MyScheme Portal (https://myscheme.gov.in).

Supports extracting structured data from both Next.js __NEXT_DATA__ hydration JSON
and static semantic HTML DOM structures.
"""

import json
import re
from typing import Any, Dict, List, Optional
from bs4 import BeautifulSoup

from scraper.models import SchemeDocumentRequirement, WelfareSchemeArticle
from scraper.parsers.base import BaseSchemeParser


def clean_text(text: str) -> str:
    """Normalize whitespace and strip HTML remnants."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", text).strip()


class MySchemeParser(BaseSchemeParser):
    """Parser for MyScheme (myscheme.gov.in)."""

    def can_parse(self, url: str, html: str) -> bool:
        norm_url = url.lower()
        if "myscheme.gov.in" in norm_url:
            return True
        if "__NEXT_DATA__" in html and "myscheme" in html.lower():
            return True
        return False

    def parse(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        # Try JSON extraction from __NEXT_DATA__ first
        article_from_json = self._parse_next_data_json(url, html)
        if article_from_json:
            return article_from_json

        # Fallback to HTML DOM extraction
        return self._parse_html_dom(url, html)

    def _parse_next_data_json(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json">([^<]+)</script>', html)
        if not match:
            return None

        try:
            payload = json.loads(match.group(1))
            props = payload.get("props", {}).get("pageProps", {})
            scheme_data = props.get("schemeData") or props.get("scheme") or props.get("data")
            if not scheme_data or not isinstance(scheme_data, dict):
                return None

            basic_details = scheme_data.get("basicDetails", {})
            title = basic_details.get("schemeName") or scheme_data.get("title") or "Welfare Scheme"
            slug = basic_details.get("slug") or re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
            
            dept = basic_details.get("nodalMinistryName") or basic_details.get("department") or "Government of India"
            state = basic_details.get("state") or "All India"
            category = basic_details.get("schemeCategory") or "General Welfare"
            benefit_summary = clean_text(scheme_data.get("benefits", {}).get("summary", "") or basic_details.get("briefDescription", ""))
            
            eligibility_raw = scheme_data.get("eligibility", {})
            elig_desc = clean_text(eligibility_raw.get("description", ""))
            elig_criteria = [clean_text(c) for c in eligibility_raw.get("criteria", []) if clean_text(c)]

            documents_raw = scheme_data.get("documents", {}).get("requiredDocuments", [])
            req_docs = []
            for d in documents_raw:
                doc_name = d.get("documentName") if isinstance(d, dict) else str(d)
                req_docs.append(SchemeDocumentRequirement(
                    name=clean_text(doc_name),
                    statutory_why="Mandatory document under scheme administrative guidelines.",
                ))

            app_process = []
            process_raw = scheme_data.get("applicationProcess", {}).get("steps", [])
            for s in process_raw:
                step_text = s.get("description") if isinstance(s, dict) else str(s)
                if step_text:
                    app_process.append(clean_text(step_text))

            return WelfareSchemeArticle(
                id=slug,
                title=title,
                portal_url=url,
                department=dept,
                state=state,
                category=category,
                benefit_summary=benefit_summary,
                eligibility_summary=elig_desc or (elig_criteria[0] if elig_criteria else ""),
                eligibility_criteria=elig_criteria,
                required_documents=req_docs,
                application_process=app_process,
                common_rejection_pitfalls=[],
                tags=[slug, category.lower(), state.lower()],
            )
        except Exception:
            return None

    def _parse_html_dom(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        soup = BeautifulSoup(html, "html.parser")
        
        # Title
        h1 = soup.find("h1")
        title = clean_text(h1.get_text()) if h1 else ""
        if not title:
            title_tag = soup.find("title")
            title = clean_text(title_tag.get_text()) if title_tag else "Welfare Scheme"
            title = re.sub(r"\s*\|\s*myScheme.*$", "", title, flags=re.I).strip()

        if not title:
            return None

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")

        # Department / Ministry
        dept = "Government of India"
        for sel in [".nodal-ministry", ".ministry", "[data-testid='ministry-name']", ".department"]:
            el = soup.select_one(sel)
            if el:
                dept = clean_text(el.get_text())
                break

        # State
        state = "All India"
        for sel in [".state-badge", "[data-testid='state-name']", ".scheme-state"]:
            el = soup.select_one(sel)
            if el:
                state = clean_text(el.get_text())
                break

        # Benefits
        benefits = ""
        b_section = soup.find(id=re.compile(r"benefit", re.I)) or soup.find(class_=re.compile(r"benefit", re.I))
        if b_section:
            benefits = clean_text(b_section.get_text())

        # Eligibility
        elig_criteria = []
        e_section = soup.find(id=re.compile(r"eligib", re.I)) or soup.find(class_=re.compile(r"eligib", re.I))
        if e_section:
            for li in e_section.find_all("li"):
                txt = clean_text(li.get_text())
                if txt and len(txt) > 5:
                    elig_criteria.append(txt)

        # Documents
        req_docs = []
        d_section = soup.find(id=re.compile(r"doc", re.I)) or soup.find(class_=re.compile(r"doc", re.I))
        if d_section:
            for li in d_section.find_all("li"):
                txt = clean_text(li.get_text())
                if txt:
                    req_docs.append(SchemeDocumentRequirement(
                        name=txt,
                        statutory_why="Statutory verification under scheme guidelines.",
                    ))

        return WelfareSchemeArticle(
            id=slug,
            title=title,
            portal_url=url,
            department=dept,
            state=state,
            category="General Welfare",
            benefit_summary=benefits[:250] if benefits else "Financial and social support under scheme provisions.",
            eligibility_summary=elig_criteria[0] if elig_criteria else "Refer to statutory eligibility guidelines.",
            eligibility_criteria=elig_criteria,
            required_documents=req_docs,
            tags=[slug, state.lower()],
        )
