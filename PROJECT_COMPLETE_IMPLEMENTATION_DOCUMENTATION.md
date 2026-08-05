# MISRA C:2012 Compliance Platform — Single Source of Truth Complete Implementation Documentation

> **Document Status**: Production Complete & Verified  
> **Target Audience**: System Architects, Safety Software Engineers, Academic Evaluators, & Report Authors  
> **Source Code Basis**: Current Repository State after Full MCP Migration & Production Cleanup

---

## 1. Project Overview

### Purpose
The **MISRA C:2012 Compliance Platform** is an enterprise-grade, human-in-the-loop static code analysis, automated remediation, and compliance workstation. It is engineered specifically for safety-critical C software development in automotive (**ISO 26262**), aerospace (**DO-178C**), and medical device (**IEC 62304**) engineering domains.

### Scope
The platform accepts standard C source code files (`.c`) or zipped project directories, preprocesses directives, constructs C99 Abstract Syntax Trees (AST), deterministically detects violations of 10 core MISRA C:2012 rules, computes location-independent range patches, presents side-by-side Monaco diff previews, delegates live runtime AI violation explanations to a local TinyLlama LLM over an **Official Model Context Protocol (MCP v2.0.0)** server, applies bottom-up byte offset remediation, and generates publication-grade PDF compliance reports.

### Objectives
- **Zero Hallucination Rule Analysis**: Rely strictly on AST visitors (`pycparser`) rather than regex pattern matching or LLMs for rule checking.
- **Human-in-the-Loop Authority**: Require developer explicit confirmation (**Accept**, **Reject**, **Skip**, **Manual**) before mutating code.
- **Architectural Decoupling**: Isolate backend business logic from LLM runtime details using an Official Model Context Protocol (MCP v2.0.0) Server architecture.
- **Mathematical Metric Invariants**: Guarantee that $\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Detected}$ holds true across all UI views and PDF report exports.
- **Stateless PDF Generation**: Streams ReportLab PDF compliance reports directly from system temporary storage without permanent local file footprint or JSON file pollution.

---

## 2. Complete Feature List

### Fully Implemented Features

1. **Deterministic AST MISRA Detection Engine**:
   - Rule 2.2 (Required): Dead Code Detection & Elimination.
   - Rule 2.7 (Advisory): Unused Parameter Detection & Void Casting.
   - Rule 7.1 (Required): Octal Literal Detection & Conversion to Decimal.
   - Rule 8.4 (Required): Compatible Prototype Declaration Requirement.
   - Rule 8.7 (Advisory): Internal Linkage (`static` keyword) Enforcer.
   - Rule 10.3 (Required): Prohibited Implicit Conversion Cast Inserter.
   - Rule 12.1 (Advisory): Operator Precedence Parentheses Enforcer.
   - Rule 14.4 (Required): Essentially Boolean Controlling Expression Transformer.
   - Rule 16.3 (Required): Switch Case Missing `break;` Inserter.
   - Rule 16.4 (Required): Switch Statement Missing `default:` Clause Inserter.

2. **Interactive Monaco Side-by-Side Diff Workstation**:
   - Visual comparison between original C code and proposed remediation patch.
   - Syntax highlighting for C language constructs.
   - Inline manual code editing for custom patch overrides.

3. **Bottom-Up Bulk Auto-Patch Engine**:
   - Resolves multi-violation remediation conflicts.
   - Applies byte-offset range replacements in descending order to avoid coordinate drift.
   - Performs post-patch AST re-parsing syntax validation.

4. **Official Model Context Protocol (MCP v2.0.0) AI Engine**:
   - Decoupled `FastAPI Backend` → `MCP Client` → `Official MCP Server` → `AI Provider` → `Ollama` → `TinyLlama` architecture.
   - Exposes standard MCP tools (`generate_misra_explanation`, `answer_code_question`, `review_patch`).
   - Returns live structured TinyLlama model inferences covering rule summary, safety risk analysis, fix rationale, and impact metrics.
   - Graceful offline handling: Returns an explicit offline status when Ollama is unavailable without fabricating fake AI content.

5. **Publication-Grade PDF Report Generator**:
   - Programmatic ReportLab PDF generation.
   - Compliance score gauge, severity distribution tables, rule summary, decision log.
   - Auto-deletes temp files immediately upon streaming completion.

6. **Multi-File Folder Batch Mode**:
   - Accepts multi-file folder uploads.
   - Displays aggregated multi-file compliance metrics and per-file violation trees.
   - Exports corrected codebase as a single `.zip` archive.

### Partially Implemented Features / Known Scope Boundaries
- **Preprocessor Macro Expansion**: Complex `#define` macros are stripped during preprocessing to allow `pycparser` C99 parsing.
- **Single Translation Unit Symbol Resolution**: Rules 8.4 and 8.7 evaluate symbols within individual C files; multi-file project analysis mode processes files sequentially.

---

## 3. Complete Workflow

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   React Frontend UI                                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ HTTP POST /api/upload (.c file / folder)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FastAPI Backend                                     │
│                                  (backend/api/main.py)                                 │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Raw Source Code Bytes
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    C Parser Service                                    │
│                              (backend/services/parser.py)                              │
│             Strips Directives + Injects FAKE_LIBC_DEFS + Builds FileAST                    │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ pycparser FileAST
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                              MISRA Deterministic Rule Engine                           │
│                              (backend/rules/__init__.py)                               │
│                      Executes 10 AST Visitors (ALL_RULES)                              │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ Structured RuleViolation Objects
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   Patch Preview Engine                                 │
│                           (backend/services/patch_engine.py)                           │
│                     Generates 17-field Structured PatchPreviews                        │
└───────────────────────────────────────────┬────────────────────────────────────────────┘
                                            │ JSON Response
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                           Monaco Diff Workstation & Metrics UI                         │
│                    Developer Selects Accept / Reject / Skip / Manual                   │
└───────┬───────────────────────────────────┬────────────────────────────────────┬───────┘
        │                                   │                                    │
        │ Click Ask AI                      │ Apply Patches                      │ Export PDF
        ▼                                   ▼                                    ▼
┌──────────────┐                   ┌────────────────┐                   ┌────────────────┐
│  MCP Client  │                   │ Bulk Patch Pass│                   │  ReportLab PDF │
└───────┬──────┘                   └───────┬────────┘                   └───────┬────────┘
        │ MCP JSON-RPC                     │ Descending Offsets                 │ Render PDF
        ▼                                  ▼                                    ▼
┌──────────────┐                   ┌────────────────┐                   ┌────────────────┐
│  MCP Server  │                   │ Re-parse AST   │                   │ Stream Download│
└───────┬──────┘                   └────────────────┘                   └────────────────┘
        │ Live Inference
        ▼
┌──────────────┐
│  TinyLlama   │
└──────────────┘
```

---

## 4. Complete Folder Structure

```
MISRA_Project/
├── backend/                        # FastAPI Backend Application Root
│   ├── api/                        # REST Controllers & API Endpoints
│   │   ├── __init__.py
│   │   └── main.py                 # FastAPI Application Server & Route Definitions
│   ├── mcp/                        # Backend Model Context Protocol Client Layer
│   │   ├── __init__.py
│   │   └── client.py               # MCPClient Class Invoking MCP Tools
│   ├── models/                     # Data Models & Schemas
│   │   ├── __init__.py
│   │   └── violation.py            # Pydantic Schemas (RuleViolation, PatchPreview, etc.)
│   ├── report/                     # Compliance Report Generator Module
│   │   ├── __init__.py
│   │   └── generator.py            # ReportLab PDF Report Generation Service
│   ├── rules/                      # Deterministic AST MISRA Rule Visitor Engine
│   │   ├── __init__.py             # Rules Registry & ALL_RULES Array
│   │   ├── base.py                 # Abstract BaseRule Interface Definition
│   │   ├── rule_2_2.py             # Rule 2.2 AST Detector (Dead Code)
│   │   ├── rule_2_7.py             # Rule 2.7 AST Detector (Unused Parameter)
│   │   ├── rule_7_1.py             # Rule 7.1 AST Detector (Octal Literals)
│   │   ├── rule_8_4.py             # Rule 8.4 AST Detector (Prototype Declaration)
│   │   ├── rule_8_7.py             # Rule 8.7 AST Detector (Internal Linkage)
│   │   ├── rule_10_3.py            # Rule 10.3 AST Detector (Essential Type Cast)
│   │   ├── rule_12_1.py            # Rule 12.1 AST Detector (Precedence Parentheses)
│   │   ├── rule_14_4.py            # Rule 14.4 AST Detector (Boolean Controlling Expr)
│   │   ├── rule_16_3.py            # Rule 16.3 AST Detector (Switch Case Break)
│   │   └── rule_16_4.py            # Rule 16.4 AST Detector (Switch Default Clause)
│   ├── services/                   # Core Domain Application Services
│   │   ├── __init__.py
│   │   ├── llm.py                  # LLM Service Wrapper (Delegates to MCP Client)
│   │   ├── parser.py               # Preprocessor & pycparser AST Service
│   │   ├── patch.py                # Single Patch Preview Service Adapter
│   │   └── patch_engine.py         # Range-Based Offset Patch & AST Validation Engine
│   └── tests/                      # Automated Pytest Test Suite
│       ├── test_bulk_accept_regression.py
│       ├── test_e2e_stress.py
│       ├── test_metrics_consistency.py
│       ├── test_patch_engine.py
│       ├── test_rule_verification.py
│       └── test_rules.py
├── frontend/                       # React 18 + TypeScript Web Application Root
│   ├── public/                     # Static Web Assets
│   ├── src/                        # React Application Source Code
│   │   ├── App.tsx                 # Root React Application Component
│   │   ├── main.tsx                # React DOM Mount Entrypoint
│   │   ├── index.css               # Global Tailwind CSS Stylesheet
│   │   ├── components/             # UI Tab Pages & Components
│   │   │   ├── Analysis.tsx        # File/Folder Upload & Initial Metrics Page
│   │   │   ├── BulkActionModal.tsx # Bulk Patch Confirmation Modal
│   │   │   ├── Dashboard.tsx       # Analytics, Compliance Score, Gauges Page
│   │   │   ├── GeneratedCode.tsx   # Corrected Code & ZIP Download Page
│   │   │   ├── Header.tsx          # Navigation Bar & Status Header Component
│   │   │   ├── MetricCard.tsx      # Analytical Metric Card Component
│   │   │   ├── Reports.tsx         # Executive PDF Report Export Page
│   │   │   └── Violations.tsx      # Violations Tree & Monaco Diff Editor Workstation
│   │   ├── context/
│   │   │   └── AppContext.tsx      # Application Global State & Counter Engine
│   │   └── types/
│   │       └── index.ts            # Shared TypeScript Domain Type Definitions
│   ├── index.html                  # Main Web HTML Template
│   ├── package.json                # Frontend Node Dependencies Manifest
│   ├── postcss.config.js           # PostCSS Configuration
│   ├── tailwind.config.js          # Tailwind CSS Configuration
│   ├── tsconfig.json               # TypeScript Compiler Configuration
│   └── vite.config.ts              # Vite Bundler & Development Server Config
├── mcp_server/                     # Standalone Model Context Protocol (MCP) Server
│   ├── __init__.py
│   ├── ai_provider.py              # Pluggable AI Capabilities Layer (Ollama/TinyLlama)
│   ├── prompts.py                  # Prompt Engineering Engine & Structured Schemas
│   └── server.py                   # Official MCP 2.0.0 Server (mcp.server.Server)
├── perf_test/                      # Performance Benchmarking Fixtures
├── scripts/                        # System Benchmark & Validation Scripts
│   ├── benchmark_performance.py
│   ├── run_full_validation_suite.py
│   ├── test_red_team_edge_cases.py
│   └── verify_demo_suite.py
├── LICENSE                         # MIT Software License
├── README.md                       # Public Overview Documentation
├── requirements.txt                # Python Dependencies Manifest
└── PROJECT_COMPLETE_IMPLEMENTATION_DOCUMENTATION.md # Single Source of Truth Documentation
```

---

## 5. Complete File-by-File Documentation

### Backend Infrastructure (`backend/`)

#### [backend/api/main.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/api/main.py)
- **Purpose**: Main FastAPI REST API application controller.
- **Responsibility**: Exposes HTTP endpoints for code upload, rule discovery, LLM explanations via MCP, patch previews, bulk patch applications, interactive chat, PDF report generation, and file streaming.
- **Key Functions**: `get_rules()`, `upload_file()`, `explain_violation()`, `preview_patch()`, `apply_patches()`, `chat()`, `generate_report()`, `download_pdf()`, `download_zip()`.
- **Runtime-Critical**: YES.

#### [backend/mcp/client.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/mcp/client.py)
- **Purpose**: Backend Client implementation for Model Context Protocol (MCP v2.0.0).
- **Responsibility**: Wraps `OfficialMCPServer` tool invocations (`call_tool`). Exposes semantic AI helper methods: `generate_misra_explanation`, `answer_code_question`, `review_patch`.
- **Key Classes**: `MCPClient`.
- **Runtime-Critical**: YES (for AI explanations and chat).

#### [backend/models/violation.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/models/violation.py)
- **Purpose**: Pydantic domain data models.
- **Responsibility**: Defines strict type schemas and SHA-256 stable ID generation for violations, patch previews, and API requests.
- **Key Classes**: `RuleViolation`, `PatchPreview`, `PatchRequest`, `BulkPatchRequest`, `ExplainRequest`, `ChatRequest`, `ReportRequest`.
- **Runtime-Critical**: YES.

#### [backend/report/generator.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/report/generator.py)
- **Purpose**: Programmatic PDF report generation engine.
- **Responsibility**: Uses ReportLab to construct publication-grade PDF compliance reports containing compliance score gauges, severity breakdown tables, rule summaries, decision logs, and clean string sanitization.
- **Key Classes**: `ReportGenerator`.
- **Key Functions**: `generate_pdf_report()`.
- **Runtime-Critical**: YES.

#### [backend/rules/base.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/rules/base.py)
- **Purpose**: Abstract Base Class interface for deterministic MISRA rules.
- **Responsibility**: Defines contract (`analyze()`) for AST node visitor implementation.
- **Key Classes**: `BaseRule`.
- **Runtime-Critical**: YES.

#### [backend/rules/rule_2_2.py ... rule_16_4.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/rules/)
- **Purpose**: Deterministic AST MISRA detector modules (10 modules).
- **Responsibility**: Extends `c_ast.NodeVisitor` from `pycparser` to inspect AST nodes and report violations.
- **Key Classes**: `Rule2_2`, `Rule2_7`, `Rule7_1`, `Rule8_4`, `Rule8_7`, `Rule10_3`, `Rule12_1`, `Rule14_4`, `Rule16_3`, `Rule16_4`.
- **Runtime-Critical**: YES.

#### [backend/services/parser.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/services/parser.py)
- **Purpose**: Preprocessor and pycparser AST generator service.
- **Responsibility**: Strips `#include` directives while preserving line offsets, prepends `FAKE_LIBC_DEFS`, and parses raw C string into a `pycparser` C99 `FileAST`.
- **Key Classes**: `CParserService`.
- **Runtime-Critical**: YES.

#### [backend/services/patch_engine.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/services/patch_engine.py)
- **Purpose**: Range-based byte offset patch engine and AST validator.
- **Responsibility**: Generates 17-field `PatchPreview` objects, computes line start offsets, resolves overlapping range conflicts, applies bottom-up byte replacements in descending order, and validates post-patch C code syntax.
- **Key Functions**: `generate_patch_previews()`, `apply_bulk_patches_bottom_up()`, `validate_c_syntax()`.
- **Runtime-Critical**: YES.

#### [backend/services/llm.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/services/llm.py)
- **Purpose**: Lightweight backend orchestration wrapper.
- **Responsibility**: Routes AI explanation and chat requests to `MCPClient`. Completely purged of Ollama URLs or direct REST calls.
- **Key Classes**: `LLMService`.
- **Runtime-Critical**: YES.

---

### Model Context Protocol Server (`mcp_server/`)

#### [mcp_server/server.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/mcp_server/server.py)
- **Purpose**: Official Model Context Protocol (MCP v2.0.0) Server.
- **Responsibility**: Wraps `mcp.server.Server` ("misra-compliance-ai-server"). Registers official request handlers for `"tools/list"` (`types.ListToolsRequest`) and `"tools/call"` (`types.CallToolRequestParams`). Implements standard stdio runner (`run_stdio_server`).
- **Key Classes**: `OfficialMCPServer`.
- **Runtime-Critical**: YES.

#### [mcp_server/ai_provider.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/mcp_server/ai_provider.py)
- **Purpose**: AI Capabilities Layer abstraction.
- **Responsibility**: Encapsulates Ollama REST client HTTP calls (`http://localhost:11434/api/chat`), timeout handling, connection error recovery, and robust JSON extraction/repair.
- **Key Classes**: `BaseAIProvider`, `OllamaProvider`.
- **Key Functions**: `extract_json_from_response()`.
- **Runtime-Critical**: YES.

#### [mcp_server/prompts.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/mcp_server/prompts.py)
- **Purpose**: Centralized prompt engineering engine.
- **Responsibility**: Defines expert system prompts (`SYSTEM_PROMPT_EXPERT`, `SYSTEM_PROMPT_QA`) and context-rich prompt builders (`build_misra_explanation_prompt`, `build_code_qa_prompt`, `build_patch_review_prompt`).
- **Runtime-Critical**: YES.

---

### Frontend Components (`frontend/src/`)

#### [frontend/src/App.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/App.tsx)
- **Purpose**: Main React shell component.
- **Responsibility**: Manages active tab navigation (Analysis, Dashboard, Violations, Generated Code, Reports) and header layout.
- **Runtime-Critical**: YES.

#### [frontend/src/context/AppContext.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/context/AppContext.tsx)
- **Purpose**: Global application React Context provider.
- **Responsibility**: Maintains single source of truth for uploaded files, AST violations, patch previews, user decisions (Accepted, Rejected, Skipped, Manual), metrics counter equations, and API communications.
- **Runtime-Critical**: YES.

#### [frontend/src/components/Violations.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/components/Violations.tsx)
- **Purpose**: Side-by-side Monaco diff code review workstation and Ask AI modal.
- **Responsibility**: Renders file violation tree, Monaco DiffEditor, decision buttons, manual edit editor, bulk patch modal trigger, and structured AI explanation popup.
- **Runtime-Critical**: YES.

#### [frontend/src/components/Dashboard.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/components/Dashboard.tsx)
- **Purpose**: Executive analytical dashboard.
- **Responsibility**: Visualizes compliance score percentage, SVG radial compliance score gauge, severity distribution cards, decision metrics, and project overview cards.
- **Runtime-Critical**: YES.

#### [frontend/src/components/Analysis.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/components/Analysis.tsx)
- **Purpose**: File & folder upload landing page.
- **Responsibility**: Provides drag-and-drop file upload, folder selection, file parsing trigger, and initial summary card display.
- **Runtime-Critical**: YES.

#### [frontend/src/components/Reports.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/components/Reports.tsx)
- **Purpose**: Compliance report export page.
- **Responsibility**: Offers single-click trigger for executive PDF compliance report generation and streaming download.
- **Runtime-Critical**: YES.

#### [frontend/src/components/GeneratedCode.tsx](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/frontend/src/components/GeneratedCode.tsx)
- **Purpose**: Remediation artifact export workstation.
- **Responsibility**: Displays final corrected C source code and provides single-click ZIP archive export for multi-file folder batches.
- **Runtime-Critical**: YES.

---

## 6. Backend Architecture

- **Framework**: FastAPI (asynchronous ASGI framework running on Uvicorn).
- **Architecture Pattern**: Controller Services Repositories (Layered Domain Architecture).
- **Data Transfer**: Pydantic v2 schemas enforcing strict validation.

### API Endpoints
- `GET /api/rules`: Returns metadata array for all 10 MISRA rules.
- `POST /api/upload`: Multipart upload endpoint processing C files, executing AST visitors, and returning structured violations.
- `POST /api/explain`: Receives violation payload, delegates to `MCPClient.generate_misra_explanation()`, and returns live TinyLlama analysis.
- `POST /api/preview-patch`: Previews individual patch decision.
- `POST /api/apply-patches`: Executes bottom-up bulk patch remediation.
- `POST /api/chat`: Interactive QA assistant endpoint routing questions to TinyLlama via MCP Client.
- `POST /api/generate-report`: Triggers ReportLab PDF generation in temp storage.
- `GET /api/download-pdf/{filename}`: Streams generated PDF report and executes background file deletion.
- `POST /api/download-zip`: Packages corrected C files into a ZIP archive for folder mode.

---

## 7. Frontend Architecture

- **Framework**: React 18 + TypeScript powered by Vite.
- **Editor Engine**: Monaco Editor (`@monaco-editor/react`) for side-by-side diff code editing.
- **Styling**: Tailwind CSS with custom glassmorphism panels, dark mode styling, and dynamic metric badges.
- **State Management**: Centralized React Context (`AppContext.tsx`) maintaining single source of truth for counter invariants:
  $$\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Detected}$$

---

## 8. MCP Architecture & Centralized Prompt Management Layer

The Model Context Protocol (MCP v2.0.0) architecture separates the application into distinct capability layers:

```
React UI ──► FastAPI Backend ──► MCP Client ──► Official MCP Server ──► PromptManager ──► AI Provider Layer ──► Ollama ──► TinyLlama
```

1. **Official MCP Server (`mcp_server/server.py`)**: Uses `mcp.server.Server` ("misra-compliance-ai-server"). Exposes 3 semantic tools:
   - `generate_misra_explanation`: Tool generating structured MISRA violation analysis.
   - `answer_code_question`: Tool answering developer C code questions.
   - `review_patch`: Tool reviewing proposed C code patches.
2. **Centralized Prompt Management Layer (`mcp_server/prompts/` & `mcp_server/prompt_manager.py`)**:
   - `misra_explanation.md`, `code_qa.md`, `patch_review.md`: Standards-based Markdown prompt templates stored separately from Python code.
   - `PromptManager`: Class dynamically loading markdown templates and formatting variables without hardcoding large prompt strings in business logic.
   - `mcp_server/prompts.py`: Clean facade wrapper maintaining modular compatibility.
3. **AI Capabilities Layer (`mcp_server/ai_provider.py`)**: `OllamaProvider` executes live inference via Ollama HTTP API (`http://localhost:11434/api/chat`).
4. **MCP Client (`backend/mcp/client.py`)**: Issues MCP tool calls (`call_tool`) to the server.

---

## 9. AI Explanation Pipeline

1. **Trigger**: Developer clicks **Ask AI** on a violation in `Violations.tsx`.
2. **HTTP Request**: Frontend posts `{ violation, source_code }` to `/api/explain`.
3. **Backend Delegation**: `LLMService.get_structured_explanation(...)` forwards request to `MCPClient.generate_misra_explanation(...)`.
4. **MCP Execution**: `MCPClient` executes MCP tool call `generate_misra_explanation` on `OfficialMCPServer`.
5. **Prompt Template Loading**: `OfficialMCPServer` retrieves the prompt from `mcp_server/prompts/misra_explanation.md` via `PromptManager` (`mcp_server/prompt_manager.py`).
6. **LLM Inference**: `OfficialMCPServer` delegates inference to `OllamaProvider` running TinyLlama.
7. **JSON Repair & Validation**: `extract_json_from_response` extracts and validates JSON fields (`misra_summary`, `why_it_matters`, `ai_analysis`, `why_fix_works`, `alternative_fixes`, `impact_analysis`, `confidence`).
8. **Offline Safeguard**: If Ollama is offline or unavailable, `is_available: False` is returned. The UI renders an explicit offline alert banner without fabricating fake AI text.

---

## 10. Rule Detection Pipeline

1. **Source Sanitization**: `CParserService` strips preprocessor `#include` directives while inserting blank space lines to maintain exact line numbers.
2. **Standard Library Inject**: Prepends `FAKE_LIBC_DEFS` (standard C type typedefs for `size_t`, `uint8_t`, `bool`, etc.).
3. **AST Construction**: `pycparser.c_parser.CParser().parse()` generates a complete C99 `FileAST`.
4. **Visitor Execution**: `backend/rules/__init__.py` runs the 10 AST visitor modules (`ALL_RULES`) over the AST nodes.
5. **Violation Generation**: Visitors create `RuleViolation` objects containing rule number, severity, line, column, code snippet, and suggested fix.

---

## 11. Report Generation

- **Engine**: ReportLab PDF library ([backend/report/generator.py](file:///c:/Users/saite/OneDrive/Desktop/MISRA_Project/backend/report/generator.py)).
- **Content**:
  - Publication header & document metadata.
  - Compliance Score Gauge & Executive Summary.
  - Severity Breakdown Table (Mandatory, Required, Advisory).
  - Rule-Wise Statistics & Decision Table (Accepted, Rejected, Skipped, Manual).
  - Detailed Violation Logs with code snippets and remediation actions.
- **Sanitization**: All code snippets are processed through `sanitize_for_pdf()` to strip unprintable control characters and prevent black square glyph artifacts.
- **Stateless Delivery**: PDF files are created in OS temporary storage (`tempfile.gettempdir()`), streamed via `FileResponse`, and automatically deleted immediately after download.

---

## 12. Technology Stack

- **Frontend**: React 18, TypeScript, Vite, Monaco Editor, Tailwind CSS, Lucide Icons, Framer Motion.
- **Backend API**: Python 3.10+, FastAPI, Uvicorn, Pydantic v2, pycparser, ReportLab, Pytest.
- **AI Infrastructure**: Model Context Protocol (MCP v2.0.0 SDK), Ollama API, TinyLlama model.

---

## 13. API Documentation

### `POST /api/upload`
- **Request**: Multipart `UploadFile` (`file`).
- **Response**:
  ```json
  {
    "filename": "main.c",
    "total_violations": 5,
    "violations": [ ... ],
    "patch_previews": [ ... ],
    "compliance_score": 75.0,
    "metrics": { "total": 5, "accepted": 0, "rejected": 0, "skipped": 0, "manual": 0, "remaining": 5 }
  }
  ```

### `POST /api/explain`
- **Request**: `{ "violation": { ... }, "source_code": "..." }`
- **Response**:
  ```json
  {
    "success": true,
    "is_available": true,
    "misra_summary": "...",
    "why_it_matters": "...",
    "ai_analysis": "...",
    "recommended_fix": "...",
    "impact_analysis": { "runtime": "0% penalty", ... },
    "confidence": 0.95
  }
  ```

### `POST /api/generate-report`
- **Request**: `{ "filename": "main.c", "metrics": { ... }, "violations": [ ... ] }`
- **Response**: `{ "filename": "misra_report_main_c_17857.pdf" }`

---

## 14. Data Flow

```
[User Upload .c File] ──► [FastAPI /api/upload] ──► [CParserService AST]
                                                             │
[Monaco Diff UI] ◄── [Patch Preview Engine] ◄── [10 AST MISRA Rules]
       │
       ├──► [Ask AI] ──► [MCP Client] ──► [MCP Server] ──► [TinyLlama LLM]
       ├──► [Accept Patch] ──► [Bottom-Up Offset Engine] ──► [AST Re-Parse Check]
       └──► [Export PDF] ──► [ReportLab Generator] ──► [Streamed Temp File]
```

---

## 15. Error Handling

- **C Syntax Parse Errors**: If `pycparser` encounters invalid syntax, `CParserService` catches `ParseError` and returns a clean, line-annotated syntax error message to the user.
- **AI Provider Offline**: If Ollama or TinyLlama is offline, `OllamaProvider` catches `requests.exceptions.ConnectionError` and returns `is_available: False`. The UI displays a warning banner without fabricating fake AI text.
- **Patch Range Conflicts**: `patch_engine.py` detects overlapping replacement ranges and resolves them deterministically by selecting higher severity rules (Mandatory > Required > Advisory).

---

## 16. Security Measures

- **No Public Unsanitized Directives**: Includes prepended fake headers in isolated AST memory without shell execution.
- **Sanitized PDF Output**: ReportLab string sanitization prevents font injection and black box rendering artifacts.
- **Stateless Storage & Auto-Cleanup**: Temp PDF files are deleted immediately after download to prevent data residual leaks.
- **Local Private LLM**: AI inference runs 100% locally via Ollama / TinyLlama; zero source code data leaves the local workstation environment.

---

## 17. Current Limitations

1. **Complex Preprocessor Macros**: Strips `#define` macro calls during AST parsing.
2. **Single Translation Unit Symbol Scope**: Rules 8.4 and 8.7 evaluate symbols at single file scope; multi-file project mode processes files sequentially.

---

## 18. Future Scope

1. **Clang AST Compiler Bindings**: Replace `pycparser` with Clang AST python bindings for full C11/C17 standard support and complete preprocessor expansion.
2. **Expanded Rule Suite**: Implement detectors for MISRA C:2012 Rules 9.1, 15.5, 17.7, and 21.1.
3. **CI/CD Runner Integration**: Package backend into a lightweight Docker container for GitHub Actions and GitLab CI automated pull request checks.

---

## 19. Testing

- **Backend Pytest Suite**: 96 unit and integration tests passing (`pytest backend/tests/`).
  - `test_rules.py`: Positive and negative AST detector test cases for all 10 rules.
  - `test_patch_engine.py`: Range offsets, bottom-up ordering, idempotency, overlap resolution, and large-file scaling (1,000 violations).
  - `test_metrics_consistency.py`: Counter equation invariants across all workflow operations.
  - `test_e2e_stress.py`: End-to-end full pipeline execution tests on real C files.
- **Frontend Build**: Verified production Vite build (`npm run build`).

---

## 20. Dependencies

- **Python (`requirements.txt`)**:
  - `fastapi>=0.100.0`: ASGI REST API framework.
  - `uvicorn>=0.22.0`: Asynchronous HTTP server.
  - `pycparser>=2.21`: C99 AST parser.
  - `reportlab>=4.0.0`: PDF generation library.
  - `pydantic>=2.0.0`: Data schema validation.
  - `requests>=2.31.0`: HTTP client library.
  - `mcp>=2.0.0`: Official Model Context Protocol SDK.
  - `pytest>=8.0.0`: Automated test runner.

---

## 21. Configuration Files

- `requirements.txt`: Python package dependencies manifest.
- `frontend/package.json`: Node.js frontend dependencies.
- `frontend/vite.config.ts`: Vite build bundler configuration.
- `frontend/tailwind.config.js`: Tailwind CSS styling configuration.

---

## 22. Build & Execution

### Launch Backend Server
```bash
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```

### Launch Frontend Workstation
```bash
cd frontend
npm run dev
```
Workstation UI will be live at `http://localhost:5173`.

---

## 23. Runtime Lifecycle

1. **Initialization**: Uvicorn starts FastAPI; `MCPClient` initializes connection to `OfficialMCPServer`.
2. **Analysis Request**: Developer uploads C code file. `CParserService` pre-processes code, builds AST, and executes `ALL_RULES`.
3. **Remediation Review**: Developer reviews side-by-side Monaco diff previews. Developer can click **Ask AI** to request TinyLlama analysis via MCP.
4. **Patch Execution**: Developer accepts fixes. `patch_engine` executes bottom-up range replacement pass.
5. **Artifact Export**: Developer downloads publication-grade PDF compliance report or corrected `.zip` archive.

---

## 24. Design Decisions & Rationale

1. **Why AST Parsing over Regex**: Regex cannot handle nested braces, comments, or C operator precedence. AST parsing guarantees zero false-positive syntax matches.
2. **Why Human-in-the-Loop over AI Auto-Fixing**: In ISO 26262 automotive and IEC 62304 medical software, unvalidated LLM modifications present unacceptable safety risks. Developers must retain full review authority.
3. **Why Official MCP Architecture**: Isolates the backend from AI model vendor lock-in, enabling plug-and-play AI model upgrades (TinyLlama, Llama 3, Qwen) over a standardized protocol.
4. **Why Bottom-Up Offset Patching**: Modifying source code top-down shifts byte indices of downstream lines. Descending offset replacements preserve line coordinates perfectly.

---

## 25. Appendix

- **MISRA C:2012 Standard**: Published by the Motor Industry Software Reliability Association.
- **Model Context Protocol**: Open standard developed by Anthropic.
- **ISO 26262 / DO-178C / IEC 62304**: Functional safety standard benchmarks.

---
*End of Complete Implementation Documentation.*
