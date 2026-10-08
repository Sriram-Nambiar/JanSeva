"""Unit tests for DPDP Act Compliance & Privacy Preservation."""

import pytest
from PIL import Image
from core.privacy import (
    extract_and_mask_id,
    mask_aadhaar_text,
    redact_aadhaar_image,
    sanitize_extracted_payload,
    validate_verhoeff,
)


def test_mask_aadhaar_text():
    # Spaced 12-digit number
    text = "Citizen Aadhaar is 4821 9081 4821 present on record."
    masked = mask_aadhaar_text(text)
    assert "XXXX-XXXX-4821" in masked
    assert "4821 9081" not in masked

    # Hyphenated
    text_hyphen = "Aadhaar: 9821-4821-1234"
    masked_hyphen = mask_aadhaar_text(text_hyphen)
    assert "XXXX-XXXX-1234" in masked_hyphen

    # Unspaced
    text_raw = "Ref: 890123456789"
    masked_raw = mask_aadhaar_text(text_raw)
    assert "XXXX-XXXX-6789" in masked_raw


def test_verhoeff_validation():
    # Aadhaar cannot start with 0 or 1
    assert not validate_verhoeff("012345678901")
    assert not validate_verhoeff("112345678901")

    # Short string
    assert not validate_verhoeff("12345")


def test_extract_and_mask_id():
    masked, is_aadhaar = extract_and_mask_id("982148211234")
    assert is_aadhaar is True
    assert masked == "XXXX-XXXX-1234"

    # Non-Aadhaar ID
    masked_pan, is_pan = extract_and_mask_id("ABCDE1234F")
    assert is_pan is False
    assert masked_pan == "ABCDE1234F"


def test_sanitize_extracted_payload():
    payload = {
        "applicant": "Ramesh Kumar",
        "aadhaar": "4821 9081 4821",
        "nested": {
            "family_aadhaar": "9821 4821 9999",
        },
        "id_list": ["9821 4821 7777", "regular_text"],
    }
    sanitized = sanitize_extracted_payload(payload)
    assert sanitized["aadhaar"] == "XXXX-XXXX-4821"
    assert sanitized["nested"]["family_aadhaar"] == "XXXX-XXXX-9999"
    assert sanitized["id_list"][0] == "XXXX-XXXX-7777"
    assert sanitized["id_list"][1] == "regular_text"


def test_redact_aadhaar_image():
    # Create plain white image
    img = Image.new("RGB", (300, 200), (255, 255, 255))
    redacted = redact_aadhaar_image(img, redaction_box=(50, 50, 150, 100))

    # The region (60, 60) should now be dark (15, 23, 42)
    pixel = redacted.getpixel((60, 60))
    assert pixel == (15, 23, 42)

    # Pixel outside redaction box should still be white
    assert redacted.getpixel((10, 10)) == (255, 255, 255)
