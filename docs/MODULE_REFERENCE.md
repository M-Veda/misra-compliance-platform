# MISRA AI Compliance Agent — Module Reference

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Backend Modules Reference

### 1.1 `backend.api.main`
- **Purpose**: Core REST API application entry point.
- **Key Functions**:
  - `upload_file()`: Handles `/api/upload`.
  - `preview_patch()`: Handles `/api/preview-patch`.
  - `apply_patches()`: Handles `/api/apply-patches`.
  - `generate_report()`: Handles `/api/generate-report`.
  - `generate_project_report()`: Handles `/api/generate-project-report`.
  - `download_zip()`: Handles `/api/download-zip`.

### 1.2 `backend.services.patch_engine`
- **Purpose**: Transactional offset-based patch application engine.
- **Key Functions**:
  - `can_autopatch(source, v)`: Returns `(bool, reason)`.
  - `apply_single(source, v)`: Single patch execution.
  - `apply_bulk(source, violations)`: Multi-patch bottom-up engine.
  - `_resolve_overlaps(ops)`: Priority-based spatial overlap resolver.
  - `_parse_check(source)`: Post-patch C syntax validator via `pycparser`.

### 1.3 `backend.services.parser`
- **Purpose**: C preprocessing and AST construction service.
- **Key Functions**:
  - `preprocess_and_clean(source_code)`: Strips `#include` and injects `FAKE_LIBC_DEFS`.
  - `parse_code(source_code, file_name)`: Returns `(FileAST, error)`.

### 1.4 `backend.report.generator`
- **Purpose**: PDF and JSON report generation using ReportLab.
- **Key Functions**:
  - `generate_pdf_report()`: Single-file compliance PDF.
  - `generate_project_pdf_report()`: Folder-level project PDF summary.

---

## 2. Frontend Modules Reference

### 2.1 `src/context/AppContext.tsx`
- **Purpose**: Central React Context managing single-source-of-truth state.
- **Key Functions / Hooks**:
  - `workingCode`: State string holding authoritative modified code.
  - `setWorkingCode(code)`: Updates working copy and aliases.
  - `getAnalysisMetrics(fileIdx?)`: Returns unified `AnalysisMetrics`.
  - `setAllViolations(viols)`: Sets baseline violations (guarded against overwrite).

### 2.2 `src/components/Violations.tsx`
- **Purpose**: Interactive human-in-the-loop review interface.
- **Key Logic**:
  - `violationStableKey(v)`: Computes stable violation key.
  - `previewCache`: Caches preview requests.
  - `handleDecision(decision)`: Accepts, rejects, skips, or manual-fixes violations.
  - `executeBulkActionParams(dec, sev)`: Executes atomic bulk accept.
