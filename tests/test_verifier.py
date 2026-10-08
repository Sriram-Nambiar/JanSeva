"""Unit tests for Preflight Verification & Application Readiness Scoring Engine."""

import pytest
from core.verifier import (
    DiscrepancySeverity,
    compare_dob,
    compare_names,
    evaluate_readiness,
    normalize_name,
)


def test_normalize_name():
    tokens = normalize_name("Shri Ramesh Kumar S.")
    assert "shri" not in tokens
    assert "ramesh" in tokens
    assert "kumar" in tokens
    assert "s" in tokens


def test_compare_names_identical():
    sev, msg, rem, dbt, ded = compare_names("Ramesh Kumar", "Ramesh Kumar")
    assert sev == DiscrepancySeverity.PASS
    assert ded == 0


def test_compare_names_initials_expansion():
    # Common South Indian scenario: "Ramesh K" vs "Ramesh Kumar"
    sev, msg, rem, dbt, ded = compare_names("Ramesh K", "Ramesh Kumar")
    assert sev == DiscrepancySeverity.WARNING
    assert "Initials discrepancy" in msg
    assert ded == 15


def test_compare_names_inverted_order():
    sev, msg, rem, dbt, ded = compare_names("Kumar Ramesh", "Ramesh Kumar")
    assert sev == DiscrepancySeverity.INFO
    assert ded == 5


def test_compare_names_critical_mismatch():
    sev, msg, rem, dbt, ded = compare_names("Suresh Patil", "Ramesh Kumar")
    assert sev == DiscrepancySeverity.CRITICAL
    assert ded >= 35


def test_compare_dob_exact():
    sev, msg, rem, dbt, ded = compare_dob("15/08/1982", "15-08-1982")
    assert sev == DiscrepancySeverity.PASS
    assert ded == 0


def test_compare_dob_year_only():
    sev, msg, rem, dbt, ded = compare_dob("15/08/1982", "YOB: 1982")
    assert sev == DiscrepancySeverity.WARNING
    assert "Partial DOB match" in msg
    assert ded <= 10


def test_compare_dob_critical_year_diff():
    sev, msg, rem, dbt, ded = compare_dob("15/08/1982", "15/08/1987")
    assert sev == DiscrepancySeverity.CRITICAL
    assert ded >= 30


def test_evaluate_readiness_clean_case():
    doc_a = {
        "name": "Ramesh Kumar",
        "dob": "15/08/1982",
        "gender": "Male",
        "father_name": "Narayana Swamy",
    }
    doc_b = {
        "name": "Ramesh Kumar",
        "dob": "15/08/1982",
        "gender": "Male",
        "father_name": "Narayana Swamy",
    }
    report = evaluate_readiness(doc_a, doc_b)
    assert report.score == 100
    assert "READY FOR SUBMISSION" in report.status
    assert report.critical_count == 0


def test_evaluate_readiness_warning_case():
    # Ration Card has 'Ramesh K' instead of 'Ramesh Kumar'
    doc_a = {
        "name": "Ramesh Kumar",
        "dob": "15/08/1982",
        "gender": "Male",
        "father_name": "Narayana Swamy",
    }
    doc_b = {
        "name": "Ramesh K",
        "dob": "15/08/1982",
        "gender": "Male",
        "father_name": "Narayana Swamy",
    }
    report = evaluate_readiness(doc_a, doc_b)
    assert report.score == 85  # 100 - 15 deduction for initial
    assert report.warning_count >= 1
    assert report.critical_count == 0
