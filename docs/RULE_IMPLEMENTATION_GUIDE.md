# MISRA C:2012 Static Analyzer — Rule Implementation Guide

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. Implemented Rule Matrix

Every supported rule is deterministically checked using AST `NodeVisitor` classes in `backend/rules/`:

| Rule | Title | Category | Severity | Detection Logic | Auto-Patch Strategy |
| :---: | :--- | :--- | :---: | :--- | :--- |
| **2.2** | No dead code / side-effect statement | Unused Code | Required | Finds unreachable statements after `return` or statements without side effects. | Deletes dead code / side-effect-free statement. |
| **2.7** | Unused function parameter | Unused Code | Advisory | Finds declared function parameters not referenced in body. | Inserts `(void)param;` at body start. |
| **7.1** | Octal constants prohibited | Literals | Required | Regex/AST search for octal integer literals (e.g. `077`). | Converts octal literal to decimal representation. |
| **8.4** | Missing prototype declaration | Declarations | Required | Finds non-static function definitions lacking prior prototype. | Prepends compatible prototype declaration. |
| **8.7** | Single-use global variable scope | Declarations | Advisory | Finds global variables referenced in only one function. | Prepends `static` keyword or moves variable scope. |
| **10.3**| Essential type cast / implicit conversion | Types | Required | Inspects return type vs returned expression essential types. | **Partial Auto-Patch**: Inserts explicit cast `(target_type)expr`. Semantic conversions requiring developer review are left for manual fix. |
| **12.1**| Operator precedence parentheses | Expressions | Advisory | Checks binary operations with mixed precedence lacking parentheses. | Wraps sub-expressions in explicit parentheses `((a * b) + c)`. |
| **14.4**| Non-Boolean controlling condition | Control Flow | Required | Checks `if` controlling expressions that evaluate to integer instead of Boolean. | Transforms `if (expr)` to `if ((expr) != 0)`. |
| **16.3**| Switch clause missing break | Control Flow | Required | Inspects non-empty switch cases lacking unconditional `break`. | Appends `break;` at clause termination. |
| **16.4**| Switch missing default clause | Control Flow | Required | Inspects `switch` statements lacking a `default:` label. | Appends `default:\n    break;` to switch body. |

---

## 2. Rule 10.3 Patch Policy Specification

**Rule 10.3 Policy:** **Partial Auto-Patch**.
- **Automated Fixes**: Safe cases (such as implicit conversions in return statements where an explicit target type cast is unambiguous) are fixed automatically by inserting `(target_type)expr`.
- **Manual Review Cases**: Semantic conversions involving numeric literal suffixing (e.g. `0` vs `0U`), implicit narrowing assignments, or typedef conversions that could alter program runtime behavior are intentionally left for manual developer review.

---

## 3. Patch Engine Architecture (`patch_engine.py`)

The patch engine executes structured range-based operations:
1. **Range Targeting**: Calculates exact `start_line`, `start_col`, `end_line`, `end_col`, `start_offset`, and `end_offset`.
2. **Operation Types**:
   - `REPLACE`: Replaces target range with modified code string.
   - `INSERT_BEFORE` / `INSERT_AFTER`: Inserts prototype declarations or `(void)param;` statements.
   - `DELETE`: Removes dead code statements.
3. **Bottom-Up Bulk Execution**: Multi-op bulk patch application sorts operations in descending byte offset order (`start_offset` descending) so applying earlier patches never invalidates offsets of subsequent patches.
4. **AST Validation**: Re-parses patched code with pycparser to ensure complete syntactic validity before committing.
