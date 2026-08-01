# MISRA‑C:2012 Static Analyzer Demo Suite (`perf_test`)

This directory contains three realistic embedded firmware C programs designed for demonstrating the full capabilities of the MISRA‑C:2012 static analysis engine.

## Demo Files Overview

| File Name | Embedded Domain | Line Count | Baseline Violations | Rules Detected | Re-Analysis Score |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`small.c`** | Temperature Sensor Firmware | **72 lines** | **10** | All 10 Rules | **100.0%** (0 remaining) |
| **`medium.c`** | Multi-Module Embedded Controller | **467 lines** | **39** | All 10 Rules | **60.0%** (10 manual remaining) |
| **`large.c`** | Industrial Battery Management System (BMS) | **1139 lines** | **32** | All 10 Rules | **70.0%** (6 manual remaining) |

---

## Demonstrated Rules Coverage

Every single one of the 10 supported MISRA‑C:2012 rules is triggered and demonstrated across all three demo files:

| Rule | MISRA Rule Description | Demonstrated | Auto-Patch Status | Demo Files |
| :--- | :--- | :---: | :---: | :--- |
| **2.2** | Statement with no side effects | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **2.7** | Unused function parameter | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **7.1** | Octal constant usage | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **8.4** | Function defined without visible prototype | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **8.7** | Global variable scoped to single function | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **10.3** | Essential type cast / implicit conversion | Yes | Partial Auto-Patch | `small.c`, `medium.c`, `large.c` |
| **12.1** | Missing operator precedence parentheses | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **14.4** | Non-Boolean condition in `if` statement | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **16.3** | Switch clause missing `break` statement | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |
| **16.4** | Switch statement missing `default` clause | Yes | Auto-patchable | `small.c`, `medium.c`, `large.c` |

> **Rule 10.3 Patch Policy:** Partial Auto-Patch. Safe cases are fixed automatically. Semantic conversions that could alter program behaviour are intentionally left for manual developer review.

---

## Explanation of Remaining Violations After Accept All

Upon executing **Accept All** (bulk auto-patching) and re-analyzing:

- **`small.c`**: Reaches **100.0% compliance** with **0 remaining violations**.
- **`medium.c`**: Re-analysis reports **10 remaining violations** across 4 rules (60.0% compliance).
- **`large.c`**: Re-analysis reports **6 remaining violations** across 3 rules (70.0% compliance).

### Root Cause Analysis of Remaining Violations

Rule 10.3 (Essential Type Conversion), Rule 12.1 (complex `||` expressions), Rule 7.1 (octal in nested context), and Rule 8.7 (global-scope restructuring) all have cases where auto-patching would alter program semantics. These are **intentionally left for manual developer review**, demonstrating the system's conservative and safe patching policy.

> **Scoring:** The compliance score deducts 10 points per unique rule still violated after patching. Files with more diverse remaining rule categories score lower, which is expected for larger, more complex embedded codebases.

## Presentation & Viva Guide

1. **Step 1: 2-Minute Overview (`small.c`)**
   - Upload `small.c` via Web UI or API.
   - Observe the 10 reported violations corresponding 1-to-1 to all 10 supported MISRA rules.
   - Click **Accept All** $\rightarrow$ Observe **100.0% compliance** and 0 remaining violations.

2. **Step 2: Realistic Firmware Inspection (`medium.c` & `large.c`)**
   - Upload `medium.c` or `large.c` to show multi-module controller and BMS firmware code.
   - Review patch previews, accept/reject decisions, and generate PDF compliance reports.
