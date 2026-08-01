# MISRA AI Compliance Agent — Frontend Documentation

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Structure & Technology Stack

- **Framework**: React 18 with TypeScript (`tsc -b`)
- **Build Tool**: Vite 8.1.5
- **Styling**: Vanilla CSS, TailwindCSS utilities, Framer Motion animations
- **Code Editor**: Monaco Diff Editor (`@monaco-editor/react`)
- **Icons**: Lucide React (`lucide-react`)

```
frontend/src/
├── App.tsx                     # Navigation header & tab layout router
├── main.tsx                    # React DOM entry point wrapped in AppProvider
├── index.css                   # Global CSS & glass-panel styling
├── types/
│   └── index.ts                # TypeScript types, PatchState, violationStableKey
├── context/
│   └── AppContext.tsx          # Single source of truth React Context & getAnalysisMetrics
└── components/
    ├── Analysis.tsx            # Single file & folder upload tab
    ├── Dashboard.tsx           # Metrics dashboard & rule distribution pie chart
    ├── Violations.tsx          # Human-in-the-loop review, preview, manual fix, bulk actions
    ├── GeneratedCode.tsx       # Authoritative working copy viewer & download
    ├── Reports.tsx             # PDF/JSON report generation & project report tab
    ├── BulkActionModal.tsx     # Transactional bulk decision modal
    └── Settings.tsx            # User preferences & theme settings
```

---

## 2. Centralized State Architecture (`AppContext.tsx`)

### 2.1 Key State Variables
- **`workingCode`**: The authoritative mutable copy of the code. **All Accept and Manual patch applications update this variable.**
- **`allViolations`**: Immutable baseline snapshot taken on initial analysis. **Guarded against overwrite.**
- **`decisions`**: Map of `violationStableKey(v) -> DecisionType` (`'Accept' | 'Reject' | 'Skip' | 'Manual'`).
- **`manualCodes`**: Map of `violationStableKey(v) -> string` storing manually entered replacement code.
- **`fileList`**: In folder mode, contains `FileAnalysisItem[]` where each file preserves its own `working_code`, `all_violations`, and `decisions`.

### 2.2 Unified Metrics Hook (`getAnalysisMetrics`)
All pages compute statistics through `getAnalysisMetrics(fileIdx?)`. It calculates:
- `total_detected`: `all_violations.length`
- `accepted`: count of decisions equal to `'Accept'`
- `rejected`: count of decisions equal to `'Reject'`
- `skipped`: count of decisions equal to `'Skip'`
- `manual`: count of decisions equal to `'Manual'`
- `remaining`: `violations.length`
- `compliance_score`: $100.0$ if remaining is 0, else $\max(0, 100 - \text{rules\_violated} \times 10)$.

---

## 3. View Specifications

### 3.1 Analysis Tab (`Analysis.tsx`)
- Supports single `.c` file drag-and-drop or selection.
- Supports folder upload (`webkitdirectory`). Traverses recursively, filters for `.c` extensions, and displays a summary card before analysis.
- Calls `resetSession()`, sets `workingCode`, and freezes `allViolations` baseline.

### 3.2 Violations Review Tab (`Violations.tsx`)
- **Stable Violation Indexing**: Uses `violationStableKey(v)`.
- **Preview Cache**: `previewCache` ref caches preview responses keyed by `${stable_id}:${working_code_hash}`.
- **`NoPatchPanel`**: Rendered automatically when `canAutopatch === false`. Displays violation details, reason, recommended fix, and an `[ Enter Manual Fix ]` button.
- **Accept Button Guard**: Enabled ONLY when `canAutopatch === true` AND `patchedCode !== workingCode`.
- **Atomic Bulk Accept**: Executes bulk transaction, commits `workingCode` once, updates context state once.
- **Verification Re-Analysis**: Analyzes `workingCode`. Preserves `allViolations` baseline and `decisions` map. Updates remaining violations and compliance score.

### 3.3 Generated Code Tab (`GeneratedCode.tsx`)
- Displays `workingCode` exclusively using Monaco Editor.
- Provides individual file download (`filename_fixed.c`) and full folder `.zip` download (`folder_fixed.zip`).

### 3.4 Reports Tab (`Reports.tsx`)
- Serializes `getAnalysisMetrics()` data for single file PDF/JSON generation and multi-file project report PDF generation.
