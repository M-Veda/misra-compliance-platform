# MISRA AI Compliance Agent — API Documentation

> **Base URL**: `http://127.0.0.1:8000/api`  
> **Protocol**: HTTP / JSON / Multipart Form-Data

---

## 1. Endpoints Overview

| Method | Endpoint | Description | Request Payload | Response Payload |
| :---: | :--- | :--- | :--- | :--- |
| **POST** | `/api/upload` | Analyzes a C file against all 10 MISRA rules | `multipart/form-data` (`file`) | `AnalysisResult` |
| **GET** | `/api/rules` | Returns metadata for all 10 implemented rules | None | `{ supported_rules_count, rules }` |
| **POST** | `/api/preview-patch` | Generates patch preview for single violation | `PatchRequest` (JSON) | `PatchResponse` |
| **POST** | `/api/apply-patches` | Transactional bulk patch application | `BulkPatchRequest` (JSON) | `BulkPatchResponse` |
| **POST** | `/api/explain` | Generates LLM explanation of violation | `{ source_code, violation }` | `{ explanation }` |
| **POST** | `/api/generate-report` | Generates single-file PDF/JSON report | `ReportRequest` (JSON) | `{ success, pdf_report_filename, json_report }` |
| **POST** | `/api/generate-project-report` | Generates folder project PDF report | `ProjectReportRequest` | `{ success, pdf_report_filename }` |
| **GET** | `/api/download-pdf/{filename}` | Downloads generated PDF report | None (Path Parameter) | `application/pdf` file stream |
| **POST** | `/api/download-zip` | Packages corrected files into ZIP archive | `DownloadZipRequest` | `application/zip` file stream |

---

## 2. Detailed Endpoint Schemas

### 2.1 `/api/upload`
- **Method**: `POST`
- **Content-Type**: `multipart/form-data`
- **Form Data**: `file` (C source file, e.g. `small.c`)
- **Response Example**:
```json
{
  "success": true,
  "file_name": "small.c",
  "source_code": "int func_0(int a, int b) {\n...\n}",
  "violations": [
    {
      "rule_number": "8.4",
      "rule_name": "Function prototype required",
      "severity": "Required",
      "category": "Declarations",
      "file": "small.c",
      "line": 5,
      "column": 1,
      "message": "Function 'func_0' defined without a visible prototype.",
      "code_snippet": "int func_0(int a, int b) {",
      "reason": "Function 'func_0' has external linkage...",
      "suggested_fix": "int func_0(int a, int b);",
      "confidence": 1.0,
      "ast_node_type": "FuncDef",
      "scope_name": "__global__",
      "stable_id": "8_4_FuncDef___global___a1b2c3d4"
    }
  ],
  "compliance_score": 60.0
}
```

---

### 2.2 `/api/preview-patch`
- **Method**: `POST`
- **Request Payload**:
```json
{
  "source_code": "int func_0(int a, int b) { ... }",
  "violation": { ... },
  "decision": "Accept",
  "manual_code": null
}
```
- **Response Payload**:
```json
{
  "success": true,
  "modified_code": "int func_0(int a, int b);\nint func_0(int a, int b) { ... }",
  "can_autopatch": true,
  "patch_actually_changed": true,
  "no_patch_reason": "",
  "error": null
}
```

---

### 2.3 `/api/apply-patches`
- **Method**: `POST`
- **Request Payload**:
```json
{
  "source_code": "int func_0(int a, int b) { ... }",
  "violations": [ { ... } ]
}
```
- **Response Payload**:
```json
{
  "success": true,
  "modified_code": "/* patched source code */",
  "ops_applied": 10,
  "ops_skipped_already_applied": 0,
  "ops_rejected_validation": 0,
  "ops_rejected_overlap": 0,
  "parse_valid": true,
  "conflicts": [],
  "error": null
}
```
