# MISRA AI Compliance Agent — Rule Implementation Guide

> **Verification Scope**: Validated for the current implemented rule set and tested against the documented scenarios.

---

## 1. MISRA C:2012 Rule Classification & Status Matrix

| Rule | MISRA Title | Category | Severity | Detection Engine | Remediation Mode | Rationale / Transformation | Status |
| :---: | :--- | :--- | :---: | :--- | :---: | :--- | :---: |
| **2.2** | No dead code | Unused Code | Required | `rule_2_2.py` (AST unreachable visitor) | **Automated** | Line-erase unreachable code following `return`/`break`/`goto` | **Fully Functional** |
| **2.7** | Unused parameter | Unused Code | Advisory | `rule_2_7.py` (AST symbol table visitor) | **Automated** | Inserts `(void)param;` at body start | **Fully Functional** |
| **7.1** | Octal constants prohibited | Literals | Required | `rule_7_1.py` (AST Constant visitor) | **Automated** | Converts octal literals (e.g. `077`) to decimal (`63`) | **Fully Functional** |
| **8.4** | Missing prototype | Declarations | Required | `rule_8_4.py` (AST FuncDef visitor) | **Automated** | Prepends forward declaration prototype | **Fully Functional** |
| **8.7** | Internal linkage | Declarations | Advisory | `rule_8_7.py` (AST FileScope visitor) | **Automated** | Prepends `static` keyword | **Fully Functional** |
| **10.3**| Implicit narrowing | Types | Required | `rule_10_3.py` (AST EssentialTypeVisitor) | **Automated** | Inserts explicit cast `(target_type)expr` | **Fully Functional** |
| **12.1**| Operator precedence | Expressions | Advisory | `rule_12_1.py` (AST PrecedenceVisitor) | **Automated** | Inserts explicit operator precedence parentheses `a + (b * c)` | **Fully Functional** |
| **14.4**| Non-boolean condition | Control Flow | Required | `rule_14_4.py` (AST ConditionVisitor) | **Automated** | AST controlling expression rewriter (`if (count != 0)`) | **Fully Functional** |
| **16.3**| Switch missing break | Control Flow | Required | `rule_16_3.py` (AST SwitchBreakVisitor) | **Automated** | Appends terminating `break;` to non-empty switch clauses | **Fully Functional** |
| **16.4**| Switch missing default | Control Flow | Required | `rule_16_4.py` (AST SwitchDefaultVisitor) | **Automated** | Appends `default:\n    break;` clause to switch statements | **Fully Functional** |

---

## 2. 100% Deterministic Auto-Patch Guarantee

All 10 implemented base rules are **100% Auto-Patchable** via AST-based range transformations:

1. **Zero Heuristics**: Every rule uses AST coordinate ranges and exact node properties.
2. **Coordinate-Bound Patch Previews**: Every violation produces a 17-field `PatchPreview` bound to its unique `stable_id`, line, and column coordinates.
3. **Idempotency & Syntax Integrity**: Applying patches twice produces identical code, and all modified source files are validated through `pycparser` before committing.
