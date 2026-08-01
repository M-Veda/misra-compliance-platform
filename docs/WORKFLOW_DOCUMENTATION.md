# MISRA AI Compliance Agent — Workflow Documentation

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. End-to-End User Workflow Diagram

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  1. FILE UPLOAD │ ──▶ │ 2. AST ANALYSIS  │ ──▶ │ 3. VIOLATIONS LIST  │
│ Single C file / │     │ pycparser AST    │     │ Sorted by Rule &    │
│ Folder Traversal│     │ Rule Detection   │     │ Severity Level      │
└─────────────────┘     └──────────────────┘     └──────────┬──────────┘
                                                            │
                                                            ▼
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  6. RE-ANALYSIS │ ◄── │ 5. WORKING CODE  │ ◄── │ 4. HUMAN DECISION   │
│ Verification    │     │ Single Source of │     │ Accept Patch /      │
│ Check on Code   │     │ Truth Updated    │     │ Manual Fix / Reject │
└────────┬────────┘     └──────────────────┘     └─────────────────────┘
         │
         ▼
┌─────────────────┐     ┌──────────────────┐
│  7. REPORT &    │ ──▶ │ 8. ARTIFACT ZIP  │
│  PDF GENERATE   │     │ Download Final   │
│ Compliance PDF  │     │ Refactored Code  │
└─────────────────┘     └──────────────────┘
```

---

## 2. Step-by-Step Workflow Detailed Breakdown

### Step 1: File / Folder Upload
- User drops a single `.c` file or selects a directory.
- Folder upload recursively collects `.c` files and ignores all non-C file extensions (`.h`, `.txt`, `.md`, `.json`).
- If no `.c` files exist, displays `"No C source files found in the selected folder."`

### Step 2: AST Analysis
- Frontend sends C source to `/api/upload`.
- Backend cleans `#include` statements, prepends fake libc definitions, builds AST via `pycparser`, and runs all 10 rule visitors.
- Freezes baseline `all_violations` and initializes `workingCode`.

### Step 3: Human-in-the-Loop Violations Review
- User selects an issue from the left panel.
- System queries `/api/preview-patch`.
- If `can_autopatch == True`, Monaco Diff Editor displays original vs proposed patch.
- If `can_autopatch == False`, system renders `NoPatchPanel` showing reason and manual fix instructions. `Accept Patch` button is disabled.

### Step 4: Decision & Patch Application
- **Accept Patch**: Validates patch produces non-empty modification. Updates `workingCode`.
- **Manual Fix**: User enters replacement in code editor. System commits user code to `workingCode`.
- **Bulk Accept**: Applies non-overlapping patches in a single bottom-up transaction. Updates `workingCode` once.

### Step 5: Verification Re-Analysis
- User clicks `Re-analyze Code`.
- System posts `workingCode` to `/api/upload`.
- Updates active `violations` list and compliance score.
- **`all_violations` baseline and previous decisions remain frozen.**

### Step 6: Generated Code & Export Reports
- **Generated Code Tab**: Displays finalized `workingCode`. User downloads single file or folder `.zip`.
- **Reports Tab**: User downloads PDF report (`MISRA_Report_...pdf` or `MISRA_Project_Report_...pdf`) and JSON verification artifacts.
