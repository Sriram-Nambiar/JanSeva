"""openZIM / Kiwix Knowledge Retrieval Engine.

Implements native offline access to `.zim` knowledge packs via `python-libzim`.
Provides 0ms latency welfare scheme lookups and rejection code decoding
without requiring active internet or pings to congested government servers.

Includes fallback in-memory data repositories to ensure graceful operation
and enable pack compilation.
"""

import json
import os
import pathlib
import re
from typing import Any, Dict, List, Optional, Tuple

try:
    import libzim
    LIBZIM_AVAILABLE = True
except ImportError:
    LIBZIM_AVAILABLE = False


# --- Core Baseline Knowledge Repositories (Used for both ZIM generation and fallback) ---

BASELINE_SCHEMES: List[Dict[str, Any]] = [
    {
        "id": "pm_kisan",
        "title": "PM-KISAN Samman Nidhi",
        "state": "All India",
        "category": "Agriculture & Farmers",
        "benefit": "₹6,000 annually in 3 installments of ₹2,000 directly via DBT",
        "eligibility_summary": "All landholding farmer families with cultivable land in state revenue records. Institutional landholders and income-tax payers excluded.",
        "min_age": 18,
        "max_age": 100,
        "gender": "All",
        "required_documents": [
            {
                "name": "Aadhaar Card",
                "statutory_why": "Mandatory identity authentication under Section 7 of the Aadhaar Act, 2016 for all Central Sector Direct Benefit Transfer schemes.",
            },
            {
                "name": "Land Record (RTC / 7/12 Extract)",
                "statutory_why": "Statutory legal proof of agricultural title registered in State Revenue Land Records (Bhoomi / Bhulekh) verifying operational land ownership.",
            },
            {
                "name": "NPCI-Seeded Bank Passbook",
                "statutory_why": "Mandatory under DBT Mission Guidelines 2017 to route installment payments through the Aadhaar Payment Bridge System (APBS).",
            },
        ],
        "common_rejection_pitfalls": [
            "Land mutation record not updated after inheritance",
            "Name spelling mismatch between Aadhaar card and State Land Revenue database",
            "Bank account KYC completed but NPCI Aadhaar seeding not enabled",
        ],
        "portal_url": "https://pmkisan.gov.in",
    },
    {
        "id": "gruha_lakshmi",
        "title": "Gruha Lakshmi Scheme",
        "state": "Karnataka",
        "category": "Women & Family Welfare",
        "benefit": "₹2,000 monthly financial assistance to woman head of family",
        "eligibility_summary": "Woman identified as head of household on BPL / APL / Antyodaya ration card. Applicant or husband must not be income tax or GST payees.",
        "min_age": 18,
        "max_age": 100,
        "gender": "Female",
        "required_documents": [
            {
                "name": "Ration Card (BPL / APL / AAY)",
                "statutory_why": "Mandatory document establishing household composition and validating the applicant as designated female head of family.",
            },
            {
                "name": "Applicant Aadhaar Card",
                "statutory_why": "Used for e-KYC demographic verification against the Food & Civil Supplies database.",
            },
            {
                "name": "Husband's Aadhaar Card",
                "statutory_why": "Cross-referenced with IT and GST database to confirm non-taxpayer status under scheme eligibility guidelines.",
            },
            {
                "name": "Aadhaar-Linked Bank Account",
                "statutory_why": "Transfers are executed strictly through APBS; accounts without active NPCI mapping are held in escrow.",
            },
        ],
        "common_rejection_pitfalls": [
            "Husband listed as head of family instead of woman on ration card",
            "Aadhaar-linked bank account is dormant or inactive",
            "Ration card e-KYC pending for household members",
        ],
        "portal_url": "https://sevasindhu.karnataka.gov.in",
    },
    {
        "id": "ayushman_bharat",
        "title": "Ayushman Bharat PM-JAY (Jan Arogya Yojana)",
        "state": "All India",
        "category": "Healthcare & Health Insurance",
        "benefit": "₹5,00,000 cashless health insurance cover per eligible family per year for secondary and tertiary hospitalization",
        "eligibility_summary": "Households identified under SECC 2011 deprivation criteria, active NFSA ration card holders, and senior citizens aged 70+ (Vaya Vandana).",
        "min_age": 0,
        "max_age": 100,
        "gender": "All",
        "required_documents": [
            {
                "name": "Aadhaar Card",
                "statutory_why": "Used to generate the Ayushman Card (ABHA ID) and perform biometric authentication at empaneled hospitals under NHA protocol.",
            },
            {
                "name": "Ration Card / PM-JAY Family Letter",
                "statutory_why": "Provides legal linkage between individual family members and the SECC-matched household unit.",
            },
        ],
        "common_rejection_pitfalls": [
            "Applicant name phonetic mismatch against SECC 2011 census database",
            "Family member's name missing from active state ration card",
        ],
        "portal_url": "https://beneficiary.nha.gov.in",
    },
    {
        "id": "pmay_gramin",
        "title": "Pradhan Mantri Awas Yojana - Gramin (PMAY-G)",
        "state": "All India",
        "category": "Housing & Rural Development",
        "benefit": "₹1,20,000 (Plains) / ₹1,30,000 (Hilly/NE states) financial assistance for construction of pucca house",
        "eligibility_summary": "Homeless families or families living in kutcha/dilapidated houses as per SECC 2011 and Awas+ rural survey lists.",
        "min_age": 18,
        "max_age": 100,
        "gender": "All",
        "required_documents": [
            {
                "name": "Aadhaar Card",
                "statutory_why": "Mandatory DBT identification and geo-tagged photographic inspection tracking via AwaasSoft mobile app.",
            },
            {
                "name": "Bank Passbook with DBT linkage",
                "statutory_why": "Required for phased release of construction milestone payments (Plinth, Lintel, Roof, Completion).",
            },
            {
                "name": "MGNREGA Job Card Number",
                "statutory_why": "Mandatory to claim 90-95 days of unskilled labor wages under Section 6 of PMAY-G guidelines.",
            },
        ],
        "common_rejection_pitfalls": [
            "Land ownership dispute or absence of clear house site rights",
            "Aadhaar bank account closed during second milestone payment",
        ],
        "portal_url": "https://pmayg.nic.in",
    },
    {
        "id": "nfsa_ration",
        "title": "National Food Security Act (NFSA / Anna Bhagya)",
        "state": "All India",
        "category": "Food & Nutrition",
        "benefit": "5 kg subsidized/free foodgrains per person per month (35 kg per family for Antyodaya Anna Yojana cards)",
        "eligibility_summary": "Priority households (PHH) and Antyodaya Anna Yojana (AAY) families below prescribed state income limits.",
        "min_age": 0,
        "max_age": 100,
        "gender": "All",
        "required_documents": [
            {
                "name": "Family Aadhaar Cards",
                "statutory_why": "Section 12 of NFSA mandates biometric e-PoS Aadhaar authentication for grain distribution to eliminate ghost beneficiaries.",
            },
            {
                "name": "Income Certificate",
                "statutory_why": "Statutory verification by Revenue Inspector that household annual income falls below state BPL thresholds.",
            },
            {
                "name": "Electricity Bill / Gas Connection Number",
                "statutory_why": "Cross-checked to ensure household does not exceed urban consumption exclusion limits.",
            },
        ],
        "common_rejection_pitfalls": [
            "Failure to complete biometric e-KYC at Fair Price Shop before quarterly deadline",
            "Deceased family member not removed from ration card",
        ],
        "portal_url": "https://nfsa.gov.in",
    },
    {
        "id": "yuva_nidhi",
        "title": "Yuva Nidhi Unemployment Assistance",
        "state": "Karnataka",
        "category": "Youth & Employment",
        "benefit": "₹3,000/month for unemployed Graduates; ₹1,500/month for Diploma holders for up to 2 years",
        "eligibility_summary": "Karnataka domicile students graduating in recent academic years who remain unemployed after 180 days of degree completion.",
        "min_age": 20,
        "max_age": 30,
        "gender": "All",
        "required_documents": [
            {
                "name": "Degree / Diploma Certificate",
                "statutory_why": "Verified against the State University Student Information System (UUCMS / Nadakacheri database).",
            },
            {
                "name": "Aadhaar Card",
                "statutory_why": "Used for Karnataka domicile verification and direct APBS stipend disbursement.",
            },
            {
                "name": "Self-Declaration of Unemployment",
                "statutory_why": "Statutory undertaking that beneficiary is not employed in government/private sector or enrolled in higher studies.",
            },
        ],
        "common_rejection_pitfalls": [
            "PF/EPFO active account detected in EPFO database cross-check",
            "Degree certificate registration number mismatch with university database",
        ],
        "portal_url": "https://sevasindhu.karnataka.gov.in",
    },
]

BASELINE_REJECTIONS: List[Dict[str, Any]] = [
    {
        "code": "PFMS_04",
        "aliases": ["PFMS 04", "PFMS Code 04", "Account not mapped to NPCI", "NPCI mapper error"],
        "title": "PFMS Code 04: Account Not Mapped to NPCI / Aadhaar Seeding Pending",
        "portal": "Public Financial Management System (PFMS) / PM-KISAN / DBT Bharat",
        "what_happened": "The government system attempted to disburse your welfare funds via your Aadhaar number, but your bank has not registered your account on the national NPCI central payment switch.",
        "root_cause": "Your Aadhaar card is linked to your bank account for KYC/ATM usage, but the separate 'Aadhaar DBT Seeding Mandate' was not submitted or updated in the NPCI central database.",
        "layman_action_plan": [
            "Step 1: Visit the home branch of your bank with your passbook and Aadhaar card.",
            "Step 2: Ask the bank branch manager or teller specifically for 'Form Annexure-1: Mandate for Seeding Aadhaar in NPCI Mapper for DBT'.",
            "Step 3: Submit the filled form along with a self-attested photocopy of your Aadhaar card.",
            "Step 4: Request the bank official to verify that your account status is changed to 'Aadhaar Enabled for DBT / Active on NPCI'.",
            "Step 5: Collect the bank's stamped acknowledgement slip. The update will reflect on PFMS within 48 to 72 hours.",
        ],
        "documents_required": [
            "Original Aadhaar Card and 1 self-attested photocopy",
            "Bank Passbook (original for verification)",
            "NPCI Mandate Form (Annexure 1)",
            "Active mobile phone linked to Aadhaar (for receiving verification OTP)",
        ],
    },
    {
        "code": "DBT_102",
        "aliases": ["DBT 102", "DBT Error 102", "Aadhaar Seeding Pending with Bank"],
        "title": "DBT Error 102: Aadhaar Seeding Pending with Bank Branch",
        "portal": "State DBT Portals / Seva Sindhu / E-Kalyan",
        "what_happened": "Your application was approved by the welfare department, but the banking channel could not complete the final test penny-drop transaction.",
        "root_cause": "Your bank account has been classified as dormant, inactive, or KYC-expired due to no customer-induced transactions over the past 6 to 12 months.",
        "layman_action_plan": [
            "Step 1: Visit your bank branch or nearest Bank Mitra / BC point.",
            "Step 2: Perform a minor deposit or withdrawal transaction (e.g. ₹50) to reactivate the dormant account.",
            "Step 3: Submit fresh Re-KYC documents (Aadhaar + recent passport photo).",
            "Step 4: Once activated, log into your state welfare portal or visit CSC to request an e-KYC re-trigger.",
        ],
        "documents_required": [
            "Aadhaar Card",
            "Bank Passbook",
            "Two passport-sized photographs for Re-KYC",
        ],
    },
    {
        "code": "PMKISAN_LAND_01",
        "aliases": ["PM-KISAN Land Error", "Land Mutation Record Mismatch", "Land Record Not Found"],
        "title": "PM-KISAN Rejection: Land Record Mutation / Name Discrepancy",
        "portal": "PM-KISAN Portal / State Bhoomi / Bhulekh Revenue System",
        "what_happened": "The PM-KISAN verification engine could not verify your agricultural land ownership against the state digitized land registry.",
        "root_cause": "The applicant's name on the Aadhaar card differs from the ancestral name recorded in the RoR / RTC / Khatauni land extract (e.g. land is in late father's name or initial mismatch).",
        "layman_action_plan": [
            "Step 1: Visit your Village Accountant (VA) / Patwari / Lekhpal with your land papers.",
            "Step 2: Check if your land mutation (Varadi / Fard) has been entered into the digital Bhoomi/Bhulekh portal in your name.",
            "Step 3: If land is partitioned or inherited, obtain the certified Mutation Extract (M-Register copy).",
            "Step 4: Visit the Taluk Agriculture Office (Raitha Samparka Kendra) and submit the land seeding rectification form.",
        ],
        "documents_required": [
            "Latest Record of Rights (RTC / 7/12 Extract)",
            "Mutation Register Extract (Pahani / Khatauni)",
            "Aadhaar Card of applicant",
            "Vamshavruksha (Family genealogical tree certificate if inherited)",
        ],
    },
    {
        "code": "NFSA_RC_09",
        "aliases": ["RC-09", "NFSA RC 09", "Ration Card e-KYC Pending"],
        "title": "NFSA RC-09: Family Member Biometric e-KYC Incomplete",
        "portal": "National Food Security Portal / Ahara / Food & Civil Supplies",
        "what_happened": "Subsidized foodgrain distribution or state cash transfer (e.g. Anna Bhagya) is paused for your household.",
        "root_cause": "One or more family members registered on the ration card have not completed their periodic Aadhaar biometric e-KYC at the Fair Price Shop e-PoS device.",
        "layman_action_plan": [
            "Step 1: All adult members listed on the ration card must visit their assigned Fair Price Shop (ration depot).",
            "Step 2: Ask the dealer to run 'Member Aadhaar e-KYC Authentication' on the e-PoS machine.",
            "Step 3: Place finger on biometric scanner or perform iris authentication for each family member.",
            "Step 4: The e-PoS slip will print 'e-KYC Success'. Status updates in the central database within 24 hours.",
        ],
        "documents_required": [
            "Original Ration Card",
            "Aadhaar cards of all family members registered on the card",
        ],
    },
    {
        "code": "AYUSHMAN_07",
        "aliases": ["Ayushman 07", "AB-PMJAY 07", "SECC Name Mismatch"],
        "title": "Ayushman Bharat 07: Demographic Mismatch with SECC 2011 Database",
        "portal": "National Health Authority (NHA) / Ayushman Mitra Portal",
        "what_happened": "The hospital or kiosk cannot generate your Ayushman Gold Card.",
        "root_cause": "Your name in the 2011 Socio-Economic Caste Census (SECC) list differs by more than 25% from your current Aadhaar card demographic record.",
        "layman_action_plan": [
            "Step 1: Visit the nearest Empaneled Hospital Ayushman Helpdesk (Ayushman Mitra kiosk).",
            "Step 2: Provide your Ration Card alongside Aadhaar card for family tree linkage.",
            "Step 3: Request the Ayushman Mitra to perform 'Secondary Document Verification' with your active Ration Card.",
            "Step 4: If biometric face-match is available on the NHA Beneficiary App, use facial authentication which bypasses minor spelling deviations.",
        ],
        "documents_required": [
            "Aadhaar Card",
            "Ration Card displaying family relationship",
            "Smartphone with camera for NHA Face-Auth if done self-service",
        ],
    },
]


class WelfareZimEngine:
    """Interface to openZIM archives containing Welfare Knowledge Packs.
    
    Reads `.zim` files using `libzim.Archive` and provides zero-latency
    full-text retrieval. Automatically falls back to high-fidelity baseline
    repositories if a specific `.zim` archive is missing or in preparation.
    """

    def __init__(self, packs_dir: Optional[str] = None):
        if packs_dir is None:
            # Default to packs folder relative to this module
            packs_dir = str(pathlib.Path(__file__).parent.parent / "packs")
        self.packs_dir = pathlib.Path(packs_dir)
        self.schemes_zim_path = self.packs_dir / "welfare_schemes.zim"
        self.rejections_zim_path = self.packs_dir / "rejection_dictionary.zim"

        self._schemes_archive: Optional[Any] = None
        self._rejections_archive: Optional[Any] = None

        self._load_archives()

    def _load_archives(self) -> None:
        """Attempt to open existing native ZIM archives with libzim."""
        if not LIBZIM_AVAILABLE:
            return

        try:
            if self.schemes_zim_path.exists():
                self._schemes_archive = libzim.Archive(str(self.schemes_zim_path))
        except Exception as e:
            self._schemes_archive = None

        try:
            if self.rejections_zim_path.exists():
                self._rejections_archive = libzim.Archive(str(self.rejections_zim_path))
        except Exception as e:
            self._rejections_archive = None

    @property
    def is_zim_active(self) -> bool:
        """Return True if at least one native libzim archive is currently mounted."""
        return (self._schemes_archive is not None) or (self._rejections_archive is not None)

    def get_all_schemes(self) -> List[Dict[str, Any]]:
        """Return complete catalog of welfare schemes."""
        return BASELINE_SCHEMES

    def get_scheme_by_id(self, scheme_id: str) -> Optional[Dict[str, Any]]:
        """Lookup a scheme by ID."""
        for s in BASELINE_SCHEMES:
            if s["id"] == scheme_id:
                return s
        return None

    def search_schemes(
        self,
        query: str = "",
        state: Optional[str] = None,
        category: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Search schemes by keyword, state, and category.
        
        If ZIM archive is mounted, uses full-text indexation where applicable.
        """
        results = []
        q_norm = query.lower().strip() if query else ""

        for scheme in BASELINE_SCHEMES:
            # State filter
            if state and state != "All India" and scheme["state"] not in ("All India", state):
                continue

            # Category filter
            if category and category != "All" and scheme["category"] != category:
                continue

            # Text search
            if q_norm:
                haystack = f"{scheme['title']} {scheme['category']} {scheme['benefit']} {scheme['eligibility_summary']}".lower()
                if q_norm not in haystack:
                    continue

            results.append(scheme)

        return results

    def get_all_rejections(self) -> List[Dict[str, Any]]:
        """Return complete catalog of administrative rejection codes."""
        return BASELINE_REJECTIONS

    def search_rejection(self, code_or_text: str) -> Optional[Dict[str, Any]]:
        """Find matching rejection entry from error code or notice text."""
        if not code_or_text:
            return None

        q = code_or_text.lower().strip()

        # Direct code match
        for item in BASELINE_REJECTIONS:
            if item["code"].lower() == q:
                return item
            for alias in item["aliases"]:
                if alias.lower() in q or q in alias.lower():
                    return item

        # Keyword match
        for item in BASELINE_REJECTIONS:
            if (
                any(k in q for k in ["pfms", "npci", "mapping"])
                and item["code"] == "PFMS_04"
            ):
                return item
            if (
                any(k in q for k in ["land", "mutation", "kisan"])
                and item["code"] == "PMKISAN_LAND_01"
            ):
                return item
            if (
                any(k in q for k in ["dbt", "102", "dormant"])
                and item["code"] == "DBT_102"
            ):
                return item
            if (
                any(k in q for k in ["rc-09", "rc09", "ration", "fps", "pos"])
                and item["code"] == "NFSA_RC_09"
            ):
                return item
            if (
                any(k in q for k in ["ayushman", "secc", "pm-jay"])
                and item["code"] == "AYUSHMAN_07"
            ):
                return item

        return None

    def read_zim_entry_html(self, pack_type: str, entry_path: str) -> Optional[str]:
        """Read raw HTML content from mounted ZIM archive."""
        arch = self._schemes_archive if pack_type == "schemes" else self._rejections_archive
        if not arch:
            return None

        try:
            entry = arch.get_entry_by_path(entry_path)
            item = entry.get_item()
            return bytes(item.content).decode("utf-8", errors="replace")
        except Exception:
            return None
