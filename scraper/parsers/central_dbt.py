"""Parser for Central DBT & State Welfare Portals (PM-KISAN, Seva Sindhu, DBT Bharat, NFSA)."""

import re
from typing import Optional
from bs4 import BeautifulSoup

from scraper.models import SchemeDocumentRequirement, WelfareSchemeArticle
from scraper.parsers.base import BaseSchemeParser
from scraper.parsers.myscheme import clean_text


class CentralDbtParser(BaseSchemeParser):
    """Parser for DBT portals such as dbtbharat.gov.in, pmkisan.gov.in, and sevasindhu."""

    def can_parse(self, url: str, html: str) -> bool:
        norm = url.lower()
        dbt_keywords = ["dbtbharat", "pmkisan", "sevasindhu", "nfsa.gov", "pmayg", "beneficiary.nha"]
        return any(k in norm for k in dbt_keywords)

    def parse(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        soup = BeautifulSoup(html, "html.parser")

        # Extract title
        title = ""
        for tag in ["h1", "h2", "title"]:
            found = soup.find(tag)
            if found:
                title = clean_text(found.get_text())
                if title:
                    break

        if not title:
            title = "Central Direct Benefit Transfer Scheme"

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:40]

        # Extract paragraphs & lists
        paragraphs = [clean_text(p.get_text()) for p in soup.find_all("p") if len(clean_text(p.get_text())) > 25]
        
        benefit = paragraphs[0] if paragraphs else "Direct benefit transfer assistance."

        elig_items = []
        for ul in soup.find_all(["ul", "ol"]):
            for li in ul.find_all("li"):
                txt = clean_text(li.get_text())
                if txt and len(txt) > 10:
                    elig_items.append(txt)

        # Detect documents
        doc_names = []
        doc_keywords = ["aadhaar", "ration card", "passbook", "land", "rtc", "caste certificate", "income certificate"]
        for txt in elig_items + paragraphs:
            for kw in doc_keywords:
                if kw in txt.lower() and kw.title() not in doc_names:
                    doc_names.append(kw.title())

        req_docs = [
            SchemeDocumentRequirement(
                name=d,
                statutory_why="Mandatory verification under DBT Mission Guidelines 2017.",
            )
            for d in doc_names
        ] or [
            SchemeDocumentRequirement(
                name="Aadhaar Card",
                statutory_why="Section 7 Aadhaar Act mandatory identification for Direct Benefit Transfers.",
            ),
            SchemeDocumentRequirement(
                name="Bank Passbook (NPCI Seeded)",
                statutory_why="Aadhaar Payment Bridge System (APBS) mandate requirement.",
            ),
        ]

        state = "All India"
        if "sevasindhu" in url.lower() or "karnataka" in html.lower():
            state = "Karnataka"

        return WelfareSchemeArticle(
            id=slug,
            title=title,
            portal_url=url,
            department="Direct Benefit Transfer Mission / Government of India",
            state=state,
            category="Direct Benefit Transfer",
            benefit_summary=benefit[:300],
            eligibility_summary=elig_items[0] if elig_items else "Refer to official scheme notice.",
            eligibility_criteria=elig_items[:5],
            required_documents=req_docs,
            tags=[slug, state.lower(), "dbt"],
        )
