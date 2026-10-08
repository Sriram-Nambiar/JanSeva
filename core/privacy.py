"""DPDP Act 2023 Compliance & Privacy Preservation Module.

Under the Digital Personal Data Protection (DPDP) Act 2023 and UIDAI regulations,
storing or transmitting unmasked 12-digit Aadhaar numbers to commercial third-party
APIs or uncertified storage is prohibited.

This module guarantees:
1. Mathematical verification of Aadhaar numbers using the Verhoeff Algorithm.
2. In-memory masking of the first 8 digits (XXXX-XXXX-1234).
3. Visual image redaction using PIL/OpenCV bounding-box obfuscation.
4. Zero-disk persistence policy (all processing in ephemeral RAM).
"""

import io
import re
from typing import List, Optional, Tuple
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# --- Verhoeff Algorithm Tables for Aadhaar Checksum Validation ---
_MULTIPLICATION_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 2, 3, 4, 0, 6, 7, 8, 9, 5],
    [2, 3, 4, 0, 1, 7, 8, 9, 5, 6],
    [3, 4, 0, 1, 2, 8, 9, 5, 6, 7],
    [4, 0, 1, 2, 3, 9, 5, 6, 7, 8],
    [5, 9, 8, 7, 6, 0, 4, 3, 2, 1],
    [6, 5, 9, 8, 7, 1, 0, 4, 3, 2],
    [7, 6, 5, 9, 8, 2, 1, 0, 4, 3],
    [8, 7, 6, 5, 9, 3, 2, 1, 0, 4],
    [9, 8, 7, 6, 5, 4, 3, 2, 1, 0],
]

_PERMUTATION_TABLE = [
    [0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
    [1, 5, 7, 6, 2, 8, 3, 0, 9, 4],
    [5, 8, 0, 3, 7, 9, 6, 1, 4, 2],
    [8, 9, 1, 6, 0, 4, 3, 5, 2, 7],
    [9, 4, 5, 3, 1, 2, 6, 8, 7, 0],
    [4, 2, 8, 6, 5, 7, 3, 9, 0, 1],
    [2, 7, 9, 3, 8, 0, 6, 4, 1, 5],
    [7, 0, 4, 6, 9, 1, 3, 2, 5, 8],
]

_INVERSE_TABLE = [0, 4, 3, 2, 1, 5, 6, 7, 8, 9]

# Regex matches 12-digit Aadhaar formats: 1234 5678 9012, 1234-5678-9012, or 123456789012
# UIDAI specification: Aadhaar never starts with 0 or 1
AADHAAR_REGEX = re.compile(r"\b([2-9]\d{3})[\s\-]?(\d{4})[\s\-]?(\d{4})\b")


def validate_verhoeff(number_str: str) -> bool:
    """Validate a numeric string against the Verhoeff checksum algorithm.
    
    Aadhaar numbers strictly use the Verhoeff algorithm for the 12th check digit.
    """
    cleaned = "".join(filter(str.isdigit, number_str))
    if len(cleaned) != 12:
        return False
    
    # Aadhaar cannot start with 0 or 1
    if cleaned[0] in ("0", "1"):
        return False
        
    c = 0
    reversed_digits = [int(d) for d in reversed(cleaned)]
    for i, digit in enumerate(reversed_digits):
        c = _MULTIPLICATION_TABLE[c][_PERMUTATION_TABLE[i % 8][digit]]
    return c == 0


def mask_aadhaar_text(text: str) -> str:
    """Mask the first 8 digits of any 12-digit Aadhaar number found in text.
    
    Example:
        '3456 7890 1234' -> 'XXXX-XXXX-1234'
        'Aadhaar: 987654321098' -> 'Aadhaar: XXXX-XXXX-1098'
    """
    def _replacer(match: re.Match) -> str:
        last4 = match.group(3)
        return f"XXXX-XXXX-{last4}"

    return AADHAAR_REGEX.sub(_replacer, text)


def extract_and_mask_id(id_string: str) -> Tuple[str, bool]:
    """Inspect an ID string, detect if it is an Aadhaar card, and return masked representation.
    
    Returns:
        (masked_string, is_aadhaar_detected)
    """
    if not id_string:
        return "", False
        
    cleaned = "".join(filter(str.isdigit, id_string))
    if len(cleaned) == 12:
        last4 = cleaned[-4:]
        masked = f"XXXX-XXXX-{last4}"
        return masked, True
        
    # Check if already masked
    if "XXXX" in id_string:
        return id_string, True
        
    return id_string, False


def redact_aadhaar_image(
    image: Image.Image,
    redaction_box: Optional[Tuple[int, int, int, int]] = None
) -> Image.Image:
    """Apply a visual redaction bar over the Aadhaar number region for DPDP compliance.
    
    If redaction_box (left, top, right, bottom) is omitted, heuristic card geometry
    targeting the bottom-center 12-digit number zone is applied.
    
    Returns:
        A copy of the image with the sensitive region permanently obfuscated.
    """
    redacted = image.copy().convert("RGB")
    draw = ImageDraw.Draw(redacted)
    width, height = redacted.size

    if redaction_box:
        x1, y1, x2, y2 = redaction_box
    else:
        # Standard UIDAI physical card geometry:
        # Aadhaar number is printed in the lower 75%-88% vertical band, centered horizontally.
        # We redact the left 66% of that number zone (the first 8 digits), leaving only the last 4.
        x1 = int(width * 0.18)
        y1 = int(height * 0.76)
        x2 = int(width * 0.68)
        y2 = int(height * 0.86)

    # Draw solid dark security bar
    draw.rectangle([x1, y1, x2, y2], fill=(15, 23, 42))

    # Add security badge text
    label = "🔒 DPDP ACT 2023 MASKED"
    try:
        # Attempt simple default font
        font = ImageFont.load_default()
    except Exception:
        font = None

    text_pos = (x1 + 8, y1 + int((y2 - y1) * 0.3))
    draw.text(text_pos, label, fill=(56, 189, 248), font=font)

    return redacted


def sanitize_extracted_payload(payload: dict) -> dict:
    """Recursively scrub any unmasked Aadhaar occurrences from JSON payloads before display."""
    sanitized = {}
    for key, value in payload.items():
        if isinstance(value, str):
            sanitized[key] = mask_aadhaar_text(value)
        elif isinstance(value, dict):
            sanitized[key] = sanitize_extracted_payload(value)
        elif isinstance(value, list):
            sanitized[key] = [
                sanitize_extracted_payload(item) if isinstance(item, dict)
                else mask_aadhaar_text(item) if isinstance(item, str)
                else item
                for item in value
            ]
        else:
            sanitized[key] = value
    return sanitized
