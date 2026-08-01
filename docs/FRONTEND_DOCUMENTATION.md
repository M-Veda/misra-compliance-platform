# MISRA C:2012 Static Analyzer — Frontend Documentation

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. Frontend Technologies & Architecture

- **Core Framework**: React 18 + TypeScript + Vite
- **Styling**: Tailwind CSS with sleek dark theme aesthetics, glassmorphism panels (`glass-panel`), and custom scrollbars
- **Editor & Diffs**: `@monaco-editor/react` (Monaco `DiffEditor` and `Editor`)
- **Icons & Animations**: `lucide-react` icons and `framer-motion` page transitions

---

## 2. Page & Component Structure

1. **`App.tsx`**: Top-level layout with sidebar navigation (Dashboard, Analysis Engine, Violations Review, Generated Code, Compliance Reports).
2. **`Dashboard.tsx`**: High-level compliance overview, active metrics (Accepted, Rejected, Skipped, Manual, Remaining), compliance gauge chart, and recent scan logs.
3. **`Analysis.tsx`**: Single-file and folder upload drag-and-drop zone. Displays initial rule engine parsing progress and violation count summaries.
4. **`Violations.tsx`**: Main human-in-the-loop review workspace:
   - Monaco DiffEditor rendering side-by-side patch previews.
   - Action buttons: `Accept`, `Reject`, `Skip`, `Accept All`, and `Manual Fix`.
   - **Pre-filled Manual Fix Workflow**: Pre-fills the code editor with the analyzer's best safe suggestion. Displays Original Snippet $\rightarrow$ Analyzer Suggestion $\rightarrow$ Pre-filled Editable Code Editor.
5. **`GeneratedCode.tsx`**: Monaco editor displaying `workingCode` (the single source of truth for corrected code). Includes copy to clipboard, individual `.c` download, and multi-file ZIP archive download.
6. **`Reports.tsx`**: Report generation hub for Single File PDF, Project PDF, and machine-readable JSON artifacts.
7. **`BulkActionModal.tsx`**: Multi-pass atomic bulk action transaction modal.

---

## 3. State Management (`AppContext.tsx`)

`AppContext` is the single source of truth for session data:

- `workingCode`: Current authoritative modified code.
- `allViolations`: Immutable baseline violations snapshot set on initial upload.
- `decisions`: Map storing decisions per violation key (`Accept`, `Reject`, `Skip`, `Manual`).
- `getAnalysisMetrics()`: Computes synchronized metrics:
  $$\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Baseline Violations}$$
