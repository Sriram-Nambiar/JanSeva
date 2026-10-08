"""Unit tests for 'Kyun Reject Hua?' Rejection Notice Decoder."""

import pytest
from core.rejection_decoder import RejectionDecoder


def test_decode_pfms_04():
    decoder = RejectionDecoder()
    report = decoder.decode("PFMS Code 04: Account not mapped to NPCI")
    assert report.code == "PFMS_04"
    assert "NPCI" in report.title
    assert len(report.action_plan) >= 3
    assert any("Annexure-1" in step for step in report.action_plan)
    assert any("Aadhaar Card" in doc for doc in report.documents_required)


def test_decode_dbt_102():
    decoder = RejectionDecoder()
    report = decoder.decode("DBT 102")
    assert report.code == "DBT_102"
    assert "dormant" in report.root_cause.lower() or "inactive" in report.root_cause.lower()


def test_decode_unknown_error():
    decoder = RejectionDecoder()
    report = decoder.decode("RANDOM_UNRECOGNIZED_CODE_999")
    assert report.code == "UNKNOWN_ERROR"
    assert "CSC" in report.action_plan[0] or "Gram Panchayat" in report.action_plan[0]
