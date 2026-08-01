# MISRA AI Compliance Agent — Project Structure

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. Directory Tree Overview

```
MISRA_Project/
├── backend/                        # FastAPI application, pycparser AST detectors & patch engine
│   ├── agent/                      # MCP server interface
│   │   └── mcp_server.py
│   ├── api/                        # FastAPI main application endpoints
│   │   └── main.py
│   ├── generated_reports/          # Target folder for output PDF/ZIP files
│   ├── models/                     # Violation, Patch, AnalysisResult models
│   │   └── violation.py
│   ├── report/                     # ReportLab PDF & JSON report engine
│   │   └── generator.py
│   ├── rules/                      # 10 MISRA C:2012 AST rule visitors
│   │   ├── __init__.py
│   │   ├── base.py
│   │   ├── rule_2_2.py
│   │   ├── rule_2_7.py
│   │   ├── rule_8_4.py
│   │   ├── rule_8_7.py
│   │   ├── rule_9_1.py
│   │   ├── rule_10_3.py
│   │   ├── rule_12_1.py
│   │   ├── rule_14_4.py
│   │   ├── rule_15_5.py
│   │   └── rule_17_7.py
│   ├── services/                   # Parser, Patch Engine, LLM services
│   │   ├── llm.py
│   │   ├── parser.py
│   │   ├── patch.py
│   │   └── patch_engine.py
│   └── tests/                      # Pytest unit and integration test suites
│       ├── test_e2e_stress.py
│       ├── test_patch_engine.py
│       ├── test_rules.py
│       └── validate_750_file.py
├── frontend/                       # React 18 SPA, Vite, TypeScript, Monaco Editor
│   ├── src/
│   │   ├── components/
│   │   │   ├── Analysis.tsx
│   │   │   ├── BulkActionModal.tsx
│   │   │   ├── Dashboard.tsx
│   │   │   ├── GeneratedCode.tsx
│   │   │   ├── Reports.tsx
│   │   │   ├── Settings.tsx
│   │   │   └── Violations.tsx
│   │   ├── context/
│   │   │   └── AppContext.tsx
│   │   ├── types/
│   │   │   └── index.ts
│   │   ├── App.tsx
│   │   ├── index.css
│   │   └── main.tsx
│   ├── index.html
│   ├── package.json
│   ├── tsconfig.json
│   └── vite.config.ts
├── perf_test/                      # Benchmark test C source files
│   ├── large.c
│   ├── medium.c
│   ├── multi_rule_test.c
│   ├── sample_test.c
│   └── small.c
├── docs/                           # Consolidated Documentation Suite (15 Markdown Files)
│   ├── API_DOCUMENTATION.md
│   ├── BACKEND_DOCUMENTATION.md
│   ├── CLEANUP_REPORT.md
│   ├── FEATURE_STATUS.md
│   ├── FILE_REFERENCE.md
│   ├── FINAL_PRODUCTION_VERIFICATION_REPORT.md
│   ├── FRONTEND_DOCUMENTATION.md
│   ├── LIMITATIONS_AND_FUTURE_WORK.md
│   ├── MODULE_REFERENCE.md
│   ├── PROJECT_HANDOVER.md
│   ├── PROJECT_OVERVIEW.md
│   ├── PROJECT_STRUCTURE.md
│   ├── RULE_IMPLEMENTATION_GUIDE.md
│   ├── SYSTEM_ARCHITECTURE.md
│   └── WORKFLOW_DOCUMENTATION.md
├── scripts/                        # Developer test & evidence collection utilities
│   ├── api_integration_test.py
│   ├── benchmark_performance.py
│   ├── generate_comprehensive_evidence.py
│   ├── generate_example_reports.py
│   └── run_full_validation_suite.py
├── .gitignore                      # Git ignore configuration
├── LICENSE                         # MIT License
├── README.md                       # Main project README
└── requirements.txt                # Python backend dependencies
```
