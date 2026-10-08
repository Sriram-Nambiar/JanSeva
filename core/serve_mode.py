"""JanSeva Serve Mode (The Kiwix Hotspot).

Module 4 of JanSeva:
Enables kiosk operators (Gram Panchayat / CSC / Fair Price Shops) to serve JanSeva
over a local Wi-Fi hotspot (`janseva.local` or local network IP).

Waiting citizens connect their mobile phones to the local Wi-Fi, scan the on-screen
pairing QR code, and use the copilot in their mobile browsers with 0KB mobile data.

Tracks kiosk telemetry:
- Preflight verifications performed
- DPDP Aadhaar redactions enforced
- Cloud bandwidth saved
- Clerical backlog days avoided
"""

import io
import socket
from typing import Any, Dict, Optional, Tuple
from PIL import Image
import qrcode


def get_local_ip() -> str:
    """Detect the machine's primary local network IP address."""
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        # Does not actually connect; determines outgoing interface IP
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"
    finally:
        s.close()
    return ip


def generate_hotspot_qr(url: str, box_size: int = 8, border: int = 2) -> Image.Image:
    """Generate a clean QR code image pointing to the local kiosk server."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(url)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0f172a", back_color="#ffffff")
    return img.get_image() if hasattr(img, "get_image") else img


class KioskTelemetry:
    """In-memory telemetry tracking for edge kiosk operations."""

    def __init__(self):
        self.total_preflights = 0
        self.masked_cards = 0
        self.rejections_decoded = 0
        self.schemes_queried = 0

    def record_preflight(self, masked_count: int = 2) -> None:
        self.total_preflights += 1
        self.masked_cards += masked_count

    def record_rejection_decoded(self) -> None:
        self.rejections_decoded += 1

    def record_scheme_query(self) -> None:
        self.schemes_queried += 1

    @property
    def bandwidth_saved_mb(self) -> float:
        """Estimate cellular bandwidth saved.
        
        Standard cloud AI upload: 5.0 MB per camera photo x 2 cards = 10 MB.
        JanSeva on-device edge execution: 0 MB cloud upload!
        """
        return self.total_preflights * 10.0 + self.rejections_decoded * 5.0

    @property
    def estimated_backlog_days_saved(self) -> int:
        """Estimate administrative delays prevented.
        
        Average government DBT clerical discrepancy turnaround: 14 to 21 days.
        """
        return self.total_preflights * 14

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_preflights": self.total_preflights,
            "masked_cards": self.masked_cards,
            "rejections_decoded": self.rejections_decoded,
            "schemes_queried": self.schemes_queried,
            "bandwidth_saved_mb": round(self.bandwidth_saved_mb, 1),
            "estimated_backlog_days_saved": self.estimated_backlog_days_saved,
        }
