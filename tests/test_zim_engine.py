"""Unit tests for openZIM / Kiwix engine integration."""

import pytest
from core.zim_engine import WelfareZimEngine


def test_zim_engine_initialization():
    engine = WelfareZimEngine()
    # Confirm that native ZIM archives were compiled and mounted
    assert engine.is_zim_active is True


def test_search_schemes():
    engine = WelfareZimEngine()
    results = engine.search_schemes(query="kisan")
    assert len(results) >= 1
    assert results[0]["id"] == "pm_kisan"


def test_search_schemes_by_state():
    engine = WelfareZimEngine()
    karnataka_schemes = engine.search_schemes(state="Karnataka")
    assert any(s["id"] == "gruha_lakshmi" for s in karnataka_schemes)


def test_read_zim_entry_html():
    engine = WelfareZimEngine()
    html = engine.read_zim_entry_html("schemes", "pm_kisan.html")
    assert html is not None
    assert "PM-KISAN" in html
    assert "Section 7 of the Aadhaar Act" in html


def test_search_rejection():
    engine = WelfareZimEngine()
    entry = engine.search_rejection("PFMS Code 04")
    assert entry is not None
    assert entry["code"] == "PFMS_04"
    assert "NPCI" in entry["title"]
