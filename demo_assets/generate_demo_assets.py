"""Synthetic Demo Asset Generator for JanSeva.

Generates realistic mock citizen identity documents and administrative rejection slips
for instant 1-click test runs during hackathon judging and kiosk demonstration.
All data is 100% fictional and contains zero real citizen PII.
"""

import pathlib
from PIL import Image, ImageDraw, ImageFont


def _draw_text_box(draw, text, xy, fill="#1e293b", font=None):
    draw.text(xy, text, fill=fill, font=font)


def create_mock_aadhaar(path: pathlib.Path) -> None:
    """Generate mock Aadhaar card with 12-digit number for DPDP masking test."""
    w, h = 600, 380
    img = Image.new("RGB", (w, h), "#f8fafc")
    draw = ImageDraw.Draw(img)

    # Tricolor decorative top stripe
    draw.rectangle([0, 0, w, 12], fill="#ea580c")
    draw.rectangle([0, 12, w, 24], fill="#ffffff")
    draw.rectangle([0, 24, w, 36], fill="#16a34a")

    # Header
    draw.rectangle([0, 36, w, 76], fill="#f1f5f9")
    _draw_text_box(draw, "GOVERNMENT OF INDIA / भारत सरकार", (160, 48), fill="#0f172a")

    # Photo Box
    draw.rectangle([35, 100, 165, 250], fill="#e2e8f0", outline="#94a3b8", width=2)
    draw.rectangle([65, 130, 135, 200], fill="#cbd5e1")  # Head
    draw.ellipse([75, 140, 125, 190], fill="#94a3b8")
    draw.arc([55, 200, 145, 260], start=0, end=180, fill="#64748b", width=30)
    _draw_text_box(draw, "[ PHOTO ]", (72, 220), fill="#64748b")

    # Details
    _draw_text_box(draw, "Name / नाम:  Ramesh Kumar", (190, 110), fill="#0f172a")
    _draw_text_box(draw, "DOB / जन्म तिथि:  15/08/1982", (190, 140), fill="#0f172a")
    _draw_text_box(draw, "Gender / लिंग:  Male / पुरुष", (190, 170), fill="#0f172a")
    _draw_text_box(draw, "S/O:  Narayana Swamy", (190, 200), fill="#0f172a")
    _draw_text_box(draw, "Address: No. 42, 3rd Cross, Ramanagara, KA", (190, 230), fill="#475569")

    # Aadhaar Number Band
    draw.rectangle([30, 280, 570, 345], fill="#ffffff", outline="#cbd5e1", width=1)
    _draw_text_box(draw, "4821  9081  4821", (180, 296), fill="#b91c1c")
    _draw_text_box(draw, "मेरा आधार, मेरी पहचान", (230, 324), fill="#64748b")

    img.save(path)
    print(f"Generated {path}")


def create_mock_ration(path: pathlib.Path) -> None:
    """Generate mock Ration Card with clerical mismatch ('Ramesh K' vs 'Ramesh Kumar')."""
    w, h = 600, 380
    img = Image.new("RGB", (w, h), "#fefce8")
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, w, 60], fill="#ca8a04")
    _draw_text_box(draw, "FOOD & CIVIL SUPPLIES DEPT - BPL RATION CARD", (80, 20), fill="#ffffff")

    # Details Box
    draw.rectangle([30, 80, 570, 350], fill="#ffffff", outline="#fde047", width=2)
    _draw_text_box(draw, "Ration Card No:  RC-KA-094821049", (50, 100), fill="#854d0e")
    _draw_text_box(draw, "Card Type:  Priority Household (BPL / PHH)", (50, 130), fill="#0f172a")
    # Deliberate clerical mismatch: Ramesh K instead of Ramesh Kumar
    _draw_text_box(draw, "Head of Household:  Ramesh K", (50, 165), fill="#b91c1c")
    _draw_text_box(draw, "Date of Birth:  15/08/1982", (50, 195), fill="#0f172a")
    _draw_text_box(draw, "Father's Name:  Narayana Swamy", (50, 225), fill="#0f172a")
    _draw_text_box(draw, "Fair Price Shop No:  FPS-491 (Ramanagara Rural)", (50, 255), fill="#475569")
    _draw_text_box(draw, "Total Family Members:  4 (e-KYC Verified)", (50, 285), fill="#16a34a")

    img.save(path)
    print(f"Generated {path}")


def create_mock_passbook(path: pathlib.Path) -> None:
    """Generate mock Bank Passbook."""
    w, h = 600, 380
    img = Image.new("RGB", (w, h), "#eff6ff")
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, w, 65], fill="#1e40af")
    _draw_text_box(draw, "STATE BANK OF INDIA - SAVINGS ACCOUNT PASSBOOK", (70, 22), fill="#ffffff")

    # Content Box
    draw.rectangle([30, 85, 570, 350], fill="#ffffff", outline="#bfdbfe", width=2)
    _draw_text_box(draw, "Account Name:  Ramesh Kumar", (50, 105), fill="#1e3a8a")
    _draw_text_box(draw, "Account No:  30948201948", (50, 140), fill="#0f172a")
    _draw_text_box(draw, "CIF No:  8920194820", (50, 175), fill="#475569")
    _draw_text_box(draw, "IFSC Code:  SBIN0040182", (50, 210), fill="#0f172a")
    _draw_text_box(draw, "Branch:  Ramanagara Main Branch", (50, 245), fill="#475569")
    _draw_text_box(draw, "Aadhaar Seeding Status:  PENDING (NPCI Mapper Unlinked)", (50, 280), fill="#dc2626")

    img.save(path)
    print(f"Generated {path}")


def create_mock_rejection_slip(path: pathlib.Path) -> None:
    """Generate mock administrative rejection slip."""
    w, h = 600, 380
    img = Image.new("RGB", (w, h), "#fff1f2")
    draw = ImageDraw.Draw(img)

    # Header
    draw.rectangle([0, 0, w, 65], fill="#991b1b")
    _draw_text_box(draw, "PUBLIC FINANCIAL MANAGEMENT SYSTEM (PFMS)", (110, 15), fill="#ffffff")
    _draw_text_box(draw, "Direct Benefit Transfer (DBT) Objection Notice", (140, 38), fill="#fecaca")

    # Box
    draw.rectangle([30, 85, 570, 350], fill="#ffffff", outline="#fecdd3", width=2)
    _draw_text_box(draw, "Application ID:  PMK-2024-8910482", (50, 105), fill="#0f172a")
    _draw_text_box(draw, "Scheme:  PM-KISAN Samman Nidhi", (50, 135), fill="#0f172a")
    _draw_text_box(draw, "Transaction Status:  REJECTED BY BANK / PFMS", (50, 165), fill="#b91c1c")
    _draw_text_box(draw, "Rejection Error Code:  PFMS Code 04", (50, 205), fill="#b91c1c")
    _draw_text_box(draw, "Reason:  Account not mapped to NPCI / Aadhaar Seeding Pending", (50, 235), fill="#991b1b")
    _draw_text_box(draw, "Issuing Bank:  State Bank of India (SBIN0040182)", (50, 265), fill="#475569")
    _draw_text_box(draw, "Remedy: Visit bank branch with Annexure-1 Mandate Form", (50, 295), fill="#0369a1")

    img.save(path)
    print(f"Generated {path}")


if __name__ == "__main__":
    assets_dir = pathlib.Path(__file__).parent
    create_mock_aadhaar(assets_dir / "sample_aadhaar.png")
    create_mock_ration(assets_dir / "sample_ration.png")
    create_mock_passbook(assets_dir / "sample_passbook.png")
    create_mock_rejection_slip(assets_dir / "sample_rejection_slip.png")
    print("All mock assets created successfully!")
