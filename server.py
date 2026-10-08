"""
JanSeva 2.0 FastAPI Backend Server.

Bridges the React frontend to the JanSeva core engines:

- Gemma 4 Multimodal Harness
- DPDP Act 2023 In-RAM PII Redactor & Verhoeff Validator
- Preflight Verification & Application Readiness Scoring Engine
- openZIM / Kiwix python-libzim Knowledge Retrieval
- "Kyun Reject Hua?" Rejection Decoder

Core principle:
Rules decide. AI explains. Humans verify.
"""

import base64
import binascii
import io
import pathlib
from typing import Any, Dict, Optional

from dotenv import load_dotenv
from fastapi import FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image, UnidentifiedImageError
from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Environment
# ---------------------------------------------------------------------------

load_dotenv()


# ---------------------------------------------------------------------------
# JanSeva core imports
# ---------------------------------------------------------------------------

from core.gemma_harness import (
    GemmaHarness,
    LMStudioAPIError,
    LMStudioConnectionError,
    LMStudioError,
    ModelNotConfiguredError,
    is_mock_mode,
)

from core.rejection_decoder import RejectionDecoder
from core.serve_mode import (
    KioskTelemetry,
    generate_hotspot_qr,
    get_local_ip,
)
from core.scheme_finder import SchemeFinder
from core.verifier import evaluate_readiness
from core.zim_engine import WelfareZimEngine
from core.privacy import redact_aadhaar_image


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

app = FastAPI(
    title="JanSeva API",
    version="2.0.0",
    description="Offline-first welfare application verification backend.",
)


# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
#
# Do NOT use "*" together with allow_credentials=True.
# React development server normally runs on port 3000.
#

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global engine instances
# ---------------------------------------------------------------------------

zim_engine = WelfareZimEngine()
scheme_finder = SchemeFinder(zim_engine)
rejection_decoder = RejectionDecoder(zim_engine)
gemma_harness = GemmaHarness()
telemetry = KioskTelemetry()


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = pathlib.Path(__file__).resolve().parent
DEMO_DIR = ROOT_DIR / "demo_assets"


# ---------------------------------------------------------------------------
# Pydantic request models
# ---------------------------------------------------------------------------

class ChatRequest(BaseModel):
    """Request body for AI chat."""

    prompt: str = Field(
        ...,
        min_length=1,
        description="Prompt string to analyze or send to Gemma AI.",
    )


class RejectionRequest(BaseModel):
    """Request body for rejection decoding."""

    query: str = Field(
        ...,
        min_length=1,
        description="Government rejection code, SMS, or rejection message.",
    )


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def pil_to_base64_data_uri(
    img: Image.Image,
    image_format: str = "JPEG",
) -> str:
    """
    Convert a PIL image to a base64 data URI.

    PNG is useful for redacted/demo documents.
    JPEG is used by default for compact responses.
    """

    if not isinstance(img, Image.Image):
        raise ValueError("Expected a PIL Image.")

    image_format = image_format.upper()

    if image_format not in {"JPEG", "PNG", "WEBP"}:
        raise ValueError(
            f"Unsupported image format: {image_format}"
        )

    buffer = io.BytesIO()

    converted = img.convert("RGB")

    save_kwargs = {}

    if image_format == "JPEG":
        save_kwargs["quality"] = 85
        mime_type = "image/jpeg"
    elif image_format == "PNG":
        mime_type = "image/png"
    else:
        save_kwargs["quality"] = 85
        mime_type = "image/webp"

    converted.save(
        buffer,
        format=image_format,
        **save_kwargs,
    )

    encoded = base64.b64encode(buffer.getvalue()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded}"


def read_image_from_upload(upload_file: UploadFile) -> Image.Image:
    """
    Read and validate an uploaded image.

    The image is processed in memory and is not persisted to disk.
    """

    try:
        contents = upload_file.file.read()

        if not contents:
            raise ValueError("Uploaded image is empty.")

        image = Image.open(io.BytesIO(contents))

        # Force PIL to actually decode the image while it is in memory.
        image.load()

        return image.convert("RGB")

    except UnidentifiedImageError as exc:
        raise ValueError("Uploaded file is not a valid image.") from exc

    except OSError as exc:
        raise ValueError("Unable to read the uploaded image.") from exc


def image_from_base64(data: str) -> Image.Image:
    """
    Decode an image from a base64 string or data URI.

    Example:
        data:image/png;base64,iVBOR...
    """

    if not data or not data.strip():
        raise ValueError("Base64 image data is empty.")

    try:
        clean_data = data.strip()

        # Support both:
        # data:image/png;base64,...
        # and raw base64 strings.
        if "," in clean_data:
            clean_data = clean_data.split(",", 1)[1]

        # Remove accidental whitespace/newlines.
        clean_data = "".join(clean_data.split())

        raw_bytes = base64.b64decode(
            clean_data,
            validate=True,
        )

        if not raw_bytes:
            raise ValueError("Decoded image is empty.")

        image = Image.open(io.BytesIO(raw_bytes))
        image.load()

        return image.convert("RGB")

    except (binascii.Error, ValueError, UnidentifiedImageError, OSError) as exc:
        raise ValueError("Invalid base64 image data.") from exc


def load_demo_image(filename: str) -> Image.Image:
    """
    Load a demo image from demo_assets.

    Raises FileNotFoundError if the demo asset does not exist.
    """

    path = DEMO_DIR / filename

    if not path.exists():
        raise FileNotFoundError(
            f"Demo asset not found: {filename}"
        )

    if not path.is_file():
        raise FileNotFoundError(
            f"Demo asset is not a file: {filename}"
        )

    try:
        with Image.open(path) as image:
            image.load()
            return image.convert("RGB")

    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError(
            f"Demo asset is not a valid image: {filename}"
        ) from exc


def normalize_language(language: str) -> str:
    """Normalize supported UI language codes."""

    language = (language or "en").strip().lower()

    allowed_languages = {"en", "hi", "kn"}

    if language not in allowed_languages:
        return "en"

    return language


# ---------------------------------------------------------------------------
# Root endpoint
# ---------------------------------------------------------------------------

@app.get("/")
def read_root() -> Dict[str, str]:
    """Basic API information."""

    return {
        "application": "JanSeva",
        "version": "2.0",
        "status": "running",
    }


# ---------------------------------------------------------------------------
# Health endpoint
# ---------------------------------------------------------------------------

@app.get("/health")
@app.get("/api/health")
def health_check() -> Dict[str, Any]:
    """
    Return backend/provider health information.

    Provider checks are intentionally non-fatal.
    JanSeva backend can still run in mock/offline mode.
    """

    try:
        lm_studio_online = gemma_harness.is_lm_studio_online()
    except Exception:
        lm_studio_online = False

    try:
        ollama_online = gemma_harness.is_ollama_online()
    except Exception:
        ollama_online = False

    try:
        zim_active = bool(zim_engine.is_zim_active)
    except Exception:
        zim_active = False

    try:
        local_ip = get_local_ip()
    except Exception:
        local_ip = "127.0.0.1"

    return {
        "status": "online",
        "application": "JanSeva",
        "version": "2.0",
        "mock_ai": is_mock_mode(),
        "lm_studio_online": lm_studio_online,
        "ollama_online": ollama_online,
        "zim_mounted": zim_active,
        "local_ip": local_ip,
    }


# ---------------------------------------------------------------------------
# LM Studio models
# ---------------------------------------------------------------------------

@app.get("/api/models")
def get_models() -> Dict[str, Any]:
    """Return available models from LM Studio."""

    try:
        models = gemma_harness.get_available_models()

        return {
            "models": models,
            "count": len(models),
        }

    except LMStudioConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except LMStudioError as exc:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(exc),
        ) from exc

    except Exception:
        # Do not expose internal implementation details.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to fetch available models.",
        )


# ---------------------------------------------------------------------------
# Chat
# ---------------------------------------------------------------------------

@app.post("/api/chat")
def chat(payload: ChatRequest) -> Dict[str, str]:
    """
    Chat endpoint supporting:

    - Mock mode
    - LM Studio local Gemma
    """

    prompt = payload.prompt.strip()

    if not prompt:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Prompt must not be empty.",
        )

    # Safe offline development mode.
    if is_mock_mode():
        return {
            "response": (
                "Mock JanSeva AI response: "
                "document requires human verification."
            ),
            "provider": "mock",
        }

    try:
        response_text = gemma_harness.send_chat_request(prompt)

        return {
            "response": response_text,
            "provider": "lm-studio",
        }

    except ModelNotConfiguredError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except LMStudioConnectionError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    except LMStudioAPIError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        ) from exc

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="AI provider request failed.",
        )


# ---------------------------------------------------------------------------
# Demo assets
# ---------------------------------------------------------------------------

@app.get("/api/demo-assets")
def get_demo_assets() -> Dict[str, str]:
    """
    Return base64 data URIs of pre-generated sample documents.

    Missing demo assets are simply omitted from the response.
    """

    demo_files = {
        "aadhaar": "sample_aadhaar.png",
        "ration": "sample_ration.png",
        "passbook": "sample_passbook.png",
        "rejection_slip": "sample_rejection_slip.png",
    }

    result: Dict[str, str] = {}

    for key, filename in demo_files.items():
        path = DEMO_DIR / filename

        if not path.exists() or not path.is_file():
            continue

        try:
            with Image.open(path) as image:
                image.load()
                result[key] = pil_to_base64_data_uri(
                    image,
                    image_format="PNG",
                )
        except (UnidentifiedImageError, OSError):
            # Ignore invalid/missing optional demo asset.
            continue

    return result


# ---------------------------------------------------------------------------
# Preflight verification
# ---------------------------------------------------------------------------

@app.post("/api/preflight")
async def run_preflight(
    doc_a: Optional[UploadFile] = File(None),
    doc_b: Optional[UploadFile] = File(None),
    doc_a_base64: Optional[str] = Form(None),
    doc_b_base64: Optional[str] = Form(None),
    lang: str = Form("en"),
) -> Dict[str, Any]:
    """
    Run full JanSeva Preflight Verification.

    Inputs:
    - Document A upload/base64
    - Document B upload/base64
    - Language

    Processing:
    1. Load images in memory.
    2. Redact Aadhaar image.
    3. Extract document entities.
    4. Run deterministic readiness verifier.
    5. Generate explanation.
    6. Return readiness report.
    """

    try:
        # ---------------------------------------------------------------
        # Document A
        # ---------------------------------------------------------------

        if doc_a is not None:
            img_a = read_image_from_upload(doc_a)

        elif doc_a_base64:
            img_a = image_from_base64(doc_a_base64)

        else:
            try:
                img_a = load_demo_image("sample_aadhaar.png")
            except FileNotFoundError:
                img_a = Image.new(
                    "RGB",
                    (400, 250),
                    "white",
                )

        # ---------------------------------------------------------------
        # Document B
        # ---------------------------------------------------------------

        if doc_b is not None:
            img_b = read_image_from_upload(doc_b)

        elif doc_b_base64:
            img_b = image_from_base64(doc_b_base64)

        else:
            try:
                img_b = load_demo_image("sample_ration.png")
            except FileNotFoundError:
                img_b = Image.new(
                    "RGB",
                    (400, 250),
                    "white",
                )

        # ---------------------------------------------------------------
        # Privacy processing
        # ---------------------------------------------------------------

        redacted_img_a = redact_aadhaar_image(img_a)

        redacted_a_uri = pil_to_base64_data_uri(
            redacted_img_a,
            image_format="PNG",
        )

        doc_b_uri = pil_to_base64_data_uri(
            img_b,
            image_format="PNG",
        )

        # ---------------------------------------------------------------
        # Entity extraction
        # ---------------------------------------------------------------

        entities_a = gemma_harness.extract_document_entities(
            img_a,
            doc_type_hint="aadhaar",
        )

        entities_b = gemma_harness.extract_document_entities(
            img_b,
            doc_type_hint="ration",
        )

        # ---------------------------------------------------------------
        # Deterministic readiness evaluation
        # ---------------------------------------------------------------

        report = evaluate_readiness(
            entities_a,
            entities_b,
            doc_a_name="Document A (Aadhaar)",
            doc_b_name="Document B (Ration Card)",
        )

        # ---------------------------------------------------------------
        # Human-readable explanation
        # ---------------------------------------------------------------

        language = normalize_language(lang)

        explanation = gemma_harness.explain_preflight_report(
            report.to_dict(),
            language=language,
        )

        # ---------------------------------------------------------------
        # Telemetry
        # ---------------------------------------------------------------

        telemetry.record_preflight()

        # ---------------------------------------------------------------
        # Response
        # ---------------------------------------------------------------

        return {
            "score": report.score,
            "status": report.status,
            "summary": report.summary,
            "critical_count": report.critical_count,
            "warning_count": report.warning_count,
            "pass_count": report.pass_count,
            "checks": [
                check.to_dict()
                for check in report.checks
            ],
            "explanation": explanation,
            "entities_a": entities_a,
            "entities_b": entities_b,
            "doc_a_redacted_data_uri": redacted_a_uri,
            "doc_b_data_uri": doc_b_uri,
            "dpdp_redacted": True,
        }

    except HTTPException:
        raise

    except (ValueError, FileNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc

    except Exception:
        # Do not return raw exceptions because they may contain
        # implementation details or sensitive information.
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Preflight processing failed.",
        )


# ---------------------------------------------------------------------------
# Rejection decoder
# ---------------------------------------------------------------------------

@app.post("/api/decode-rejection")
def decode_rejection(
    payload: RejectionRequest,
) -> Dict[str, Any]:
    """
    Decode an administrative error code or rejection message
    using the local openZIM rejection archive.
    """

    query = payload.query.strip()

    if not query:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Rejection query must not be empty.",
        )

    try:
        report = rejection_decoder.decode(query)

        telemetry.record_rejection_decoded()

        return report.to_dict()

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to decode the rejection notice.",
        )


# ---------------------------------------------------------------------------
# Welfare schemes
# ---------------------------------------------------------------------------

@app.get("/api/schemes")
def get_schemes(
    q: str = "",
    state: str = "All India",
    category: str = "All",
    is_farmer: bool = True,
) -> Dict[str, Any]:
    """
    Search/filter welfare schemes from the local ZIM archive.
    """

    try:
        search_query = q.strip()

        normalized_state = (
            "All India"
            if state.strip().lower() == "all"
            else state.strip()
        )

        normalized_category = category.strip() or "All"

        results = scheme_finder.filter_schemes(
            search_query=search_query,
            state=normalized_state,
            category=normalized_category,
            is_landowner=is_farmer,
        )

        telemetry.record_scheme_query()

        return {
            "count": len(results),
            "schemes": results,
            "zim_mounted": bool(zim_engine.is_zim_active),
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to search welfare schemes.",
        )


# ---------------------------------------------------------------------------
# Telemetry
# ---------------------------------------------------------------------------

@app.get("/api/telemetry")
def get_telemetry() -> Dict[str, Any]:
    """Return non-PII kiosk metrics."""

    try:
        data = telemetry.to_dict()

        try:
            data["local_ip"] = get_local_ip()
        except Exception:
            data["local_ip"] = "127.0.0.1"

        try:
            data["zim_active"] = bool(
                zim_engine.is_zim_active
            )
        except Exception:
            data["zim_active"] = False

        return data

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to retrieve telemetry.",
        )


# ---------------------------------------------------------------------------
# Serve Mode / Hotspot QR
# ---------------------------------------------------------------------------

@app.get("/api/hotspot-qr")
def get_hotspot_qr() -> Dict[str, str]:
    """
    Generate a QR code pointing to the local JanSeva kiosk UI.
    """

    try:
        ip = get_local_ip()

        if not ip:
            ip = "127.0.0.1"

        url = f"http://{ip}:3000"

        qr_img = generate_hotspot_qr(url)

        return {
            "url": url,
            "qr_data_uri": pil_to_base64_data_uri(
                qr_img,
                image_format="PNG",
            ),
        }

    except Exception:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate hotspot QR code.",
        )