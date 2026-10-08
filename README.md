# 🏛️ JanSeva — Privacy-Preserving Welfare Application Preflight Copilot

> **The client-side linter for government welfare: Verify locally, protect privacy, submit cleanly.**  
> *Built on top of the **openZIM / Kiwix** ecosystem and powered by **Gemma 4 Multimodal**.*

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](https://opensource.org/licenses/MIT)
[![Kiwix / openZIM](https://img.shields.io/badge/Kiwix%20openZIM-Compatible-0284c7.svg)](https://openzim.org/)
[![Gemma 4 Multimodal](https://img.shields.io/badge/Gemma%204-Multimodal-10b981.svg)](https://ai.google.dev/gemma)
[![DPDP Act 2023](https://img.shields.io/badge/DPDP%20Act%202023-In--RAM%20Masking-green.svg)](https://www.meity.gov.in/)

---

## 📌 Executive Summary
JanSeva is an open-source, edge-AI preflight application designed for citizen welfare kiosks (Common Service Centers / Gram Panchayats / Nada Kacheri). Rather than relying on fragile cloud OCR or uploading sensitive citizen documents to third-party commercial AI APIs, JanSeva runs **100% on-device**.

It cross-verifies physical identification documents, computes an **Application Readiness Score**, masks sensitive Aadhaar PII locally under India's Digital Personal Data Protection (DPDP) Act 2023, and decodes cryptic administrative rejection slips against offline **openZIM (`.zim`)** knowledge packs with zero cloud latency.

---

## 🎯 Hackathon Challenges Addressed

### 1. Best Use of Gemma 4
- **Multimodal Document Inspection:** Uses Gemma 4 vision to ingest noisy camera crops of laminated physical IDs (Aadhaar, Ration Card, Bank Passbook) and printed administrative rejection notices.
- **Empathetic Layman Translations:** Translates bureaucratic mismatch codes into plain English, Hindi, and Kannada.
- **Hybrid Deployment:** Runs seamlessly across Google GenAI Cloud API, local Ollama edge weights (`localhost:11434`), and offline deterministic fallback rules.

### 2. Best Open-Source AI Project
- **Model Harness for Kiwix/openZIM:** Extends Kiwix by providing a native multimodal Python Model Harness on top of `python-libzim` to query offline `.zim` welfare archives at 0ms latency.
- **Agent Skill Open Standard:** Repository ships with a fully compliant [SKILL.md](file:///c:/Users/Swathi/Desktop/janseva/SKILL.md) specification.
- **100% Public Open-Source:** Released under the MIT License for the openZIM & MLH communities.

---

## 🏛️ Core Modules

```
janseva/
├── core/
│   ├── gemma_harness.py       # Gemma 4 Multimodal Harness (Cloud / Ollama / Offline)
│   ├── verifier.py            # Preflight Linter & Application Readiness Score (0-100%)
│   ├── privacy.py             # DPDP Act 2023 In-RAM Aadhaar Verhoeff & Visual Redactor
│   ├── zim_engine.py          # Native openZIM python-libzim Archive Reader
│   ├── rejection_decoder.py   # 'Kyun Reject Hua?' 3-Part Layman Remedial Engine
│   ├── scheme_finder.py       # Welfare Scheme Matcher & Legal Requirement Tooltips
│   └── serve_mode.py          # JanSeva Serve Mode (Hotspot Pairing & Kiosk Telemetry)
├── packs/
│   ├── build_packs.py         # Native .zim Compiler using libzim.Creator
│   ├── welfare_schemes.zim    # Binary ZIM archive of Welfare Scheme Guides
│   └── rejection_dictionary.zim # Binary ZIM archive of Administrative Error Codes
├── demo_assets/               # Synthetic citizen IDs & rejection slips for 1-click test
├── tests/                     # 23 Unit Tests (100% passing)
└── app.py                     # High-Contrast Kiosk Streamlit Application Shell
```

### Module 1: Preflight Verification & Application Readiness Score (The Killer Feature)
- Cross-checks applicant name (handles South Indian initials expansion like `Ramesh K` vs `Ramesh Kumar` and honorifics).
- Evaluates Date of Birth (reconciles Year-of-Birth only cards vs exact dates).
- Enforces DPDP Act 2023 compliance by redacting the first 8 digits of Aadhaar on-screen and in JSON payloads.
- Generates a weighted **Application Readiness Score (e.g., 85%)** with an operator audit slip export.

### Module 2: "Kyun Reject Hua?" Rejection Notice Decoder
- Ingests physical rejection notices or SMS alerts (e.g. `PFMS Code 04`, `DBT Error 102`, `PMKISAN Land Mismatch`).
- Outputs a 3-part layman plan:
  1. **What Happened:** Plain language summary without bureaucratic jargon.
  2. **The Root Cause:** Underlying banking / administrative reason.
  3. **Remedial Action Plan:** Actionable checklist with exact bank branch to visit and form to request (e.g. Annexure-1).

### Module 3: Welfare Scheme Finder (openZIM RAG Engine)
- Queries offline `.zim` packs at 0ms latency with zero calls to government servers.
- Displays statutory document requirements with legal tooltips (e.g., *Section 7 of Aadhaar Act, 2016*).

### Module 4: JanSeva Serve Mode (The Kiwix Hotspot)
- Enables kiosk operators to serve the app over local Wi-Fi (`janseva.local`).
- Generates a QR code on the kiosk screen for waiting citizens to scan and pair from mobile browsers with 0KB data usage.
- Tracks real-time kiosk telemetry (Preflights Done, Cards Masked, Bandwidth Saved).

---

### Module 5: openZIM Welfare Portal Scraper & Kiwix Desktop Compiler
- **openZIM Standard Compliant:** Crawls live government portals (MyScheme `myscheme.gov.in`, PM-KISAN, Seva Sindhu, Central DBT Bharat) and packages them into standard `.zim` archives with full-text Xapian indexing and offline CSS.
- **Direct Kiwix Desktop Integration:** Compatible with [Kiwix Desktop](https://github.com/Sriram-Nambiar/kiwix-desktop) and [openZIM](https://github.com/openzim). Archives can be opened directly via `File -> Open File...` in Kiwix Desktop for 100% offline, searchable welfare access.
- **Statutory Link Normalization:** Inlines offline typography, converts remote URLs to local ZIM links, and embeds statutory justification guides (Section 7 of Aadhaar Act, APBS DBT mandates).

---

## 🚀 Quickstart

### 1. Install Dependencies
```bash
pip install -r requirements.txt
```

### 2. Run openZIM Welfare Scraper CLI
```bash
# Live crawl from MyScheme portal to Kiwix .zim archive:
python scrape_welfare_to_zim.py --url https://myscheme.gov.in --output packs/myscheme_portal.zim --max-pages 25

# Or compile comprehensive curated welfare pack immediately (0ms network delay):
python scrape_welfare_to_zim.py --curated-pack --output packs/welfare_curated.zim

# Inspect any .zim archive metadata and entries:
python scrape_welfare_to_zim.py --inspect packs/welfare_curated.zim
```

### 3. Open in Kiwix Desktop
1. Download or launch [Kiwix Desktop](https://github.com/Sriram-Nambiar/kiwix-desktop).
2. Click **File → Open File...** and select any compiled `.zim` file (e.g. `packs/welfare_curated.zim`).
3. Search and browse Indian central & state welfare schemes completely offline.

### 4. Run Pytest Suite (35 Unit Tests)
```bash
python -m pytest -v
```

### 5. Launch JanSeva Full Stack
```bash
# Terminal 1: Backend API Server
python -m uvicorn server:app --host 0.0.0.0 --port 8000 --reload

# Terminal 2: React Frontend UI (Vite)
cd frontend
npm run dev -- --host 0.0.0.0 --port 3000
```

---

## 🛡️ The "Why Local-First?" Defense for Judges

> **Judge's Question:** *"India has 5G everywhere, and the government portal is online anyway. Why make the AI local/offline?"*
> 
> **Our Answer:**
> 1. **DPDP Act (2023) Legal Mandate:** Uploading raw, unmasked 12-digit Aadhaar cards and bank passbooks to commercial cloud AI is illegal. JanSeva redacts and processes 100% in local device RAM.
> 2. **Government Portal Server Congestion:** Portals crash during peak hours because millions of kiosks upload heavy 5MB image scans at once. JanSeva acts as an **"ESLint for Welfare"**—performing heavy visual validation on edge kiosks, then transmitting a tiny 1KB verified payload.
> 3. **Eliminating the 15–20% Clerical Rejection Backlog:** Minor typos (e.g., `Ramesh Kumar` vs `Ramesh K`) delay welfare disbursements by weeks. JanSeva catches errors *before* submission.

---

## 👥 Team
- **Sriram S Nambiar:** Lead AI & Core Systems Architect
- **Pavan Adiveppa Harali:** Desktop Interface & Local-Serve Engineer
- **Vasanth S Tumarikoppa:** Knowledge Retrieval & ZIM Pipeline Engineer
- **Raghavendra:** Preflight Logic & Scoring Engine Developer

---

## 📄 License
MIT License. Open-source contribution to the openZIM & MLH community.
