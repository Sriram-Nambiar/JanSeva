"""JanSeva 2.0 FastAPI Backend Server.

Bridges the React frontend to the JanSeva core engines:
- Gemma 4 Multimodal Harness
- DPDP Act 2023 In-RAM PII Redactor & Verhoeff Validator
- Preflight Verification & Application Readiness Scoring Engine
- openZIM / Kiwix python-libzim Knowledge Retrieval
- 'Kyun Reject Hua?' Rejection Decoder
"""

import base64
import io
import os
import pathlib
from typing import Any, Dict, List, Optional
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from core.gemma_harness import GemmaHarness
from core.privacy import (
    extract_and_mask_id,
    mask_aadhaar_text,
    redact_aadhaar_image,
    sanitize_extracted_payload,
)
from core.rejection_decoder import RejectionDecoder
from core.scheme_finder import SchemeFinder
from core.serve_mode import KioskTelemetry, generate_hotspot_qr, get_local_ip
from core.verifier import DiscrepancySeverity, evaluate_readiness
from core.zim_engine import WelfareZimEngine

app = FastAPI(title="JanSeva API", version="2.0.0")

# Enable CORS for local Vite development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global engine instances
zim_engine = WelfareZimEngine()
scheme_finder = SchemeFinder(zim_engine)
rejection_decoder = RejectionDecoder(zim_engine)
gemma_harness = GemmaHarness()
telemetry = KioskTelemetry()

ROOT_DIR = pathlib.Path(__file__).parent
DEMO_DIR = ROOT_DIR / "demo_assets"


def pil_to_base64_data_uri(img: Image.Image, format="JPEG") -> str:
    """Convert PIL image to base64 data URI."""
    buf = io.BytesIO()
    img.convert("RGB").save(buf, format=format, quality=85)
    b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return f"data:image/{format.lower()};base64,{b64}"


def read_image_from_upload(upload_file: UploadFile) -> Image.Image:
    """Read PIL image from uploaded file buffer."""
    contents = upload_file.file.read()
    return Image.open(io.BytesIO(contents))


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "app": "JanSeva 2.0",
        "zim_mounted": zim_engine.is_zim_active,
        "ollama_online": gemma_harness.is_ollama_online(),
        "local_ip": get_local_ip(),
    }


@app.get("/api/demo-assets")
def get_demo_assets():
    """Return base64 data URIs of pre-generated sample documents for 1-click test."""
    p_aadhaar = DEMO_DIR / "sample_aadhaar.png"
    p_ration = DEMO_DIR / "sample_ration.png"
    p_passbook = DEMO_DIR / "sample_passbook.png"
    p_slip = DEMO_DIR / "sample_rejection_slip.png"

    res = {}
    if p_aadhaar.exists():
        res["aadhaar"] = pil_to_base64_data_uri(Image.open(p_aadhaar), format="PNG")
    if p_ration.exists():
        res["ration"] = pil_to_base64_data_uri(Image.open(p_ration), format="PNG")
    if p_passbook.exists():
        res["passbook"] = pil_to_base64_data_uri(Image.open(p_passbook), format="PNG")
    if p_slip.exists():
        res["rejection_slip"] = pil_to_base64_data_uri(Image.open(p_slip), format="PNG")

    return res


@app.post("/api/preflight")
async def run_preflight(
    doc_a: Optional[UploadFile] = File(None),
    doc_b: Optional[UploadFile] = File(None),
    doc_a_base64: Optional[str] = Form(None),
    doc_b_base64: Optional[str] = Form(None),
    lang: str = Form("en"),
):
    """Run full Preflight Verification:
    1. Reads ingested images.
    2. Performs DPDP Act in-RAM visual redaction on Aadhaar card.
    3. Extracts structured entities via Gemma 4 harness.
    4. Evaluates clerical discrepancies and calculates Readiness Score.
    5. Generates layman plain-language explanation in requested language.
    """
    try:
        # Resolve doc_a
        if doc_a:
            img_a = read_image_from_upload(doc_a)
        elif doc_a_base64:
            clean_b64 = doc_a_base64.split(",")[-1]
            img_a = Image.open(io.BytesIO(base64.b64decode(clean_b64)))
        else:
            p = DEMO_DIR / "sample_aadhaar.png"
            img_a = Image.open(p) if p.exists() else Image.new("RGB", (400, 250), "#fff")

        # Resolve doc_b
        if doc_b:
            img_b = read_image_from_upload(doc_b)
        elif doc_b_base64:
            clean_b64 = doc_b_base64.split(",")[-1]
            img_b = Image.open(io.BytesIO(base64.b64decode(clean_b64)))
        else:
            p = DEMO_DIR / "sample_ration.png"
            img_b = Image.open(p) if p.exists() else Image.new("RGB", (400, 250), "#fff")

        # 1. Apply DPDP Visual Redaction to Document A (Aadhaar)
        redacted_img_a = redact_aadhaar_image(img_a)
        redacted_a_uri = pil_to_base64_data_uri(redacted_img_a, format="PNG")
        doc_b_uri = pil_to_base64_data_uri(img_b, format="PNG")

        # 2. Extract Entities via Gemma 4 Harness
        entities_a = gemma_harness.extract_document_entities(img_a, doc_type_hint="aadhaar")
        entities_b = gemma_harness.extract_document_entities(img_b, doc_type_hint="ration")

        # 3. Deterministic Preflight Cross-Verification
        report = evaluate_readiness(
            entities_a,
            entities_b,
            doc_a_name="Document A (Aadhaar)",
            doc_b_name="Document B (Ration Card)",
        )

        # 4. Layman Explanation
        explanation = gemma_harness.explain_preflight_report(report.to_dict(), language=lang)

        # 5. Record telemetry
        telemetry.record_preflight()

        return {
            "score": report.score,
            "status": report.status,
            "summary": report.summary,
            "critical_count": report.critical_count,
            "warning_count": report.warning_count,
            "pass_count": report.pass_count,
            "checks": [c.to_dict() for c in report.checks],
            "explanation": explanation,
            "entities_a": entities_a,
            "entities_b": entities_b,
            "doc_a_redacted_data_uri": redacted_a_uri,
            "doc_b_data_uri": doc_b_uri,
            "dpdp_redacted": True,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class RejectionRequest(BaseModel):
    query: str


@app.post("/api/decode-rejection")
def decode_rejection(payload: RejectionRequest):
    """Decode administrative error code or SMS notice against openZIM rejection archive."""
    report = rejection_decoder.decode(payload.query)
    telemetry.record_rejection_decoded()
    return report.to_dict()


@app.get("/api/schemes")
def get_schemes(
    q: str = "",
    state: str = "All India",
    category: str = "All",
    is_farmer: bool = True,
):
    """Filter schemes from local .zim archive via python-libzim at 0ms latency."""
    results = scheme_finder.filter_schemes(
        search_query=q,
        state=state if state != "All" else "All India",
        category=category,
        is_landowner=is_farmer,
    )
    telemetry.record_scheme_query()
    return {
        "count": len(results),
        "schemes": results,
        "zim_mounted": zim_engine.is_zim_active,
    }


@app.get("/api/telemetry")
def get_telemetry():
    """Return edge kiosk metrics."""
    data = telemetry.to_dict()
    data["local_ip"] = get_local_ip()
    data["zim_active"] = zim_engine.is_zim_active
    return data


@app.get("/api/hotspot-qr")
def get_hotspot_qr():
    """Generate QR code pointing to this kiosk server."""
    ip = get_local_ip()
    url = f"http://{ip}:3000"
    qr_img = generate_hotspot_qr(url)
    return {
        "url": url,
        "qr_data_uri": pil_to_base64_data_uri(qr_img, format="PNG"),
    }
