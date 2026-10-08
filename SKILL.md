---
name: janseva-welfare-copilot
description: Privacy-preserving offline welfare preflight verifier and rejection decoder built on openZIM and Gemma 4.
version: 1.0.0
license: MIT
metadata:
  model_compatibility: ["gemma-4", "gemma-2-2b", "gemma-multimodal"]
  harness: "openzim-gemma-harness"
  offline_capable: true
  open_standard: "agent-skill-v1"
---

# JanSeva Welfare Copilot Agent Skill

## Overview
JanSeva acts as a client-side preflight copilot for citizen welfare applications. It performs on-device multimodal document cross-verification, redacts sensitive PII under India's DPDP Act, calculates an Application Readiness Score, and decodes administrative rejection slips against local openZIM archives.

## Core Operational Principles
- **Rules Decide:** Deterministic validation engines evaluate statutory scheme criteria.
- **AI Explains:** Gemma 4 multimodal vision translates mismatches and administrative codes into plain language.
- **Humans Verify:** Operators retain final review authority before official submission.

## Tool Definitions
- `evaluate_readiness(applicant_data, document_crops)`: Computes an Application Readiness percentage (0–100%) and returns actionable pre-submission fixes.
- `cross_check_identity(doc_a_fields, doc_b_fields)`: Identifies relational mismatches (e.g., spelling abbreviations) across multi-card camera crops.
- `mask_sensitive_pii(document_image)`: Redacts the first 8 digits of Aadhaar cards for DPDP Act compliance.
- `decode_rejection_clause(notice_image)`: Maps bureaucratic rejection codes from paper slips to step-by-step remedial checklists.
- `query_welfare_zim(query, pack_path)`: Queries offline `.zim` knowledge packs via python-libzim with 0ms cloud latency.
