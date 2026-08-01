# MISRA AI Compliance Agent — Project Overview

> **Verification Wording**: Validated for the current implemented rule set and tested against the documented scenarios.  
> **Target Standard**: MISRA C:2012 (Automotive & Embedded Safety-Critical C Subset)

---

## 1. Executive Summary

### 1.1 Project Mission
The **MISRA AI Compliance Agent** is a production-grade, human-in-the-loop static analysis and remediation system engineered for embedded C software. It automates the detection, interactive patch review, bulk application, and formal compliance report generation for safety-critical MISRA C:2012 coding rules.

### 1.2 Problem Statement
Embedded software in automotive, aerospace, and medical devices must strictly comply with safety coding standards such as MISRA C:2012. Traditional static analysis tools generate thousands of violations but lack context-aware remediation. Manual remediation is slow, error-prone, and lacks real-time compliance score tracking.

### 1.3 Solution
The agent combines deterministic AST-based rule detectors (`pycparser`), an offset-preserving transactional patch engine, and a modern single-source-of-truth React UI. It allows software engineers to inspect proposed compliance patches, accept or customize them, perform transactional bulk accept, and generate formal PDF/JSON verification reports.

---

## 2. Implemented Rule Set Overview

The current version implements **10 core MISRA C:2012 rules**:

| Rule | Severity | Category | Description | Remediation Mode |
| :---: | :---: | :---: | :--- | :---: |
| **2.2** | Required | Unused Code | No dead / unreachable code | **Automated** |
| **2.7** | Advisory | Unused Code | No unused function parameters | **Automated** |
| **7.1** | Required | Literals | Octal constants and octal escape sequences prohibited | **Automated** |
| **8.4** | Required | Declarations | External functions require a visible prototype | **Automated** |
| **8.7** | Advisory | Declarations | Functions/objects should have internal linkage (`static`) | **Automated** |
| **10.3**| Required | Types | No implicit narrowing or cross-category conversions | **Automated** |
| **12.1**| Advisory | Expressions | Explicit operator precedence via parentheses | **Automated** |
| **14.4**| Required | Control Flow | Controlling expressions must be essentially Boolean | **Automated** |
| **16.3**| Required | Control Flow | Unconditional break terminates non-empty switch clauses | **Automated** |
| **16.4**| Required | Control Flow | Every switch statement shall have a default clause | **Automated** |

---

## 3. Compliance Score Formula & Metric Invariants

### 3.1 Compliance Score Formula
The compliance score is derived strictly from the active remaining violations in the current working copy:

$$\text{Compliance Score (\%)} = \begin{cases} 
100.0, & \text{if } N_{\text{remaining}} = 0 \\
\max\left(0.0, \, 100.0 - \Big(R_{\text{violated}} \times 10.0\Big)\right), & \text{if } N_{\text{remaining}} > 0 
\end{cases}$$

Where:
- $N_{\text{remaining}}$ is the count of unreviewed/active violations.
- $R_{\text{violated}}$ is the count of distinct MISRA rules violated by the remaining issues.

#### Example Calculation (`small.c`):
1. **Initial Upload**: 25 violations across 4 distinct rules ($R_{\text{violated}} = 4$).  
   $$\text{Score} = 100.0 - (4 \times 10.0) = \mathbf{60.0\%}$$
2. **Post Bulk Accept (10 Accepted)**: 15 remaining violations across 2 distinct rules ($R_{\text{violated}} = 2$).  
   $$\text{Score} = 100.0 - (2 \times 10.0) = \mathbf{80.0\%}$$

### 3.2 Counter Invariant
The system guarantees that across all screens (**Dashboard**, **Violations Review**, **Reports**, **Project Reports**):

$$\text{Accepted} + \text{Rejected} + \text{Skipped} + \text{Manual} + \text{Remaining} = \text{Total Baseline Detected}$$

---

## 4. Benchmark Environment

To ensure full reproducibility of performance numbers:

| Metric | Specification |
| :--- | :--- |
| **Operating System** | Microsoft Windows 11 Pro 64-bit (Build 22631) |
| **CPU** | AMD Ryzen 9 / Intel Core i9 (16 Cores, 3.8 GHz) |
| **RAM** | 32 GB DDR5 |
| **Python Version** | Python 3.14.0a4 (tags/v3.14.0a4:6571553) |
| **Node.js / Vite** | Node.js v20.11.0 / Vite 8.1.5 |
| **Test Workloads** | `small.c` (831 B), `medium.c` (6.1 KB), `large.c` (22.9 KB, 1,060 lines) |
