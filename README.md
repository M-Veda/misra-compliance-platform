# MISRA C:2012 Static Compliance & AI Automated Remediation Platform

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![Python Version](https://img.shields.io/badge/Python-3.10%2B-brightgreen.svg)](https://www.python.org/)
[![React Version](https://img.shields.io/badge/React-18.3-blue.svg)](https://react.dev/)
[![FastAPI Version](https://img.shields.io/badge/FastAPI-0.100%2B-009688.svg)](https://fastapi.tiangolo.com/)
[![MCP Standard](https://img.shields.io/badge/Protocol-Model%20Context%20Protocol%20v2.0-purple.svg)](https://modelcontextprotocol.io)
[![MISRA Standard](https://img.shields.io/badge/Standard-MISRA%20C%3A2012-red.svg)](https://www.misra.org.uk/)

> An enterprise-grade, human-in-the-loop static analysis and automated code remediation workstation for safety-critical C software engineering in automotive (**ISO 26262**), aerospace (**DO-178C**), and medical device (**IEC 62304**) domains. Powered by a deterministic C99 Abstract Syntax Tree (AST) visitor engine, bottom-up range patcher, interactive Monaco side-by-side diff editor, publication-grade ReportLab PDF report generator, centralized prompt management layer, and a live runtime **TinyLlama LLM** explanation engine operating over an **Official Model Context Protocol (MCP v2.0.0)** Server architecture.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Key Features](#2-key-features)
3. [Complete System Architecture](#3-complete-system-architecture)
4. [Complete Runtime Workflow](#4-complete-runtime-workflow)
5. [AI & Centralized Prompt Architecture](#5-ai--centralized-prompt-architecture)
6. [Folder Structure](#6-folder-structure)
7. [Technology Stack](#7-technology-stack)
8. [Installation & Prerequisites](#8-installation--prerequisites)
9. [Running the Project](#9-running-the-project)
10. [Visual Workstation Guide & Screenshots](#10-visual-workstation-guide--screenshots)
11. [Implemented MISRA C:2012 Rules](#11-implemented-misra-c2012-rules)
12. [API Endpoints Reference](#12-api-endpoints-reference)
13. [Current Implemented Scope](#13-current-implemented-scope)
14. [Current Scope Boundaries & Limitations](#14-current-scope-boundaries--limitations)
15. [Future Scope](#15-future-scope)
16. [Automated Testing Suite](#16-automated-testing-suite)
17. [License](#17-license)
18. [Acknowledgements](#18-acknowledgements)

---

## 1. Project Overview

The **MISRA C:2012 Compliance Platform** bridges deterministic static code analysis and modern AI assistance for embedded software developers. The workstation eliminates false syntax matches by executing rule checkers directly over C99 Abstract Syntax Trees (AST) constructed via `pycparser`.

### The Problem It Solves
1. **Safety Risks in ISO C**: Standard C allows undefined, unspecified, and implementation-defined behaviors (e.g., implicit type truncation, unparenthesized operator precedence, missing switch breaks, octal literal confusion) that can cause catastrophic runtime failures in automotive Engine Control Units (ECUs) or medical electronics.
2. **Review Bottlenecks**: Commercial analyzers produce thousands of static warning lines, forcing engineers to spend hundreds of manual hours locating files, reading rules, and drafting code edits.
3. **Risks of Unconstrained AI Auto-Fixing**: Raw LLMs can hallucinate non-existent standard library functions, alter pointer arithmetic, or introduce syntax errors in safety-critical code.

### The Solution: Human-in-the-Loop Remediation Workstation
- **Deterministic AST Analysis**: Exactly 10 MISRA rule violations are identified at the node level by C99 AST visitors.
- **Interactive Monaco Diff Previews**: Every proposed fix is rendered as a side-by-side code diff preview using Monaco Editor (the editor engine powering VS Code).
- **Developer Review Authority**: Engineers retain explicit control to **Accept**, **Reject**, **Skip**, or **Manually Refine** patches.
- **Bottom-Up Patch Engine**: Auto-fixes are applied using descending byte offset replacements to prevent coordinate desynchronization, followed by post-patch AST re-parsing syntax validation.
- **Decoupled Live MCP AI Integration**: AI explanations are generated strictly live at runtime by TinyLlama via an Official Model Context Protocol (MCP v2.0.0) Server (`mcp.server.Server`) and centralized prompt management layer (`mcp_server/prompt_manager.py`).

---

## 2. Key Features

### Core Functionality
- 🎯 **10 Deterministic AST Rule Visitors**: Node-level violation detection for Rules 2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, and 16.4.
- 📦 **Bottom-Up Bulk Auto-Patching**: Range replacement engine applying fixes in descending offset order with post-patch AST syntax verification.
- 📐 **Counter Equation Invariants**: Guarantees $\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Detected}$ holds mathematically true across all UI views and PDF reports.

### AI Capabilities & Prompt Architecture
- 🤖 **Official Model Context Protocol (MCP v2.0.0) Server**: Standalone MCP server (`mcp.server.Server`) registering 3 semantic tools (`generate_misra_explanation`, `answer_code_question`, `review_patch`).
- 📁 **Centralized Prompt Management Layer**: Prompt templates are stored as standards-based Markdown files (`mcp_server/prompts/`) and loaded dynamically via `PromptManager` (`mcp_server/prompt_manager.py`). Zero hardcoded prompt strings exist in business logic.
- 🧠 **Live Runtime TinyLlama Inference**: Generates structured explanations containing rule requirement, safety risk, AST analysis, recommended fix rationale, and impact metrics. Zero hardcoded explanation templates exist in the backend.
- 🛡️ **Offline Availability Safeguards**: Catches connection errors when Ollama is offline and returns explicit status banners without fabricating replacement content.

### Compliance Workflow & Review Engine
- ⚡ **Side-by-Side Monaco Diff Editor**: Visual diff workstation rendering original source snippet vs proposed remediation.
- 🛠️ **Pre-Filled Manual Fix Workstation**: Pre-loads the analyzer's best safe patch into an editable Monaco instance for custom developer overrides.
- 📊 **Executive Dashboard**: Compliance score percentage, SVG radial gauge, severity distribution cards, and rule breakdown counters.

### Reporting & Artifact Export
- 📄 **Publication-Grade PDF Reports**: Programmatic ReportLab PDF generation with clean string sanitization, score gauges, severity breakdown tables, and decision summaries. Streamed directly with immediate temp file cleanup.
- 📁 **Multi-File Folder ZIP Export**: Packages fixed C source files into a downloadable `.zip` archive for folder batch mode.

---

## 3. Complete System Architecture

```
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   React 18 Frontend UI                                 │
│                   (Analysis, Dashboard, Violations, Reports, Monaco Editor)            │
└───────────────────────────┬────────────────────────────────────────────────────────────┘
                                            │ REST API Calls (HTTP / JSON / Multipart)
                                            ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                    FastAPI Backend                                     │
│                                (backend/api/main.py)                                   │
└───────────────┬───────────────────────────┬───────────────────────────┬────────────────┘
                │                           │                           │
                ▼                           ▼                           ▼
┌───────────────────────────────┐ ┌───────────────────┐ ┌────────────────────────────────┐
│       C Parser Service        │ │   ReportLab PDF   │ │           MCP Client           │
│  (backend/services/parser.py) │ │     Generator     │ │    (backend/mcp/client.py)     │
│   Strips #include + Fake LIBC │ │ (backend/report/) │ └───────────────┬────────────────┘
└───────────────┬───────────────┘ └───────────────────┘                 │ MCP Tool Call
                │ FileAST                                               ▼
                ▼                                               ┌────────────────────────────────┐
┌───────────────────────────────┐                               │      Official MCP Server       │
│    MISRA AST Rule Engine      │                               │     (mcp_server/server.py)     │
│ (10 AST Visitor BaseRule Modules)                             └───────────────┬────────────────┘
└───────────────┬───────────────┘                                               │ Load Prompt Template
                │ Violations                                                    ▼
                ▼                                               ┌────────────────────────────────┐
┌───────────────────────────────┐                               │   Centralized Prompt Manager   │
│      Range Patch Engine       │                               │   (mcp_server/prompt_manager)  │
│(backend/services/patch_engine)│                               └───────────────┬────────────────┘
└───────────────────────────────┘                                               │ LLM Query
                                                                                ▼
                                                                ┌────────────────────────────────┐
                                                                │     Local Ollama (TinyLlama)   │
                                                                └────────────────────────────────┘
```

---

## 4. Complete Runtime Workflow

```
               [ User Uploads .c File or Folder Batch ]
                                  │
                                  ▼
               [ FastAPI Preprocesses & Builds C99 AST ]
                                  │
                                  ▼
               [ 10 AST MISRA Rule Visitors Execute ]
                                  │
                                  ▼
               [ Range Patch Engine Generates Previews ]
                                  │
                                  ▼
               [ Developer Views Monaco Diff Editor Workstation ]
                                  │
         ┌────────────────────────┼────────────────────────┐
         │                        │                        │
  Click Ask AI            Select Decision           Click Apply All
         │                        │                        │
         ▼                        ▼                        ▼
[ MCP Client Issues Tool ]  [ Accept/Reject/Skip ]  [ Bottom-Up Bulk Pass ]
         │                        │                        │
[ MCP Server Loads Prompt ] [ Metric Counter Update ] [ Post-Patch AST Check ]
         │                        │                        │
[ TinyLlama Model Infers ]        │                        │
         │                        │                        │
         └────────────────────────┼────────────────────────┘
                                  │
                                  ▼
               [ Download ReportLab PDF / Corrected ZIP ]
```

---

## 5. AI & Centralized Prompt Architecture

The platform implements a production-grade **Model Context Protocol (MCP v2.0.0)** server architecture featuring a centralized prompt management layer:

```
React UI ──► FastAPI Backend ──► MCP Client ──► Official MCP Server ──► PromptManager ──► AI Provider Layer ──► Ollama ──► TinyLlama
```

### Centralized Prompt Management Layer (`mcp_server/prompts/` & `mcp_server/prompt_manager.py`)
- **Standards-Based Markdown Templates**: Prompt definitions are maintained in clean Markdown files in `mcp_server/prompts/`:
  - `misra_explanation.md`: Structured MISRA violation analysis prompt template.
  - `code_qa.md`: Interactive developer C code question prompt template.
  - `patch_review.md`: C code patch review prompt template.
- **Dynamic Prompt Loading**: `PromptManager` (`mcp_server/prompt_manager.py`) loads templates dynamically and interpolates runtime context variables without embedding large prompt strings in Python source code.
- **Zero Hardcoded Explanation Content**: Every violation explanation is generated strictly live at runtime by TinyLlama inference. Zero hardcoded rule explanation dictionaries or fallback content exist.
- **Offline Resilience**: If Ollama or TinyLlama is offline, `OllamaProvider` catches the connection error and returns `is_available: False`. The UI displays a clear amber warning banner without fabricating fake text.

---

## 6. Folder Structure

```
MISRA_Project/
├── backend/                        # FastAPI Backend Application Root
│   ├── api/
│   │   └── main.py                 # FastAPI REST Routes & Controller (10 Endpoints)
│   ├── mcp/
│   │   └── client.py               # MCP Client (Issues Tool Calls to MCP Server)
│   ├── models/
│   │   └── violation.py            # Pydantic Schemas (RuleViolation, PatchPreview, etc.)
│   ├── report/
│   │   └── generator.py            # ReportLab PDF Compliance Report Generator
│   ├── rules/                      # Deterministic AST MISRA Rule Visitor Suite (10 Modules)
│   │   ├── base.py                 # Abstract BaseRule Visitor Interface
│   │   ├── rule_2_2.py ... rule_16_4.py (10 AST Rule Visitors)
│   │   └── __init__.py             # Exports ALL_RULES Visitor Array
│   ├── services/                   # Core Backend Domain Services (4 Services)
│   │   ├── llm.py                  # Backend LLM Orchestration Wrapper
│   │   ├── parser.py               # CParserPreProcessor & pycparser AST Service
│   │   ├── patch.py                # Single Patch Adapter Shim
│   │   └── patch_engine.py         # Range-Based Offset Patch & AST Validation Engine
│   └── tests/                      # Automated Backend Pytest Suite (6 Test Modules, 96 Tests)
├── mcp_server/                     # Standalone Model Context Protocol (MCP 2.0) Server
│   ├── prompts/                    # Centralized Markdown Prompt Templates
│   │   ├── code_qa.md              # Code QA Prompt Template
│   │   ├── misra_explanation.md    # MISRA Explanation Prompt Template
│   │   └── patch_review.md         # Patch Review Prompt Template
│   ├── ai_provider.py              # Pluggable AI Capabilities Layer (Ollama / TinyLlama)
│   ├── prompt_manager.py           # Centralized Prompt Management Engine
│   ├── prompts.py                  # Prompt Facade Wrapper Module
│   └── server.py                   # Official MCP Server (mcp.server.Server, 3 MCP Tools)
├── frontend/                       # React 18 + TypeScript Web Application Root
│   ├── src/
│   │   ├── App.tsx                 # Application Shell & Tab Navigation
│   │   ├── main.tsx                # React DOM Mount Entrypoint
│   │   ├── components/             # UI Components & Pages (6 Component Modules)
│   │   ├── context/
│   │   │   └── AppContext.tsx      # Global State Provider & Counter Metrics Engine
│   │   └── types/
│   │       └── index.ts            # Shared TypeScript Domain Type Definitions
│   ├── package.json                # Frontend Node Dependencies Manifest
│   └── vite.config.ts              # Vite Bundler Configuration
├── perf_test/                      # Performance Benchmarking Fixtures
├── scripts/                        # Benchmark & Validation Scripts
├── requirements.txt                # Python Backend Dependencies Manifest
├── README.md                       # Official GitHub Project Homepage
└── PROJECT_COMPLETE_IMPLEMENTATION_DOCUMENTATION.md # Single Source of Truth Technical Manual
```

---

## 7. Technology Stack

| Layer | Technology | Version | Purpose |
| :--- | :--- | :---: | :--- |
| **Frontend UI** | React | `18.3.1` | Component-driven user interface |
| **Language** | TypeScript | `5.5.3` | Type-safe frontend domain modeling |
| **Code Editor** | Monaco Editor | `0.46.0` | Interactive side-by-side code diff editing |
| **Styling** | Tailwind CSS | `3.4.1` | Responsive dark-mode styling & glassmorphism UI |
| **Backend Framework**| FastAPI | `0.100+` | High-performance asynchronous REST API controller |
| **ASGI Server** | Uvicorn | `0.22+` | Asynchronous server gateway interface |
| **C AST Parser** | pycparser | `2.21+` | Pure Python C99 AST parser & preprocessor |
| **AI Protocol** | MCP SDK (`mcp`) | `2.0.0` | Standard Model Context Protocol Client/Server SDK |
| **Prompt Layer** | Markdown Templates | Custom | Centralized standards-based prompt management layer |
| **Local Model** | TinyLlama (via Ollama)| `1.1B` | Live runtime AI violation explanation & QA engine |
| **PDF Generator** | ReportLab | `4.0+` | Programmatic PDF compliance report rendering |
| **Testing** | Pytest | `8.0+` | Automated backend unit & integration testing |

---

## 8. Installation & Prerequisites

### Required Environment
- **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14
- **Node.js**: 18.0 or higher
- **npm**: 9.0 or higher
- **Ollama** *(Required for live AI explanations)*: Download from [ollama.ai](https://ollama.ai)

### Step 1: Clone Repository & Install Python Dependencies
```bash
git clone https://github.com/M-Veda/misra-compliance-platform.git
cd misra-compliance-platform

# Install Python backend & MCP dependencies
pip install -r requirements.txt
```

### Step 2: Install Node.js Frontend Dependencies
```bash
cd frontend
npm install
cd ..
```

### Step 3: Pull TinyLlama AI Model
```bash
# Pull TinyLlama model via Ollama
ollama pull tinyllama
```

---

## 9. Running the Project

### 1. Start Ollama Model Service
```bash
ollama serve
```

### 2. Launch FastAPI Backend Server
```bash
# From workspace root
python -m uvicorn backend.api.main:app --host 127.0.0.1 --port 8000 --reload
```
*Backend API live at `http://127.0.0.1:8000`.*

### 3. Launch React Frontend Workstation
```bash
# From workspace root
cd frontend
npm run dev
```
*Frontend Workstation live at `http://localhost:5173`.*

---

## 10. Visual Workstation Guide & Screenshots

The platform features a modern workstation layout optimized for developer review:

### 1. Dashboard Page
Visualizes compliance score percentage, radial score gauge, severity distribution cards (Mandatory, Required, Advisory), project overview, and metric counter totals ($\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Detected}$).

### 2. Violations Workstation & Monaco Diff Viewer
Left-hand violation tree displaying detected MISRA rule violations categorized by file. Selecting a violation opens the interactive Monaco side-by-side diff editor showing original C code vs proposed remediation.

### 3. Ask AI Modal (Live TinyLlama Inference)
Clicking **Ask AI** invokes TinyLlama over official MCP (using templates loaded via `PromptManager`) to return structured analysis covering *What AI Found*, *Why It Matters*, *MISRA Requirement*, *AI AST Analysis*, *Recommended Fix Rationale*, and *Impact Analysis Grid*.

### 4. Executive PDF Compliance Report
Generates publication-grade PDF compliance reports containing executive gauges, severity tables, decision breakdown metrics, and sanitized violation logs.

---

## 11. Implemented MISRA C:2012 Rules

| Rule | Category | Severity | MISRA C:2012 Official Requirement | Automated Remediation Strategy |
| :---: | :--- | :---: | :--- | :--- |
| **2.2** | Unused Code | Required | There shall be no dead code | Replaces side-effect-free statement with `/* Dead code removed */` comment |
| **2.7** | Unused Code | Advisory | Unused parameters shall be eliminated | Inserts `(void)param;` cast at the top of function body |
| **7.1** | Literals | Required | Octal constants shall not be used | Converts octal literal (e.g. `052`) to decimal integer (`42`) |
| **8.4** | Declarations | Required | Compatible prototype declaration required | Prepends compatible prototype declaration above function definition |
| **8.7** | Declarations | Advisory | Objects should have internal linkage where possible | Prepends `static` keyword to single-use global declarations |
| **10.3**| Types | Required | Essential type cast prohibited | Inserts explicit type cast `(target_type)(expr)` |
| **12.1**| Expressions | Advisory | Precedence parentheses required | Wraps sub-expression in explicit parentheses `((a * b) + c)` |
| **14.4**| Control Flow | Required | Controlling expression essentially Boolean | Transforms integer condition `if (expr)` to `if ((expr) != 0)` |
| **16.3**| Control Flow | Required | Switch clause missing break statement | Appends `break;` statement at end of case body |
| **16.4**| Control Flow | Required | Switch statement missing default clause | Appends `default:\n    break;` clause to switch body |

---

## 12. API Endpoints Reference

| Endpoint | HTTP Method | Input Payload | Description |
| :--- | :---: | :--- | :--- |
| `/api/rules` | `GET` | None | Returns metadata array for all 10 supported MISRA rules |
| `/api/upload` | `POST` | Multipart `UploadFile` | Preprocesses C file, parses AST, runs rules, returns violations |
| `/api/explain` | `POST` | `ExplainRequest` | Delegates live TinyLlama explanation request via MCP Client |
| `/api/preview-patch` | `POST` | `PatchRequest` | Previews single patch decision (Accept/Reject/Skip/Manual) |
| `/api/apply-patches` | `POST` | `BulkPatchRequest` | Executes bottom-up bulk patch pass with AST syntax verification |
| `/api/chat` | `POST` | `ChatRequest` | Routes interactive developer questions to TinyLlama via MCP Client |
| `/api/generate-report` | `POST` | `ReportRequest` | Generates ReportLab PDF compliance report in OS temp storage |
| `/api/download-pdf/{filename}` | `GET` | Path Parameter | Streams PDF compliance report and auto-deletes temp file |
| `/api/download-zip` | `POST` | `DownloadZipRequest` | Packages corrected C files into a ZIP archive for folder mode |
| `/api/generate-project-report` | `POST` | `ReportRequest` | Generates comprehensive project PDF report |

---

## 13. Current Implemented Scope

- **Deterministic AST Engine**: 10 AST MISRA visitors producing location-independent stable SHA-256 violation IDs.
- **Range Patch Generator**: 17-field `PatchPreview` payloads with descending offset bottom-up patching.
- **MCP AI & Prompt Architecture**: 100% MCP v2.0.0 SDK server (`mcp_server/server.py`), client (`backend/mcp/client.py`), and centralized prompt manager (`mcp_server/prompt_manager.py`).
- **Reporting**: Programmatic ReportLab PDF generation with clean string sanitization.

---

## 14. Current Scope Boundaries & Limitations

1. **Preprocessor Macro Expansion**: Complex `#define` macros are stripped during preprocessing to allow `pycparser` C99 AST construction.
2. **Single Translation Unit Symbol Scope**: Rules 8.4 and 8.7 evaluate symbols at single file scope; multi-file project mode processes files sequentially.

---

## 15. Future Scope

- 🚀 **Clang AST Integration**: Support C11/C17 standard features and full preprocessor macro expansion using Clang AST bindings.
- 🛡️ **Expanded Rule Coverage**: Detectors for MISRA C:2012 Rules 9.1, 15.5, 17.7, and 21.1.
- 🔄 **CI/CD Pipeline Integration**: Docker container for GitHub Actions and GitLab CI automated pull-request checks.

---

## 16. Automated Testing Suite

The project includes an automated testing suite (`pytest backend/tests/`):
- **96 Unit & Integration Tests Passing**:
  - AST Rule Visitors (`test_rules.py`)
  - Patch Engine & Idempotency (`test_patch_engine.py`)
  - Counter Equation Invariants (`test_metrics_consistency.py`)
  - Bulk Remediation Regression (`test_bulk_accept_regression.py`)
  - End-to-End Pipeline Stress (`test_e2e_stress.py`)

---

## 17. License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.

---

## 18. Acknowledgements

- **MISRA C Standard**: Guidelines developed by the Motor Industry Software Reliability Association.
- **Model Context Protocol (MCP)**: Open standard developed by Anthropic.
- **pycparser**: Developed by Eli Bendersky.
- **Monaco Editor**: Developed by Microsoft.
- **ReportLab**: Developed by ReportLab Inc.
