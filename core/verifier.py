"""Preflight Verification & Application Readiness Scoring Engine.

Implements deterministic cross-document validation algorithms designed
specifically for Indian citizen documentation patterns (Aadhaar, Ration Card,
Bank Passbook, Voter ID).

Evaluates clerical discrepancies (initials vs full name, YOB vs exact date,
honorific differences) and calculates an Application Readiness Score (0-100%)
to eliminate the 15-20% clerical rejection backlog before portal submission.
"""

import re
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple
from rapidfuzz import fuzz

HONORIFICS = {"shri", "sri", "smt", "shrimati", "kumari", "mr", "mrs", "ms", "late"}


class DiscrepancySeverity(str, Enum):
    PASS = "PASS"
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class VerificationCheck:
    def __init__(
        self,
        field_name: str,
        doc_a_label: str,
        doc_a_value: str,
        doc_b_label: str,
        doc_b_value: str,
        severity: DiscrepancySeverity,
        message: str,
        remediation: str,
        dbt_impact: str,
        score_deduction: int = 0,
    ):
        self.field_name = field_name
        self.doc_a_label = doc_a_label
        self.doc_a_value = doc_a_value
        self.doc_b_label = doc_b_label
        self.doc_b_value = doc_b_value
        self.severity = severity
        self.message = message
        self.remediation = remediation
        self.dbt_impact = dbt_impact
        self.score_deduction = score_deduction

    def to_dict(self) -> Dict[str, Any]:
        return {
            "field_name": self.field_name,
            "doc_a_label": self.doc_a_label,
            "doc_a_value": self.doc_a_value,
            "doc_b_label": self.doc_b_label,
            "doc_b_value": self.doc_b_value,
            "severity": self.severity.value,
            "message": self.message,
            "remediation": self.remediation,
            "dbt_impact": self.dbt_impact,
            "score_deduction": self.score_deduction,
        }


def normalize_name(name: str) -> List[str]:
    """Clean name tokens, strip honorifics and punctuation."""
    if not name:
        return []
    cleaned = re.sub(r"[^\w\s]", " ", name.lower())
    tokens = [t for t in cleaned.split() if t and t not in HONORIFICS]
    return tokens


def compare_names(name_a: str, name_b: str) -> Tuple[DiscrepancySeverity, str, str, str, int]:
    """Evaluate name consistency across two Indian identity documents.
    
    Handles:
    - Exact match
    - Initials expansion (e.g. "Ramesh K" vs "Ramesh Kumar")
    - Token reordering (e.g. "Kumar Ramesh" vs "Ramesh Kumar")
    - Minor phonetic / typo differences (e.g. "Lakshmi" vs "Laxmi")
    """
    if not name_a or not name_b:
        return (
            DiscrepancySeverity.CRITICAL,
            "Missing applicant name on one of the ingested documents.",
            "Ensure both uploaded documents are legible and clearly display applicant's name.",
            "Portal submission will be instantly rejected due to incomplete mandatory field.",
            35,
        )

    tokens_a = normalize_name(name_a)
    tokens_b = normalize_name(name_b)

    str_a = " ".join(tokens_a)
    str_b = " ".join(tokens_b)

    if str_a == str_b:
        return (
            DiscrepancySeverity.PASS,
            f"Names match identically: '{name_a}'",
            "No action needed.",
            "Zero clerical mismatch risk on DBT portal name verification.",
            0,
        )

    # Check for initials expansion (e.g. ['ramesh', 'k'] vs ['ramesh', 'kumar'])
    # Very common in South Indian records
    is_initials_variation = False
    if len(tokens_a) == len(tokens_b):
        differences = 0
        for ta, tb in zip(tokens_a, tokens_b):
            if ta != tb:
                differences += 1
                if (len(ta) == 1 and tb.startswith(ta)) or (len(tb) == 1 and ta.startswith(tb)):
                    is_initials_variation = True
                else:
                    is_initials_variation = False
                    break
        if differences == 1 and is_initials_variation:
            return (
                DiscrepancySeverity.WARNING,
                f"Initials discrepancy detected: '{name_a}' vs '{name_b}' (Initial expanded to full surname).",
                "Keep a self-declaration affidavit or Annexure-I ready. At Grama One/CSC, request operator to use Aadhaar demographic name as primary.",
                "Automated DBT matching might pause for manual officer verification if similarity threshold is set to 100%.",
                15,
            )

    # Check token set match (order independent)
    set_a = set(tokens_a)
    set_b = set(tokens_b)
    if set_a == set_b:
        return (
            DiscrepancySeverity.INFO,
            f"Word order inverted: '{name_a}' vs '{name_b}' (Surname first vs given name first).",
            "Verify with operator that first name and last name fields are mapped accurately in the portal.",
            "Most state DBT portals accept inverted token orders, but bank NPCI seeding requires exact match.",
            5,
        )

    # Fuzzy similarity calculation
    ratio = fuzz.token_sort_ratio(str_a, str_b)
    if ratio >= 88:
        return (
            DiscrepancySeverity.WARNING,
            f"Minor spelling variation ({ratio}% match): '{name_a}' vs '{name_b}'.",
            "Submit a Gazette notification or local Panchayat name variation certificate if portal returns PFMS mismatch.",
            "PFMS automated name-validation algorithm flags spelling distance < 90%.",
            15,
        )
    elif ratio >= 65:
        return (
            DiscrepancySeverity.WARNING,
            f"Moderate name mismatch ({ratio}% match): '{name_a}' vs '{name_b}'.",
            "High risk of rejection. Update either Ration Card or Aadhaar demographic details at nearest kiosk prior to submission.",
            "Significant risk of DBT rejection under PFMS Rule 4 (Beneficiary Name Mismatch).",
            25,
        )
    else:
        return (
            DiscrepancySeverity.CRITICAL,
            f"Critical name mismatch ({ratio}% match): '{name_a}' vs '{name_b}'.",
            "Do NOT submit application with these documents. Reconcile identity records at UIDAI / Food Dept before applying.",
            "Guaranteed automatic rejection by DBT engine.",
            40,
        )


def parse_indian_date(date_str: str) -> Optional[Dict[str, int]]:
    """Parse various Indian document date representations:
    - 15/08/1982, 15-08-1982, 1982-08-15
    - Year of birth only: 'YOB: 1982' or '1982'
    """
    if not date_str:
        return None
    cleaned = date_str.strip()
    
    # Try year-only match
    yob_match = re.search(r"\b(19\d{2}|20\d{2})\b", cleaned)
    year_only = None
    if yob_match:
        year_only = int(yob_match.group(1))

    # Try full date patterns
    patterns = [
        r"(\d{1,2})[\/\-\.](\d{1,2})[\/\-\.](\d{4})",  # DD/MM/YYYY
        r"(\d{4})[\/\-\.](\d{1,2})[\/\-\.](\d{1,2})",  # YYYY/MM/DD
    ]
    for pat in patterns:
        m = re.search(pat, cleaned)
        if m:
            parts = [int(p) for p in m.groups()]
            if parts[0] > 1900:  # YYYY/MM/DD
                return {"year": parts[0], "month": parts[1], "day": parts[2], "is_yob_only": False}
            else:  # DD/MM/YYYY
                return {"year": parts[2], "month": parts[1], "day": parts[0], "is_yob_only": False}

    if year_only:
        return {"year": year_only, "month": 0, "day": 0, "is_yob_only": True}
    return None


def compare_dob(dob_a: str, dob_b: str) -> Tuple[DiscrepancySeverity, str, str, str, int]:
    """Verify Date of Birth consistency across documents."""
    if not dob_a or not dob_b:
        return (
            DiscrepancySeverity.WARNING,
            "Date of birth missing on one of the scanned documents.",
            "Verify date of birth manually from birth certificate or school transfer certificate.",
            "May trigger portal flag if scheme has strict age criteria (e.g. PM-KISAN, Old Age Pension).",
            10,
        )

    parsed_a = parse_indian_date(dob_a)
    parsed_b = parse_indian_date(dob_b)

    if not parsed_a or not parsed_b:
        return (
            DiscrepancySeverity.INFO,
            f"Dates unparsed in standard format: '{dob_a}' vs '{dob_b}'.",
            "Manually confirm date before submitting.",
            "Minor clerical scrutiny.",
            5,
        )

    if parsed_a["year"] != parsed_b["year"]:
        return (
            DiscrepancySeverity.CRITICAL,
            f"Birth year discrepancy: {parsed_a['year']} vs {parsed_b['year']} ('{dob_a}' vs '{dob_b}').",
            "Update Date of Birth on Aadhaar card using School Leaving Certificate or Municipal Birth Certificate.",
            "Immediate disqualification in age-gated welfare schemes (e.g., SSP Old Age Pension, Yuva Nidhi).",
            30,
        )

    # Years match, check if one is YOB only (Aadhaar legacy issue)
    if parsed_a["is_yob_only"] or parsed_b["is_yob_only"]:
        return (
            DiscrepancySeverity.WARNING,
            f"Partial DOB match: Birth year ({parsed_a['year']}) matches, but one card records Year of Birth only.",
            "Many early Aadhaar cards record only YOB. Submit Ration Card or Voter ID as primary proof of day/month.",
            "Acceptable on most welfare portals if age calculated from YOB qualifies.",
            8,
        )

    # Both have full dates
    if (parsed_a["month"] == parsed_b["month"]) and (parsed_a["day"] == parsed_b["day"]):
        return (
            DiscrepancySeverity.PASS,
            f"Date of birth matches identically: {parsed_a['day']:02d}/{parsed_a['month']:02d}/{parsed_a['year']}",
            "No action needed.",
            "Zero rejection risk on DOB validation.",
            0,
        )
    else:
        return (
            DiscrepancySeverity.WARNING,
            f"Day/Month mismatch: '{dob_a}' vs '{dob_b}' (Year {parsed_a['year']} matches).",
            "Discrepancy in day/month may cause rejection in direct portal e-KYC validation.",
            "Update Aadhaar demographic details at nearest Post Office/CSC.",
            15,
        )


def compare_gender(gender_a: str, gender_b: str) -> Tuple[DiscrepancySeverity, str, str, str, int]:
    """Validate gender consistency across documents."""
    if not gender_a or not gender_b:
        return (DiscrepancySeverity.INFO, "Gender field missing on one card.", "Verify manually.", "Low risk.", 2)

    ga = gender_a.strip().lower()
    gb = gender_b.strip().lower()

    norm_a = "female" if ga.startswith("f") or "महिला" in ga else "male" if ga.startswith("m") or "पुरुष" in ga else ga
    norm_b = "female" if gb.startswith("f") or "महिला" in gb else "male" if gb.startswith("m") or "पुरुष" in gb else gb

    if norm_a == norm_b:
        return (DiscrepancySeverity.PASS, f"Gender matches: {norm_a.title()}", "No action needed.", "No risk.", 0)
    else:
        return (
            DiscrepancySeverity.CRITICAL,
            f"Gender mismatch detected: '{gender_a}' vs '{gender_b}'.",
            "Correct gender record on Aadhaar/Ration card immediately.",
            "Immediate rejection for gender-specific schemes (e.g. Gruha Lakshmi, PMMVY, Shakti).",
            35,
        )


def compare_father_or_spouse(name_a: str, name_b: str) -> Tuple[DiscrepancySeverity, str, str, str, int]:
    """Validate Father / Husband / Guardian name consistency."""
    if not name_a or not name_b:
        return (
            DiscrepancySeverity.INFO,
            "Guardian/Father/Spouse name missing on one document.",
            "Cross-verify with family ration card if available.",
            "Typically secondary check on DBT portals.",
            4,
        )

    tokens_a = normalize_name(name_a)
    tokens_b = normalize_name(name_b)

    ratio = fuzz.token_sort_ratio(" ".join(tokens_a), " ".join(tokens_b))
    if ratio >= 85:
        return (
            DiscrepancySeverity.PASS,
            f"Father/Guardian name aligns: '{name_a}' vs '{name_b}' ({ratio}% match).",
            "No action needed.",
            "Passes secondary relationship verification.",
            0,
        )
    elif ratio >= 60:
        return (
            DiscrepancySeverity.WARNING,
            f"Father/Guardian name discrepancy: '{name_a}' vs '{name_b}' ({ratio}% match).",
            "Confirm guardian identity with Gram Panchayat village accountant if needed.",
            "Low-to-medium risk depending on scheme rules.",
            10,
        )
    else:
        return (
            DiscrepancySeverity.WARNING,
            f"Father/Guardian name differs significantly: '{name_a}' vs '{name_b}'.",
            "Verify whether one document references husband and the other references father.",
            "Common cause of delay for married women applicants.",
            15,
        )


class PreflightReport:
    def __init__(
        self,
        checks: List[VerificationCheck],
        score: int,
        status: str,
        summary: str,
        critical_count: int,
        warning_count: int,
        pass_count: int,
    ):
        self.checks = checks
        self.score = score
        self.status = status
        self.summary = summary
        self.critical_count = critical_count
        self.warning_count = warning_count
        self.pass_count = pass_count

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "status": self.status,
            "summary": self.summary,
            "critical_count": self.critical_count,
            "warning_count": self.warning_count,
            "pass_count": self.pass_count,
            "checks": [c.to_dict() for c in self.checks],
        }


def evaluate_readiness(
    doc_a: Dict[str, Any],
    doc_b: Dict[str, Any],
    doc_a_name: str = "Document A (Aadhaar)",
    doc_b_name: str = "Document B (Ration Card)",
) -> PreflightReport:
    """Perform preflight cross-verification between two applicant documents
    and calculate the Application Readiness Score.
    
    Returns structured PreflightReport.
    """
    checks: List[VerificationCheck] = []
    total_deductions = 0

    # 1. Applicant Name Verification
    sev, msg, rem, dbt, ded = compare_names(
        doc_a.get("name", ""),
        doc_b.get("name", "")
    )
    checks.append(VerificationCheck("Applicant Name", doc_a_name, doc_a.get("name", "N/A"), doc_b_name, doc_b.get("name", "N/A"), sev, msg, rem, dbt, ded))
    total_deductions += ded

    # 2. Date of Birth Verification
    sev, msg, rem, dbt, ded = compare_dob(
        doc_a.get("dob", ""),
        doc_b.get("dob", "")
    )
    checks.append(VerificationCheck("Date of Birth", doc_a_name, doc_a.get("dob", "N/A"), doc_b_name, doc_b.get("dob", "N/A"), sev, msg, rem, dbt, ded))
    total_deductions += ded

    # 3. Gender Verification
    if doc_a.get("gender") or doc_b.get("gender"):
        sev, msg, rem, dbt, ded = compare_gender(
            doc_a.get("gender", ""),
            doc_b.get("gender", "")
        )
        checks.append(VerificationCheck("Gender", doc_a_name, doc_a.get("gender", "N/A"), doc_b_name, doc_b.get("gender", "N/A"), sev, msg, rem, dbt, ded))
        total_deductions += ded

    # 4. Father / Spouse Name Verification
    f_a = doc_a.get("father_name") or doc_a.get("guardian_name", "")
    f_b = doc_b.get("father_name") or doc_b.get("guardian_name", "")
    if f_a or f_b:
        sev, msg, rem, dbt, ded = compare_father_or_spouse(f_a, f_b)
        checks.append(VerificationCheck("Father/Spouse Name", doc_a_name, f_a or "N/A", doc_b_name, f_b or "N/A", sev, msg, rem, dbt, ded))
        total_deductions += ded

    # Calculate final score (bounded 0 to 100)
    score = max(0, min(100, 100 - total_deductions))

    crit_count = sum(1 for c in checks if c.severity == DiscrepancySeverity.CRITICAL)
    warn_count = sum(1 for c in checks if c.severity == DiscrepancySeverity.WARNING)
    pass_count = sum(1 for c in checks if c.severity == DiscrepancySeverity.PASS)

    # Determine status categorization
    if score >= 85 and crit_count == 0:
        status = "READY FOR SUBMISSION (उच्च तैयारी)"
        summary = "All mandatory identity parameters align cleanly. Low risk of clerical portal rejection."
    elif score >= 65 and crit_count == 0:
        status = "ACTION REQUIRED BEFORE SUBMISSION (सुधार आवश्यक)"
        summary = "Minor clerical discrepancies detected (e.g. initials or birth date format). Review checklist before final submission."
    else:
        status = "HIGH RISK OF REJECTION (अस्वीकृति का उच्च जोखिम)"
        summary = "Critical mismatches detected across applicant records. Submitting will likely trigger automated DBT rejection."

    return PreflightReport(
        checks=checks,
        score=score,
        status=status,
        summary=summary,
        critical_count=crit_count,
        warning_count=warn_count,
        pass_count=pass_count,
    )
