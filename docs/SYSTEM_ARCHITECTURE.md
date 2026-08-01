# MISRA AI Compliance Agent — System Architecture

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. High-Level Architecture Overview

The system uses a decoupled Client-Server architecture:
- **Frontend Layer**: React 18 SPA built with Vite, TypeScript, TailwindCSS, Monaco Diff Editor, and Lucide Icons. Managed via a single-source-of-truth React Context (`AppContext.tsx`).
- **Backend Layer**: FastAPI web framework in Python 3.14, serving RESTful endpoints for C code parsing (`pycparser`), MISRA detection, transactional offset-based patch application, LLM explanations, and ReportLab PDF generation.

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                 FRONTEND (React)                                │
│                                                                                 │
│   ┌──────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌───────┐  │
│   │ Dashboard.tsx│    │  Violations.tsx  │    │GeneratedCode.tsx│    │Reports│  │
│   └──────┬───────┘    └────────┬─────────┘    └────────┬────────┘    └───┬───┘  │
│          │                     │                       │                 │      │
│          └─────────────────────┼───────────────────────┴─────────────────┘      │
│                                │                                                │
│                 ┌──────────────▼───────────────────────┐                        │
│                 │      AppContext.tsx (Context)        │                        │
│                 │ - workingCode (Single Source)        │                        │
│                 │ - allViolations (Immutable Baseline) │                        │
│                 │ - getAnalysisMetrics() Hook          │                        │
│                 └──────────────┬───────────────────────┘                        │
└────────────────────────────────┼────────────────────────────────────────────────┘
                                 │ HTTP / REST
┌────────────────────────────────▼────────────────────────────────────────────────┐
│                                 BACKEND (FastAPI)                               │
│                                                                                 │
│   ┌───────────────────┐    ┌────────────────────┐    ┌──────────────────────┐   │
│   │ /api/upload       │    │ /api/preview-patch  │    │ /api/apply-patches   │   │
│   └─────────┬─────────┘    └─────────┬──────────┘    └──────────┬───────────┘   │
│             │                        │                          │               │
│   ┌─────────▼─────────┐    ┌─────────▼──────────┐    ┌──────────▼───────────┐   │
│   │  AST Detection    │    │ Patch Engine       │    │ Bottom-Up Offset     │   │
│   │  (pycparser)      │    │ (can_autopatch)    │    │ Transactional Engine │   │
│   └───────────────────┘    └────────────────────┘    └──────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Working Code Lifecycle

The application enforces a **Single Authoritative Working Copy** model:

```
  Original File Upload
           │
           ▼
  [ working_code ] ◄── Initialized to original source code
           │
           ├──► User Accepts Patch / Applies Manual Fix
           │        │
           │        ▼
           │    [ setWorkingCode(new_source) ]
           │        │
           │        ├── Updates working_code
           │        ├── Syncs source_code and corrected_code aliases
           │        └── Invalidates previewCache
           │
           ├──► Generated Code View reads working_code
           ├──► Reports PDF Generator serializes working_code
           └──► Re-analysis executes verification pass on working_code
```

---

## 3. Patch Lifecycle State Machine

Each detected violation progresses through a formal state machine:

```
                   ┌──────────┐
                   │ DETECTED │
                   └────┬─────┘
                        │
                        ▼
              ┌───────────────────┐
              │  can_autopatch()  │
              └─────────┬─────────┘
                        │
         ┌──────────────┴──────────────┐
         ▼                             ▼
   [True (Auto)]                [False (Manual)]
         │                             │
         ▼                             ▼
┌──────────────────┐         ┌───────────────────┐
│  PREVIEW_READY   │         │  MANUAL_REQUIRED  │
└────────┬─────────┘         └─────────┬─────────┘
         │                             │
         ├─────────────────────────────┘
         ▼
 ┌──────────────┐        ┌──────────────┐        ┌──────────────┐
 │   ACCEPTED   │   OR   │   REJECTED   │   OR   │   SKIPPED    │
 └───────┬──────┘        └──────────────┘        └──────────────┘
         │
         ▼
  ┌────────────┐
  │  APPLIED   │ (Transaction commits working_code)
  └──────┬─────┘
         │
         ▼
  ┌────────────┐
  │  VERIFIED  │ (Re-analysis confirms 0 remaining)
  └──────┬─────┘
         │
         ▼
  ┌────────────┐
  │   CLOSED   │
  └────────────┘
```

---

## 4. Transactional Bulk Accept Engine

Bulk Accept executes as an **Atomic Transaction**:

1. **Candidate Filtering**: Identifies undecided violations eligible for auto-patching (`can_autopatch == True`).
2. **Offset Op Construction**: Creates `PatchOp` objects with byte-offsets `(start_offset, end_offset)`.
3. **Overlap Resolution**: Sorts by severity (Mandatory > Required > Advisory) and resolves overlapping offset intervals.
4. **Bottom-Up Patch Application**: Applies replacements in **descending offset order** so earlier offsets remain unaffected by later text insertions.
5. **Post-Patch Parse Check**: Runs `pycparser` on the final patched code. Rejects the transaction if C syntax is invalid.
6. **Atomic Commit**: Updates `working_code`, `decisions`, and `analysisResult` **exactly once** in context.
