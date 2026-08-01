# MISRA C:2012 Static Analyzer — Workflow Documentation

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. End-to-End User Workflows

### Workflow 1: Single File Upload & Analysis
1. User navigates to **Analysis Engine**.
2. User selects or drops a `.c` source file.
3. Backend `/api/upload` endpoint parses AST, runs all 10 rule checkers, computes baseline compliance score, and returns violations list with structured `patch_preview` objects.
4. UI transitions automatically to **Violations Review**.

### Workflow 2: Multi-File Folder Upload & Analysis
1. User drops a folder containing multiple `.c` files in **Analysis Engine**.
2. Frontend creates a `FileAnalysisItem` for each file and runs AST analysis.
3. User can switch active files using the **Active File Selector** dropdown present across Violations, Generated Code, and Reports pages.

---

## 2. Human-in-the-Loop Review Workflow

On the **Violations Review** page:

1. **Selecting an Issue**:
   - Selecting a violation from the left panel triggers `/api/preview-patch`.
   - Monaco DiffEditor renders the side-by-side comparison of original vs proposed code.

2. **Decision Actions**:
   - **`Accept`**: Applies the proposed patch to `workingCode`, updates metrics (`accepted + 1`, `remaining - 1`), invalidates preview cache, and advances to the next violation.
   - **`Reject`**: Marks violation as rejected (`rejected + 1`, `remaining - 1`), keeps original source unchanged, and advances to next violation.
   - **`Skip`**: Defers violation review (`skipped + 1`, `remaining - 1`), source unchanged.
   - **`Manual Fix`** (Pre-filled Workflow):
     - Server/Frontend generates the best safe suggested patch.
     - User is presented with: Original Snippet $\rightarrow$ Suggested Fix $\rightarrow$ Pre-filled Code Editor initialized with the suggested patch.
     - User refines formatting, modifies parentheses, or rewrites logic in the editor.
     - User clicks **Confirm Manual Fix** to apply changes to `workingCode`.

3. **Bulk Actions (`Accept All`)**:
   - Clicking **Bulk Actions $\rightarrow$ Accept All Violations** triggers a multi-pass atomic bulk transaction via `/api/apply-patches`.
   - All auto-patchable violations are applied bottom-up in byte offset order.
   - AST verification scan is executed on the resulting code to verify syntax validity.
   - Counters commit atomically once.

4. **Re-Analysis**:
   - Clicking **Re-analyze Code** posts the current `workingCode` to `/api/upload`.
   - Analyzes remaining violations on the latest modified code without resetting baseline violation history.

---

## 3. Executive Report Generation Workflow

1. User navigates to **Compliance Reports**.
2. User clicks **Generate Report (PDF)** or **Download JSON Report**.
3. Backend `/api/generate-report` serializes finalized session data, generating a ReportLab PDF with clean Latin-1 encoding.
4. In folder mode, clicking **Generate Report (PROJECT PDF)** calls `/api/generate-project-report` to generate an executive multi-file summary PDF.
5. User can also download all fixed `.c` files as a single ZIP archive via **Download All Fixed Files (ZIP)** (`/api/download-zip`).
