"""'Kyun Reject Hua?' Rejection Notice Decoder.

Module 2 of JanSeva:
Ingests administrative rejection slips, SMS error receipts, or PFMS status reports.
Decodes cryptic bureaucratic error codes against local openZIM archives and translates
them into an actionable 3-part layman remedial plan:
1. What happened (Plain language summary)
2. The root cause (Underlying administrative/banking reason)
3. Action checklist (Exact office to visit, exact form to request, and documents to carry)
"""

from typing import Any, Dict, List, Optional
from core.zim_engine import WelfareZimEngine


class DecodedRejectionReport:
    """Structured remedial report for citizen applicants."""

    def __init__(
        self,
        code: str,
        title: str,
        portal: str,
        what_happened: str,
        root_cause: str,
        action_plan: List[str],
        documents_required: List[str],
        zim_source: str = "openZIM rejection_dictionary.zim",
    ):
        self.code = code
        self.title = title
        self.portal = portal
        self.what_happened = what_happened
        self.root_cause = root_cause
        self.action_plan = action_plan
        self.documents_required = documents_required
        self.zim_source = zim_source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "title": self.title,
            "portal": self.portal,
            "what_happened": self.what_happened,
            "root_cause": self.root_cause,
            "action_plan": self.action_plan,
            "documents_required": self.documents_required,
            "zim_source": self.zim_source,
        }


class RejectionDecoder:
    """Decodes administrative rejection notices using openZIM knowledge packs."""

    def __init__(self, zim_engine: Optional[WelfareZimEngine] = None):
        self.zim_engine = zim_engine or WelfareZimEngine()

    def decode(self, query_code_or_text: str) -> DecodedRejectionReport:
        """Decode a rejection notice code or extracted SMS text."""
        entry = self.zim_engine.search_rejection(query_code_or_text)

        if not entry:
            # Generic fallback for unidentified codes
            return DecodedRejectionReport(
                code="UNKNOWN_ERROR",
                title=f"Administrative Query: '{query_code_or_text[:50]}...'",
                portal="State Welfare Portal / PFMS",
                what_happened="The administrative portal returned an unrecognized clerical code or general pending review status.",
                root_cause="The application could not be verified automatically against centralized databases and has been routed to manual clerical verification.",
                action_plan=[
                    "Step 1: Visit your Gram Panchayat (Grama One / Nada Kacheri) or nearest Citizen Service Center (CSC).",
                    "Step 2: Provide your application acknowledgment receipt number to the operator.",
                    "Step 3: Request the operator to pull the backend 'Reason for Objection' from the supervisor portal screen.",
                    "Step 4: Keep original Aadhaar Card, Ration Card, and Bank Passbook ready for immediate document upload.",
                ],
                documents_required=[
                    "Application Acknowledgment Receipt",
                    "Original Aadhaar Card",
                    "Bank Passbook with active IFSC",
                ],
            )

        return DecodedRejectionReport(
            code=entry["code"],
            title=entry["title"],
            portal=entry["portal"],
            what_happened=entry["what_happened"],
            root_cause=entry["root_cause"],
            action_plan=entry["layman_action_plan"],
            documents_required=entry["documents_required"],
            zim_source="openZIM rejection_dictionary.zim" if self.zim_engine.is_zim_active else "JanSeva Local Rejection Engine",
        )
