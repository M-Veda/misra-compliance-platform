# MISRA AI Compliance Agent — Project Handover & Developer Guide

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Quick Start Guide for New Developers & AI Assistants

### 1.1 Prerequisites
- Python 3.12+ / 3.14+
- Node.js 18+ / 20+

### 1.2 Installation & Startup

#### 1. Backend Startup
```bash
# Navigate to project root
cd c:\Users\saite\OneDrive\Desktop\MISRA_Project

# Install Python dependencies
pip install -r requirements.txt

# Start FastAPI Uvicorn Server
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

#### 2. Frontend Startup
```bash
# Navigate to frontend directory
cd c:\Users\saite\OneDrive\Desktop\MISRA_Project\frontend

# Install dependencies
npm install

# Start Vite Development Server
npm run dev
```

The web application opens at `http://localhost:5173/`.

---

## 2. Key Architecture Invariants to Maintain

When extending or modifying the project, you **MUST preserve the following 4 core invariants**:

1. **Single Source of Truth (`working_code`)**:
   - `workingCode` in `AppContext.tsx` is the ONLY authoritative source of modified code.
   - All Accept patch applications and manual code edits MUST call `setWorkingCode()`.
   - Never create independent local state variables for code output in pages.
2. **Immutable Baseline Snapshot (`all_violations`)**:
   - `all_violations` is frozen on initial upload.
   - Never replace `all_violations` during re-analysis or bulk actions.
   - `Accepted ≤ Total Baseline` MUST hold at all times.
3. **Strict Counter Invariant**:
   - $\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Baseline Detected}$.
   - All components MUST derive statistics via `getAnalysisMetrics()`.
4. **Patch Verification via `can_autopatch`**:
   - Never enable the `Accept Patch` button unless `can_autopatch(source, v)` returns `(True, "")` AND `patchedCode !== workingCode`.
   - Manual-only rules (9.1, 15.5, 17.7) display rule-specific manual remediation panels and direct the developer to provide manual code fixes.

---

## 3. How to Add a New MISRA Rule

To add a new rule detector (e.g., Rule 1.3):

1. **Create Detector**: Create `backend/rules/rule_1_3.py` inheriting from `BaseRule`. Implement `analyze(ast, source_code, file_name)`.
2. **Register Detector**: Add `Rule_1_3` to `_LOADED_RULES` in `backend/rules/__init__.py`.
3. **Create Patch Builder**: If auto-patchable, add `_build_1_3(source, v)` in `backend/services/patch_engine.py` and register it in `_PATCH_BUILDERS`. If manual-only, add `"1.3"` to `MANUAL_ONLY_RULES`.
4. **Verify**: Run `python run_full_validation_suite.py` to ensure all E2E API tests pass.
