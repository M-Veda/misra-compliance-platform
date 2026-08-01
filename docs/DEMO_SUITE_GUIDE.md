# MISRA C:2012 Static Analyzer — Demo Suite Guide (`perf_test`)

> **Date**: August 1, 2026  
> **Status**: Release Baseline 1.0

---

## 1. Overview of `perf_test/` Files

The `perf_test/` folder contains a professional, realistic embedded C firmware demonstration suite:

```
perf_test/
├── README.md   (60 lines)
├── small.c     (72 lines)
├── medium.c    (467 lines)
└── large.c     (1139 lines)
```

| File | Domain | Lines | Baseline Violations | Detected Rules | Re-Analysis Score |
| :--- | :--- | :---: | :---: | :---: | :---: |
| **`small.c`** | Temperature Sensor Firmware | **72 lines** | **10** | All 10 Rules | **100.0%** (0 remaining) |
| **`medium.c`** | Multi-Module Controller Firmware | **467 lines** | **39** | All 10 Rules | **60.0%** (10 manual remaining) |
| **`large.c`** | Battery Management System (BMS) | **1139 lines** | **32** | All 10 Rules | **70.0%** (6 manual remaining) |

---

## 2. Presentation Walkthrough Order

1. **Step 1: Classroom / Viva 2-Minute Demo (`small.c`)**
   - Upload `small.c` via Web UI or API.
   - Show the 10 detected violations mapping 1-to-1 to all 10 supported MISRA rules (`2.2`, `2.7`, `7.1`, `8.4`, `8.7`, `10.3`, `12.1`, `14.4`, `16.3`, `16.4`).
   - Click **Accept All** $\rightarrow$ Show **100.0% compliance** and 0 remaining violations.

2. **Step 2: Pre-filled Manual Fix Demo (`medium.c` / `large.c`)**
   - Upload `medium.c` or `large.c`.
   - Select a violation and click **Manual Fix**.
   - Show the pre-filled code editor pre-populated with the analyzer's best safe suggestion.
   - Refine code formatting or parentheses and click **Confirm Manual Fix**.

3. **Step 3: Executive PDF Report Download**
   - Navigate to **Compliance Reports**.
   - Download the generated PDF compliance report (`MISRA_Report_small_c.pdf` or `MISRA_Project_Report_perf_test.pdf`).
