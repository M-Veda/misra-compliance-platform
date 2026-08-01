# MISRA C:2012 Static Analyzer — Backend Documentation

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. Backend Architecture Overview

The backend is built with **FastAPI** (Python 3.14) and uses `pycparser` / `PyGCCXML` for C Abstract Syntax Tree (AST) parsing and rule analysis.

```
backend/
├── api/
│   └── main.py                 # FastAPI REST API endpoints
├── models/
│   └── violation.py            # Pydantic data models for violations & patches
├── report/
│   └── generator.py            # ReportLab PDF & JSON report generator
├── rules/                      # 10 Rule checkers
│   ├── base.py                 # Abstract BaseRule class
│   ├── rule_2_2.py
│   ├── rule_2_7.py
│   ├── rule_7_1.py
│   ├── rule_8_4.py
│   ├── rule_8_7.py
│   ├── rule_10_3.py
│   ├── rule_12_1.py
│   ├── rule_14_4.py
│   ├── rule_16_3.py
│   └── rule_16_4.py
└── services/
    ├── parser.py               # pycparser wrapper & line adjustment helper
    ├── patch_engine.py         # Range-based AST patch engine
    └── llm.py                  # TinyLlama AI explanation service
```

---

## 2. Rule Checkers & AST Visitor Logic

Each rule in `backend/rules/` inherits from `BaseRule` and defines:
- `rule_number`: e.g. `"2.2"`
- `rule_name`: Title description
- `severity`: `"Required"` or `"Advisory"`
- `category`: Rule category
- `analyze(ast, source_code, file_name)`: Analyzes AST using custom `NodeVisitor` classes, returning `List[RuleViolation]`.

---

## 3. Patch Engine Architecture (`patch_engine.py`)

The patch engine calculates exact line, column, and byte offsets (`start_offset`, `end_offset`) for every violation:

1. **Structured Operations (`StructuredPatchOp`)**:
   - `REPLACE`: Replaces target code range with modified code.
   - `INSERT_BEFORE` / `INSERT_AFTER`: Prepends prototypes or adds `(void)param;`.
   - `DELETE`: Removes dead code statements.
2. **Bottom-Up Multi-Op Pass (`apply_bulk`)**:
   - Sorts operations in descending byte offset order (`start_offset` descending).
   - Applies patches from bottom of file to top, preventing earlier edits from invalidating offsets of subsequent edits.
   - Re-parses patched code with pycparser to ensure complete syntactic validity before returning.
