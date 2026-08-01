# MISRA‑C:2012 Static Analyzer Demo Suite (`perf_test`)

This directory contains three realistic embedded firmware C programs designed for demonstrating the full capabilities of the MISRA‑C:2012 static analysis engine.

## Demo Files Overview

| File Name | Embedded Domain | Line Count | Baseline Violations | Rules Detected | Re-Analysis Score |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`small.c`** | Temperature Sensor Firmware | **86 lines** | **10** | All 10 Rules | **100.0%** (0 remaining) |
| **`medium.c`** | Multi-Module Embedded Controller | **98 lines** | **15** | All 10 Rules | **70.0%** (3 manual remaining) |
| **`large.c`** | Industrial Battery Management System (BMS) | **98 lines** | **15** | All 10 Rules | **70.0%** (3 manual remaining) |

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
- **`medium.c` & `large.c`**: Re-analysis reports **3 remaining Rule 10.3 violations** (70.0% compliance).

### Root Cause Analysis of Remaining Rule 10.3 Violations:
1. **Rule ID:** `Rule 10.3` (Essential Type Conversion).
2. **Why They Remain:** When passing integer literals (e.g. `0` or numeric constants) to unsigned integer parameters or expressions without explicit `U` suffixes, C implicitly promotes the signed integer literal type to unsigned types.
3. **Classification:** **Intentionally Manual Refactoring Requirement**. Partial Auto-Patch: Safe cases are fixed automatically. Semantic conversions that could alter program behaviour are intentionally left for manual developer review.

---

## Presentation & Viva Guide

1. **Step 1: 2-Minute Overview (`small.c`)**
   - Upload `small.c` via Web UI or API.
   - Observe the 10 reported violations corresponding 1-to-1 to all 10 supported MISRA rules.
   - Click **Accept All** $\rightarrow$ Observe **100.0% compliance** and 0 remaining violations.

2. **Step 2: Realistic Firmware Inspection (`medium.c` & `large.c`)**
   - Upload `medium.c` or `large.c` to show multi-module controller and BMS firmware code.
   - Review patch previews, accept/reject decisions, and generate PDF compliance reports.
