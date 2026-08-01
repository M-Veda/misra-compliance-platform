# MISRA AI Compliance Agent — Backend Documentation

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Overview & Technology Stack

The backend is built with:
- **Framework**: FastAPI (Python 3.14)
- **Parser**: `pycparser` v2.22 for AST construction with custom fake libc preprocessor headers.
- **Report Engine**: ReportLab v4.4.1 for PDF generation with sanitized Latin-1 strings.
- **LLM Service**: HuggingFace Transformers / Ollama interface for interactive rule explanations.

---

## 2. Package & Service Architecture

```
backend/
├── api/
│   └── main.py                 # FastAPI endpoints & CORS configuration
├── models/
│   └── violation.py            # RuleViolation, AnalysisResult, Patch models
├── rules/
│   ├── base.py                 # Abstract BaseRule class
│   ├── rule_2_2.py             # Rule 2.2 AST detector
│   ├── rule_2_7.py             # Rule 2.7 AST detector
│   ├── rule_8_4.py             # Rule 8.4 AST detector
│   ├── rule_8_7.py             # Rule 8.7 AST detector
│   ├── rule_9_1.py             # Rule 9.1 AST detector
│   ├── rule_10_3.py            # Rule 10.3 AST detector
│   ├── rule_12_1.py            # Rule 12.1 AST detector
│   ├── rule_14_4.py            # Rule 14.4 AST detector
│   ├── rule_15_5.py            # Rule 15.5 AST detector
│   └── rule_17_7.py            # Rule 17.7 AST detector
├── services/
│   ├── parser.py               # Preprocessor & pycparser AST Service
│   ├── patch_engine.py         # Transactional offset-based patch builders & can_autopatch
│   ├── patch.py                # Single & preview patch generator wrapper
│   └── llm.py                  # TinyLlama / AI explanation service
└── report/
    └── generator.py            # ReportLab PDF & JSON report generator
```

---

## 3. Detailed Service Specifications

### 3.1 C Preprocessor & Parser Service (`backend/services/parser.py`)
- **`preprocess_and_clean(source_code: str) -> (str, str)`**: Strips `#include` directives while preserving empty line offsets. Prepends standard fake libc definitions (`FAKE_LIBC_DEFS`) containing `size_t`, `bool`, `uint32_t`, `printf`, `malloc`, etc.
- **`parse_code(source_code: str, file_name: str) -> (FileAST, str)`**: Parses C source into a `pycparser` `FileAST`. Returns `(ast, None)` on success, or `(None, error_string)` on syntax failure.

### 3.2 Transactional Patch Engine (`backend/services/patch_engine.py`)
- **`MANUAL_ONLY_RULES`**: Set of rules `{"9.1", "15.5"}` requiring manual architectural intervention.
- **`can_autopatch(source: str, v: RuleViolation) -> (bool, str)`**: Validates if an automated patch builder exists, op validation succeeds against source byte offsets, and `apply_single` produces clean C syntax.
- **`apply_single(source: str, v: RuleViolation) -> PatchResult`**: Constructs `PatchOp`, validates byte offsets, applies replacement, and checks syntax via `pycparser`.
- **`apply_bulk(source: str, violations: list[RuleViolation]) -> PatchResult`**: Safe multi-patch engine. Filters candidates with `can_autopatch`, resolves spatial byte overlaps, applies ops in descending order (bottom-up), and validates syntax.

### 3.3 Stable Violation Identifier Generator (`backend/models/violation.py`)
- **`generate_stable_id(rule_number, ast_node_type, scope_name, snippet) -> str`**: Location-independent identifier formulation:
  $$\text{Stable ID} = \text{rule\_number} \text{ \_ } \text{ast\_node\_type} \text{ \_ } \text{scope\_name} \text{ \_ } \text{sha256\_8chars}(\text{normalised\_snippet})$$
  Example: `14_4_If_main_dc7ba4a4`. Survives line-number shifts after earlier edits.

### 3.4 Report Generator (`backend/report/generator.py`)
- **`generate_pdf_report(...)`**: Generates a single-file PDF report formatted with ReportLab. Replaces non-ASCII characters with standard printable ASCII to prevent black square (■) glyphs.
- **`generate_project_pdf_report(...)`**: Generates a multi-file folder project PDF report summarizing total files, overall compliance score, and per-file statistics.
