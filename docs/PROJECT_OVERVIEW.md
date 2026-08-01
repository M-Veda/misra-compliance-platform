# MISRA C:2012 Static Analyzer & Compliance Platform — Project Overview

> **Version**: Release Baseline 1.0  
> **Date**: August 1, 2026  
> **Target Standard**: MISRA C:2012 (10 Supported Rules)

---

## 1. Executive Summary

The **MISRA C:2012 Compliance Platform** is an enterprise-grade, web-based static analysis and remediation platform designed for embedded C software. It provides deterministic Abstract Syntax Tree (AST) violation detection, interactive side-by-side patch previews, human-in-the-loop remediation workflows, pre-filled manual fix editing, and executive PDF compliance report generation.

The platform focuses on 10 core MISRA C:2012 rules essential for embedded firmware safety and reliability.

---

## 2. Key Platform Features

- **AST-Based Deterministic Analysis**: Uses PyGCCXML / pycparser for standard C AST parsing.
- **Single & Multi-File Folder Support**: Analyzes standalone `.c` files or complete multi-file firmware folders.
- **Interactive Patch Preview**: Side-by-side Monaco diff viewer showing original vs proposed code.
- **Human-in-the-Loop Review Workflow**: Support for `Accept`, `Reject`, `Skip`, `Accept All`, and `Pre-filled Manual Fix` decisions.
- **Pre-filled Manual Fix Workflow**: Pre-fills the code editor with the analyzer's best safe suggestion so developers can refine formatting, adjust parentheses, or rewrite logic before applying.
- **Atomic Bulk Patch Engine**: Range-targeted, bottom-up patch application ensuring syntax validity.
- **Strict Counter & Compliance Invariant**:  
  $$\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Baseline Violations}$$
- **Executive PDF & JSON Compliance Reports**: Professional ReportLab PDF export with clean Latin-1 encoding and zero missing glyphs.

---

## 3. Supported MISRA C:2012 Rules (10 Rules)

| Rule | Category | Title / Description | Patch Policy |
| :---: | :--- | :--- | :--- |
| **2.2** | Unused Code | Statement with no side effects | Auto-patchable |
| **2.7** | Unused Code | Unused function parameter | Auto-patchable |
| **7.1** | Literals | Octal constant usage prohibited | Auto-patchable |
| **8.4** | Declarations | Compatible prototype declaration required | Auto-patchable |
| **8.7** | Declarations | Block scope / internal linkage for single-use globals | Auto-patchable |
| **10.3**| Types | Essential type cast / implicit conversion | **Partial Auto-Patch** |
| **12.1**| Expressions | Explicit operator precedence parentheses | Auto-patchable |
| **14.4**| Control Flow | Controlling expression essentially Boolean | Auto-patchable |
| **16.3**| Control Flow | Switch clause missing `break` statement | Auto-patchable |
| **16.4**| Control Flow | Every switch statement shall have a default clause | Auto-patchable |

> **Rule 10.3 Patch Policy:** Partial Auto-Patch. Safe cases are fixed automatically. Semantic conversions that could alter program behaviour are intentionally left for manual developer review.

---

## 4. Repository Structure Overview

```
MISRA_Project/
├── backend/
│   ├── api/
│   │   └── main.py                 # FastAPI REST API endpoints
│   ├── models/
│   │   └── violation.py            # Violation & patch data models
│   ├── report/
│   │   └── generator.py            # ReportLab PDF & JSON generator
│   ├── rules/                      # Deterministic AST rule checkers (10 rules)
│   │   ├── rule_2_2.py
│   │   ├── rule_2_7.py
│   │   ├── rule_7_1.py
│   │   ├── rule_8_4.py
│   │   ├── rule_8_7.py
│   │   ├── rule_10_3.py
│   │   ├── rule_12_1.py
│   │   ├── rule_14_4.py
│   │   ├── rule_16_3.py
│   │   └── rule_16_4.py
│   └── services/
│       ├── parser.py               # pycparser C AST parser wrapper
│       ├── patch_engine.py         # Range-based bottom-up patch engine
│       └── llm.py                  # AI explanation service
├── docs/                           # Single source of truth documentation
├── fastmcp/                        # FastMCP server stub
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── Dashboard.tsx
│   │   │   ├── Analysis.tsx
│   │   │   ├── Violations.tsx      # Main review workspace & pre-filled manual fix
│   │   │   ├── GeneratedCode.tsx   # Authoritative working copy viewer
│   │   │   ├── Reports.tsx         # PDF/JSON report generation
│   │   │   └── BulkActionModal.tsx # Atomic bulk patch modal
│   │   ├── context/
│   │   │   └── AppContext.tsx      # Single source of truth React context
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── perf_test/                      # Real embedded firmware demo suite
│   ├── small.c                     # Sensor demo (86 lines, 10 violations)
│   ├── medium.c                    # Controller demo (98 lines, 15 violations)
│   ├── large.c                     # BMS demo (98 lines, 15 violations)
│   └── README.md
├── scripts/                        # Automated test & benchmark suite
│   ├── run_full_validation_suite.py
│   ├── verify_demo_suite.py
│   └── benchmark_performance.py
└── requirements.txt
```
