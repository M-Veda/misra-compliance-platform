# MISRA C:2012 Static Analyzer — System Architecture

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. System High-Level Architecture

The system is structured as a decoupled client-server web application:

```
[ React 18 + Vite + Monaco Diff Editor ]
                 │
                 │ HTTP REST API (JSON)
                 ▼
[ FastAPI Backend (Python 3.14) ]
   ├── Parser Service (pycparser C AST)
   ├── Rule Engine (10 Deterministic AST Rule Checkers)
   ├── Range-Based Patch Engine (patch_engine.py)
   └── Executive Report Generator (ReportLab PDF / JSON)
```

---

## 2. Frontend Architecture (React + TypeScript)

The frontend is built using React 18, Vite, Tailwind CSS, Monaco Editor, and Framer Motion.

### Key Components:
- **`App.tsx`**: Main layout container with top-level sidebar navigation (Dashboard, Analysis Engine, Violations Review, Generated Code, Compliance Reports).
- **`AppContext.tsx`**: The single source of truth for global state. Manages active file selections, baseline violation snapshots (`allViolations`), decisions (`Accept`, `Reject`, `Skip`, `Manual`), and authoritative working source code (`workingCode`).
- **`Violations.tsx`**: Main human-in-the-loop review workspace featuring:
  - Monaco `DiffEditor` for side-by-side patch previews.
  - Action bar for `Accept`, `Reject`, `Skip`, `Accept All`, and `Manual Fix`.
  - Pre-filled Manual Fix workflow displaying original snippet, suggested fix, and an editable pre-filled code editor.
- **`GeneratedCode.tsx`**: Monaco editor displaying the authoritative `workingCode` after all accepted and manual edits. Supports individual `.c` download and folder ZIP download.
- **`Reports.tsx`**: Executive PDF and machine-readable JSON report generator.
- **`BulkActionModal.tsx`**: Progress modal managing multi-pass atomic bulk patch transactions.

---

## 3. Backend Architecture (FastAPI + pycparser)

The backend is implemented in Python using FastAPI.

### Modules:
1. **`backend/api/main.py`**: REST API routes handling file upload, preview generation, bulk patch execution, AI explanation, and report generation.
2. **`backend/services/parser.py`**: C Parser service wrapper around `pycparser`. Preprocesses source code and generates Abstract Syntax Trees.
3. **`backend/rules/`**: Rule checkers implementing the 10 supported MISRA C:2012 rules. Each rule inherits from `BaseRule` and uses AST `NodeVisitor` classes.
4. **`backend/services/patch_engine.py`**: Production range-based bottom-up AST patch engine. Expresses every modification as structured operations (`REPLACE`, `INSERT_BEFORE`, `INSERT_AFTER`, `DELETE`) with exact line, column, and byte offset targeting.
5. **`backend/report/generator.py`**: Executive report generator producing PDFs via ReportLab and JSON summaries.

---

## 4. Single Source of Truth & Data Invariants

1. **`working_code` Single Source of Truth**:
   - `workingCode` is the sole source of truth for Generated Code, Reports, and Re-analysis.
2. **Immutable Baseline**:
   - Initial detection count is frozen on first upload; `Accepted ≤ Total Detected`.
3. **Counter Invariant**:
   $$\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Baseline Violations}$$
   holds strictly across Dashboard, Violations, Reports, and Folder Mode.
