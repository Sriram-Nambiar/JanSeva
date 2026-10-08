# 🏛️ JanSeva 2.0 — Complete Project Context & Specification
> **For the AI Assistant in the new chat:** This document contains the full context, architectural decisions, hackathon challenge requirements, and technical blueprint established for **JanSeva**. Read this file to immediately continue development without losing any previous decisions.

---

## 1. Project Overview & Identity
- **Project Name:** `JanSeva — Privacy-Preserving Welfare Application Preflight Copilot`
- **Tagline:** *"The client-side linter for government welfare: Verify locally, protect privacy, submit cleanly."*
- **Core Ethos:** *"Rules decide. AI explains. Humans verify."*
- **Ecosystem Integration:** Built directly on top of the **openZIM / Kiwix** offline knowledge infrastructure, powered by **Gemma 4 Multimodal AI**.
- **License:** Open Source (MIT License).
- **Target Event:** Hacktoberfest Hack Day Bengaluru (MLH & IEEE RIT).

---

## 2. Hackathon Tracks & Challenges Targeted

### Challenge 1: Best Use of Gemma 4
- **Multimodal Experience:** Uses Gemma 4 vision to read noisy webcam captures of laminated physical citizen documents (Aadhaar, Ration Card, Bank Passbook) and printed administrative rejection notices.
- **Focused AI Tool:** Solves the 15–20% clerical rejection rate in public welfare delivery.
- **Rapid Prototyping:** Runs via local quantized open weights (Ollama/llama.cpp) with an optional Google Gemini/Gemma Cloud API fallback.

### Challenge 2: Best Open-Source AI Project
- **Model Harness for Kiwix/openZIM:** Extends Kiwix by creating an open-source multimodal Model Harness on top of `python-libzim` to query offline `.zim` welfare archives.
- **Agent Skill Open Standard:** Repository includes a compliant `SKILL.md` specification.
- **100% Public Open-Source:** Full repository published under MIT License.

---

## 3. The Core Problem & The "Why Local-First?" Defense

### The Judge's Challenge & Our Winning Defense:
> **Question from Judges:** *"India has 5G and mobile internet everywhere, and the government portal is online anyway. Why make the AI local/offline?"*
> 
> **Our Answer:**
> We do NOT process locally due to a lack of internet. We process locally to solve the three biggest bottlenecks in Indian public administration:
> 1. **DPDP Act (2023) & Data Privacy:** Uploading citizens' raw, unmasked 12-digit Aadhaar cards and bank passbooks to commercial cloud AI (OpenAI, third-party OCR) is illegal and exposes millions to identity theft. Processing happens 100% in local device RAM.
> 2. **Government Portal Server Congestion ("Server Down"):** Portals crash because millions of kiosks upload heavy 5MB image scans and trigger server-side OCR at once. JanSeva acts like an **"ESLint / Pre-commit Linter" for Welfare**—doing heavy visual validation on edge kiosks, then sending a tiny, clean 1KB verified payload to the server.
> 3. **Eliminating the 15–20% Clerical Rejection Backlog:** Up to 20% of Direct Benefit Transfer (DBT) welfare applications are rejected weeks later due to minor spelling discrepancies (e.g., *"Ramesh Kumar"* vs *"Ramesh K"*). JanSeva catches errors *before* submission.

---

## 4. The 4 Core Modules to Build

### Module 1: Preflight Verification & Application Readiness Score (The Killer Feature)
- Ingests webcam photos of 2 physical ID cards (e.g., Aadhaar + Ration Card).
- Gemma 4 Multimodal extracts key entities (`Name`, `DOB`, `Father's Name`, `ID Number`).
- Cross-checks for clerical mismatches (spelling differences, date variations).
- Automatically masks the first 8 digits of the Aadhaar card for DPDP compliance.
- Generates the **Application Readiness Score (e.g., 78% Ready)** with a "Things to fix before submission" checklist.

### Module 2: "Kyun Reject Hua?" Rejection Notice Decoder
- Ingests a photo of a physical rejection notice or SMS receipt with cryptic administrative error codes (e.g., *"PFMS Code 04: Account not mapped to NPCI"*).
- Maps error code against the local `.zim` rejection dictionary.
- Generates a 3-part layman plan:
  1. What happened.
  2. The root cause.
  3. Action checklist (exact bank branch to visit and form to request).

### Module 3: Welfare Scheme Finder (openZIM RAG Engine)
- Filters schemes from local `.zim` packs based on age, land acreage, and income.
- Queries `python-libzim` at 0ms latency with zero pings to government databases.
- Displays required document lists with "Why this is required" legal tooltips.

### Module 4: JanSeva Serve Mode (The Kiwix Hotspot)
- Operator's laptop enables an embedded local Wi-Fi hotspot (`janseva.local`).
- Waiting citizens connect their mobile phones over local Wi-Fi and use the copilot in their mobile browsers with zero mobile data usage.

---

## 5. Technical Stack
- **Frontend / Application Shell:** Streamlit (Python) with high-contrast, accessible UI.
- **Knowledge Engine:** `python-libzim` reading offline `.zim` Welfare Knowledge Packs.
- **Multimodal AI:** Gemma 4 (via `google-genai` SDK and local Ollama endpoint `localhost:11434`).
- **Data Privacy:** Local PII regex + OpenCV bounding box redactor for 8-digit Aadhaar masking.
- **Agent Standard:** `SKILL.md` adhering to the Agent Skill Open Standard.

---

## 6. Team Structure & Roles
- **LEAD:** Sriram S Nambiar — *Lead AI & Core Systems Architect*
- **MEMBER 2:** Pavan Adiveppa Harali — *Desktop Interface & Local-Serve Engineer*
- **MEMBER 3:** Vasanth S Tumarikoppa — *Knowledge Retrieval & ZIM Pipeline Engineer*
- **MEMBER 4:** Raghavendra — *Preflight Logic & Scoring Engine Developer*
