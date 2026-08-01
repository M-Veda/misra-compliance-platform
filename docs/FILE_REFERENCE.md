# MISRA AI Compliance Agent — File Reference

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Complete File Audit Inventory

| File Path | Purpose & Responsibilities | Key Functions / Classes | Used / Deprecated | Safety Status |
| :--- | :--- | :--- | :---: | :---: |
| `backend/api/main.py` | FastAPI application endpoints | `upload_file`, `preview_patch`, `apply_patches`, `generate_report`, `download_zip` | **MUST KEEP** | Core Production API |
| `backend/models/violation.py` | Pydantic data models & stable ID calculation | `RuleViolation`, `generate_stable_id`, `PatchResponse`, `BulkPatchResponse` | **MUST KEEP** | Core Data Schemas |
| `backend/services/parser.py` | C preprocessor & AST parsing | `CParserService`, `preprocess_and_clean`, `parse_code`, `remove_includes` | **MUST KEEP** | Core AST Engine |
| `backend/services/patch_engine.py` | Transactional offset-based patching | `can_autopatch`, `apply_single`, `apply_bulk`, `_resolve_overlaps`, `build_patch_op` | **MUST KEEP** | Core Patch Engine |
| `backend/services/patch.py` | Single patch service wrapper | `PatchService.generate_preview` | **REVIEW** | Legacy wrapper (delegates to `patch_engine`) |
| `backend/services/llm.py` | AI rule explanation generator | `LLMService.answer_question` | **MUST KEEP** | AI Explanation Feature |
| `backend/report/generator.py` | ReportLab PDF report creation | `ReportGenerator.generate_pdf_report`, `generate_project_pdf_report` | **MUST KEEP** | Core Reporting Engine |
| `backend/agent/mcp_server.py` | Model Context Protocol server interface | `MCPServer`, tool registration | **REVIEW** | Optional CLI/MCP Integration |
| `backend/rules/base.py` | Abstract BaseRule interface | `BaseRule` | **MUST KEEP** | Core Detector Base |
| `backend/rules/rule_2_2.py` | Rule 2.2 AST detector | `Rule_2_2` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_2_7.py` | Rule 2.7 AST detector | `Rule_2_7` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_8_4.py` | Rule 8.4 AST detector | `Rule_8_4` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_8_7.py` | Rule 8.7 AST detector | `Rule_8_7` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_9_1.py` | Rule 9.1 AST detector | `Rule_9_1` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_10_3.py` | Rule 10.3 AST detector | `Rule_10_3` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_12_1.py` | Rule 12.1 AST detector | `Rule_12_1` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_14_4.py` | Rule 14.4 AST detector | `Rule_14_4` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_15_5.py` | Rule 15.5 AST detector | `Rule_15_5` | **MUST KEEP** | Core Detector |
| `backend/rules/rule_17_7.py` | Rule 17.7 AST detector | `Rule_17_7` | **MUST KEEP** | Core Detector |
| `frontend/src/context/AppContext.tsx` | Single source of truth React Context | `AppProvider`, `useAppContext`, `getAnalysisMetrics`, `setWorkingCode` | **MUST KEEP** | Core Frontend State |
| `frontend/src/types/index.ts` | TypeScript interfaces & stable key helper | `RuleViolation`, `FileAnalysisItem`, `AnalysisMetrics`, `violationStableKey` | **MUST KEEP** | Core Types |
| `frontend/src/components/Analysis.tsx` | Upload view (single & folder mode) | `Analysis`, `handleSingleFileUpload`, `handleFolderSelection` | **MUST KEEP** | Core UI Tab |
| `frontend/src/components/Violations.tsx` | Violation review & bulk patch view | `Violations`, `handleDecision`, `executeBulkActionParams`, `NoPatchPanel` | **MUST KEEP** | Core UI Tab |
| `frontend/src/components/Dashboard.tsx` | System overview dashboard | `Dashboard`, metrics consumption | **MUST KEEP** | Core UI Tab |
| `frontend/src/components/GeneratedCode.tsx` | Code output & ZIP downloader | `GeneratedCode`, `workingCode` reader | **MUST KEEP** | Core UI Tab |
| `frontend/src/components/Reports.tsx` | PDF report exporter | `Reports`, PDF generation trigger | **MUST KEEP** | Core UI Tab |
| `frontend/src/components/BulkActionModal.tsx` | Bulk accept confirmation modal | `BulkActionModal` | **MUST KEEP** | Core UI Component |
| `frontend/src/components/Settings.tsx` | App settings & appearance configuration | `Settings` | **MUST KEEP** | Core UI Tab |
