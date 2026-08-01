# MISRA C:2012 Static Analyzer — REST API Documentation

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0  
> **Base URL**: `http://127.0.0.1:8000/api`

---

## 1. Endpoints Specification

### GET `/api/rules`
Returns metadata about the 10 supported MISRA C:2012 rules.

- **Response (200 OK)**:
```json
{
  "supported_rules_count": 10,
  "rules": [
    {
      "rule_number": "2.2",
      "rule_name": "No dead code",
      "severity": "Required",
      "category": "Unused Code",
      "description": "There shall be no dead or unreachable code."
    }
  ]
}
```

---

### POST `/api/upload`
Uploads a `.c` source file, parses AST, runs the rule engine, and returns detected violations with structured `patch_preview` objects.

- **Form Data**: `file` (multipart/form-data, `.c` file)
- **Response (200 OK)**:
```json
{
  "success": true,
  "file_name": "small.c",
  "source_code": "... source content ...",
  "violations": [
    {
      "rule_number": "2.2",
      "rule_name": "No dead code",
      "severity": "Required",
      "category": "Unused Code",
      "file": "small.c",
      "line": 48,
      "column": 5,
      "message": "Statement has no side effects and its result is discarded.",
      "code_snippet": "12345;",
      "reason": "...",
      "suggested_fix": "/* Dead code removed */",
      "confidence": 1.0,
      "patch_preview": { ... }
    }
  ],
  "compliance_score": 70.0
}
```

---

### POST `/api/preview-patch`
Generates a side-by-side patch preview for a single violation without modifying file state.

- **Request Body**:
```json
{
  "source_code": "...",
  "violation": { ... },
  "decision": "Accept",
  "manual_code": null
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "modified_code": "... modified code ...",
  "can_autopatch": true,
  "patch_actually_changed": true,
  "no_patch_reason": "",
  "patch_preview": { ... }
}
```

---

### POST `/api/apply-patches`
Applies all approved violations as an atomic, multi-pass, bottom-up transaction.

- **Request Body**:
```json
{
  "source_code": "...",
  "violations": [ ... ]
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "modified_code": "... patched code ...",
  "ops_applied": 10,
  "ops_skipped_already_applied": 0,
  "ops_rejected_validation": 0,
  "ops_rejected_overlap": 0,
  "parse_valid": true,
  "conflicts": [],
  "error": null
}
```

---

### POST `/api/explain`
Generates a plain-language explanation of why a violation exists and how the fix resolves it.

- **Request Body**: `{ "source_code": "...", "violation": { ... } }`
- **Response (200 OK)**: `{ "explanation": "..." }`

---

### POST `/api/generate-report`
Generates a ReportLab PDF compliance report and returns filename metadata.

- **Request Body**:
```json
{
  "file_name": "small.c",
  "original_code": "...",
  "corrected_code": "...",
  "violations": [ ... ],
  "decisions": { ... },
  "compliance_score": 100.0
}
```
- **Response (200 OK)**: `{ "success": true, "json_report": { ... }, "pdf_report_filename": "MISRA_Report_small_c.pdf" }`

---

### GET `/api/download-pdf/{filename}`
Downloads the generated PDF compliance report file.

---

### POST `/api/download-zip`
Packages all corrected C files in a folder session into a downloadable ZIP archive.

- **Request Body**: `{ "folder_name": "perf_test", "files": [ { "file_name": "small.c", "corrected_code": "..." } ] }`
- **Response (200 OK)**: ZIP binary file response (`perf_test_fixed.zip`).

---

### POST `/api/generate-project-report`
Generates an executive multi-file project summary PDF report.

- **Request Body**: `{ "folder_name": "perf_test", "files_summary": [ ... ], "overall_score": 80.0, "total_files": 3, "total_violations": 40 }`
- **Response (200 OK)**: `{ "success": true, "pdf_report_filename": "MISRA_Project_Report_perf_test.pdf" }`
