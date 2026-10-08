"""Generic smart parser for arbitrary welfare, government, and NGO portals."""

import re
from typing import List, Optional
from bs4 import BeautifulSoup

from scraper.models import SchemeDocumentRequirement, WelfareSchemeArticle
from scraper.parsers.base import BaseSchemeParser
from scraper.parsers.myscheme import clean_text


class GenericWelfareParser(BaseSchemeParser):
    """Fallback parser that intelligently parses any structured welfare web page."""

    def can_parse(self, url: str, html: str) -> bool:
        # Generic parser can always attempt parsing
        return bool(html and len(html.strip()) > 50)

    def parse(self, url: str, html: str) -> Optional[WelfareSchemeArticle]:
        soup = BeautifulSoup(html, "html.parser")

        # Decompose non-content elements
        for tag in soup(["script", "style", "nav", "footer", "iframe", "noscript"]):
            tag.decompose()

        # Find Title
        title = ""
        h1 = soup.find("h1")
        if h1:
            title = clean_text(h1.get_text())
        if not title:
            title_tag = soup.find("title")
            if title_tag:
                title = clean_text(title_tag.get_text())

        if not title or len(title) < 3:
            title = "Welfare Scheme Article"

        slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")[:45]
        if not slug:
            slug = "welfare-scheme"

        # Content container
        main_container = soup.find("main") or soup.find("article") or soup.find(id=re.compile(r"content|main", re.I)) or soup.body or soup

        # Extract paragraphs
        paragraphs = [clean_text(p.get_text()) for p in main_container.find_all("p") if len(clean_text(p.get_text())) > 30]

        # Extract list items
        list_items = [clean_text(li.get_text()) for li in main_container.find_all("li") if len(clean_text(li.get_text())) > 15]

        # Benefit summary
        benefit = paragraphs[0] if paragraphs else "Government welfare and financial assistance scheme."

        # Eligibility criteria
        eligibility_items: List[str] = []
        for item in list_items:
            if any(k in item.lower() for k in ["eligib", "age", "income", "resident", "citizen", "criteria", "must be", "who can"]):
                eligibility_items.append(item)

        if not eligibility_items and list_items:
            eligibility_items = list_items[:4]

        # Document requirements
        docs: List[SchemeDocumentRequirement] = []
        for item in list_items:
            if any(k in item.lower() for k in ["aadhaar", "ration card", "certificate", "passbook", "proof", "voter id", "pan card"]):
                docs.append(SchemeDocumentRequirement(
                    name=item[:100],
                    statutory_why="Mandatory document under scheme administrative guidelines.",
                ))

        if not docs:
            docs = [
                SchemeDocumentRequirement(
                    name="Aadhaar Card",
                    statutory_why="Proof of identity under Section 7 of the Aadhaar Act, 2016.",
                ),
                SchemeDocumentRequirement(
                    name="Bank Passbook / Account Proof",
                    statutory_why="Direct Benefit Transfer routing through NPCI APBS.",
                ),
            ]

        # Department / State detection
        text_full = soup.get_text().lower()
        state = "All India"
        for st in ["Karnataka", "Maharashtra", "Tamil Nadu", "Uttar Pradesh", "Bihar", "Kerala", "Gujarat", "Rajasthan", "Madhya Pradesh"]:
            if st.lower() in text_full:
                state = st
                break

        return WelfareSchemeArticle(
            id=slug,
            title=title,
            portal_url=url,
            department="Government / Nodal Welfare Authority",
            state=state,
            category="Citizen Welfare & Social Security",
            benefit_summary=benefit[:300],
            eligibility_summary=eligibility_items[0] if eligibility_items else "Refer to official portal notification.",
            eligibility_criteria=eligibility_items[:5],
            required_documents=docs[:5],
            tags=[slug, state.lower(), "welfare"],
        )
