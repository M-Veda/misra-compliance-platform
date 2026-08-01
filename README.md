# MISRA AI Compliance Agent

> **Verification Scope & Wording**: Validated for the current implemented rule set and tested against the documented scenarios.  
> **Target Standard**: MISRA C:2012 (Automotive & Embedded Safety-Critical C Subset)

---

## Overview

The **MISRA AI Compliance Agent** is a static analysis and interactive remediation suite designed for embedded software engineers. It automates the detection, transactional patch application, and formal compliance report generation for MISRA C:2012 rules.

### Key Features
- **10 Core Deterministic AST Rule Detectors**: Rules 2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4.
- **Single-Source-of-Truth Working Copy**: Centralized state model in React (`AppContext.tsx`).
- **100% Auto-Patchable Range-Based Engine**: Every rule provides 100% deterministic AST detection, unique 17-field coordinate-bound patch previews, and transactional bulk accept.
- **Strict Metric Invariants**: Counter equation $\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Detected}$ holds strictly across all pages.
- **PDF & JSON Report Generation**: Professional ReportLab PDF export free of missing glyph (■) artifacts.

---

## Repository Structure

```
MISRA_Project/
├── backend/                    # FastAPI backend, pycparser AST detectors & patch engine
├── frontend/                   # React 18 SPA, Vite, TypeScript, Monaco Editor
├── perf_test/                  # Benchmark test C source files (small.c, medium.c, large.c)
├── docs/                       # Consolidated Documentation Suite (12 Markdown Files)
│   ├── API_DOCUMENTATION.md
│   ├── BACKEND_DOCUMENTATION.md
│   ├── DEMO_SUITE_GUIDE.md
│   ├── FINAL_PRODUCTION_VERIFICATION_REPORT.md
│   ├── FRONTEND_DOCUMENTATION.md
│   ├── LIMITATIONS_AND_FUTURE_WORK.md
│   ├── PROJECT_OVERVIEW.md
│   ├── RULE_IMPLEMENTATION_GUIDE.md
│   ├── SYSTEM_ARCHITECTURE.md
│   ├── TECHNICAL_AUDIT_REPORT.md
│   ├── TESTING_AND_VALIDATION.md
│   └── WORKFLOW_DOCUMENTATION.md
├── scripts/                    # Validation & benchmark test suite
│   ├── run_full_validation_suite.py
│   ├── verify_demo_suite.py
│   └── benchmark_performance.py
├── LICENSE                     # MIT License
├── requirements.txt            # Python dependencies
├── .gitignore                  # Git ignore configuration
└── README.md                   # Project README
```

---

## Quick Start Guide

### 1. Start Backend Server
```bash
# Navigate to project root
cd c:\Users\saite\OneDrive\Desktop\MISRA_Project

# Install Python dependencies
pip install -r requirements.txt

# Launch FastAPI Uvicorn Server
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### 2. Start Frontend Application
```bash
# Navigate to frontend directory
cd c:\Users\saite\OneDrive\Desktop\MISRA_Project\frontend

# Install Node dependencies
npm install

# Start Vite Development Server
npm run dev
```
Open `http://localhost:5173/` in your browser.

---

## Verification & Testing

To run the automated E2E validation test suite:
```bash
python scripts/run_full_validation_suite.py
```

All 21 automated end-to-end test cases execute against the live API for the supported 10-rule scope.
