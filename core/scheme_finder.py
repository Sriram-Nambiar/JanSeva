"""Welfare Scheme Finder (openZIM RAG Engine).

Module 3 of JanSeva:
Queries the offline `.zim` archive via `WelfareZimEngine` at 0ms latency.
Filters schemes based on citizen demographic criteria (age, gender, landholding,
state) and renders required document checklists with statutory legal justifications.
"""

from typing import Any, Dict, List, Optional
from core.zim_engine import WelfareZimEngine


class SchemeFinder:
    """Zero-latency offline welfare scheme matcher."""

    def __init__(self, zim_engine: Optional[WelfareZimEngine] = None):
        self.zim_engine = zim_engine or WelfareZimEngine()

    def filter_schemes(
        self,
        age: Optional[int] = None,
        gender: Optional[str] = None,
        is_landowner: bool = False,
        state: str = "All India",
        category: str = "All",
        search_query: str = "",
    ) -> List[Dict[str, Any]]:
        """Filter schemes based on applicant criteria."""
        all_schemes = self.zim_engine.search_schemes(query=search_query, state=state, category=category)
        matched = []

        for s in all_schemes:
            # Check age boundary if provided
            if age is not None:
                min_age = s.get("min_age", 0)
                max_age = s.get("max_age", 100)
                if not (min_age <= age <= max_age):
                    continue

            # Check gender requirement
            s_gender = s.get("gender", "All")
            if gender and s_gender not in ("All", gender):
                continue

            # Landowner requirement (e.g. PM-KISAN)
            if s["id"] == "pm_kisan" and not is_landowner:
                continue

            matched.append(s)

        return matched

    def get_scheme_details(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Get complete details for a specific scheme."""
        return self.zim_engine.get_scheme_by_id(scheme_id)

    def get_document_legal_checklist(self, scheme_id: str) -> List[Dict[str, str]]:
        """Return the required documents with legal justifications for a given scheme."""
        scheme = self.get_scheme_details(scheme_id)
        if not scheme:
            return []
        return scheme.get("required_documents", [])
