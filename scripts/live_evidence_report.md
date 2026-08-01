# Live Application Verification — Evidence Report

**Total checks**: 140 | **PASS**: 140 | **FAIL**: 0

**Test file**: `multi_rule_test.c`  
**Backend endpoint**: `http://127.0.0.1:8000/api`

---

## Summary Table

| Status | Check | Detail |
|---|---|---|
| PASS | At least 10 violations detected | 22 |
| PASS | Rule 2.2 violation detected |  |
| PASS | Rule 2.7 violation detected |  |
| PASS | Rule 7.1 violation detected |  |
| PASS | Rule 8.4 violation detected |  |
| PASS | Rule 8.7 violation detected |  |
| PASS | Rule 10.3 violation detected |  |
| PASS | Rule 12.1 violation detected |  |
| PASS | Rule 14.4 violation detected |  |
| PASS | Rule 16.3 violation detected |  |
| PASS | Rule 16.4 violation detected |  |
| PASS | Rule 2.2: patch_preview embedded in violation |  |
| PASS | Rule 2.2: 17 mandatory fields |  |
| PASS | Rule 2.2: original_source != replacement_source |  |
| PASS | Rule 2.2: unified_diff non-empty |  |
| PASS | Rule 2.2: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 2.2: can_autopatch=True |  |
| PASS | Rule 2.2: applies_cleanly=True |  |
| PASS | Rule 2.7: patch_preview embedded in violation |  |
| PASS | Rule 2.7: 17 mandatory fields |  |
| PASS | Rule 2.7: original_source != replacement_source |  |
| PASS | Rule 2.7: unified_diff non-empty |  |
| PASS | Rule 2.7: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 2.7: can_autopatch=True |  |
| PASS | Rule 2.7: applies_cleanly=True |  |
| PASS | Rule 7.1: patch_preview embedded in violation |  |
| PASS | Rule 7.1: 17 mandatory fields |  |
| PASS | Rule 7.1: original_source != replacement_source |  |
| PASS | Rule 7.1: unified_diff non-empty |  |
| PASS | Rule 7.1: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 7.1: can_autopatch=True |  |
| PASS | Rule 7.1: applies_cleanly=True |  |
| PASS | Rule 8.4: patch_preview embedded in violation |  |
| PASS | Rule 8.4: 17 mandatory fields |  |
| PASS | Rule 8.4: original_source != replacement_source |  |
| PASS | Rule 8.4: unified_diff non-empty |  |
| PASS | Rule 8.4: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 8.4: can_autopatch=True |  |
| PASS | Rule 8.4: applies_cleanly=True |  |
| PASS | Rule 8.7: patch_preview embedded in violation |  |
| PASS | Rule 8.7: 17 mandatory fields |  |
| PASS | Rule 8.7: original_source != replacement_source |  |
| PASS | Rule 8.7: unified_diff non-empty |  |
| PASS | Rule 8.7: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 8.7: can_autopatch=True |  |
| PASS | Rule 8.7: applies_cleanly=True |  |
| PASS | Rule 10.3: patch_preview embedded in violation |  |
| PASS | Rule 10.3: 17 mandatory fields |  |
| PASS | Rule 10.3: original_source != replacement_source |  |
| PASS | Rule 10.3: unified_diff non-empty |  |
| PASS | Rule 10.3: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 10.3: can_autopatch=True |  |
| PASS | Rule 10.3: applies_cleanly=True |  |
| PASS | Rule 12.1: patch_preview embedded in violation |  |
| PASS | Rule 12.1: 17 mandatory fields |  |
| PASS | Rule 12.1: original_source != replacement_source |  |
| PASS | Rule 12.1: unified_diff non-empty |  |
| PASS | Rule 12.1: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 12.1: can_autopatch=True |  |
| PASS | Rule 12.1: applies_cleanly=True |  |
| PASS | Rule 14.4: patch_preview embedded in violation |  |
| PASS | Rule 14.4: 17 mandatory fields |  |
| PASS | Rule 14.4: original_source != replacement_source |  |
| PASS | Rule 14.4: unified_diff non-empty |  |
| PASS | Rule 14.4: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 14.4: can_autopatch=True |  |
| PASS | Rule 14.4: applies_cleanly=True |  |
| PASS | Rule 14.4: explicit comparison in replacement | while (count != 0) {             /* Rule 14.4: count is int, not bool */ |
| PASS | Rule 16.3: patch_preview embedded in violation |  |
| PASS | Rule 16.3: 17 mandatory fields |  |
| PASS | Rule 16.3: original_source != replacement_source |  |
| PASS | Rule 16.3: unified_diff non-empty |  |
| PASS | Rule 16.3: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 16.3: can_autopatch=True |  |
| PASS | Rule 16.3: applies_cleanly=True |  |
| PASS | Rule 16.4: patch_preview embedded in violation |  |
| PASS | Rule 16.4: 17 mandatory fields |  |
| PASS | Rule 16.4: original_source != replacement_source |  |
| PASS | Rule 16.4: unified_diff non-empty |  |
| PASS | Rule 16.4: patch_type=AUTO_PATCH | AUTO_PATCH |
| PASS | Rule 16.4: can_autopatch=True |  |
| PASS | Rule 16.4: applies_cleanly=True |  |
| PASS | Rule 2.2: /preview-patch 200 | 200 |
| PASS | Rule 2.2: preview success=True |  |
| PASS | Rule 2.2: preview can_autopatch=True |  |
| PASS | Rule 2.2: patch_actually_changed=True |  |
| PASS | Rule 2.7: /preview-patch 200 | 200 |
| PASS | Rule 2.7: preview success=True |  |
| PASS | Rule 2.7: preview can_autopatch=True |  |
| PASS | Rule 2.7: patch_actually_changed=True |  |
| PASS | Rule 7.1: /preview-patch 200 | 200 |
| PASS | Rule 7.1: preview success=True |  |
| PASS | Rule 7.1: preview can_autopatch=True |  |
| PASS | Rule 7.1: patch_actually_changed=True |  |
| PASS | Rule 8.4: /preview-patch 200 | 200 |
| PASS | Rule 8.4: preview success=True |  |
| PASS | Rule 8.4: preview can_autopatch=True |  |
| PASS | Rule 8.4: patch_actually_changed=True |  |
| PASS | Rule 8.7: /preview-patch 200 | 200 |
| PASS | Rule 8.7: preview success=True |  |
| PASS | Rule 8.7: preview can_autopatch=True |  |
| PASS | Rule 8.7: patch_actually_changed=True |  |
| PASS | apply-patches 200 |  |
| PASS | patched modified_code non-empty |  |
| PASS | parse_valid=True |  |
| PASS | patched differs from original |  |
| PASS | re-analysis upload 200 |  |
| PASS | Rule 2.2: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 2.7: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 7.1: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 8.4: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 8.7: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 10.3: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 12.1: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 14.4: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 16.3: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 16.4: auto-patchable eliminated after bulk patch |  |
| PASS | Rule 2.2: idempotent at line 59 |  |
| PASS | Rule 2.7: idempotent at line 65 |  |
| PASS | Rule 7.1: idempotent at line 23 |  |
| PASS | Rule 7.1: idempotent at line 24 |  |
| PASS | Rule 8.4: idempotent at line 8 |  |
| PASS | Rule 8.4: idempotent at line 14 |  |
| PASS | Rule 8.4: idempotent at line 22 |  |
| PASS | Rule 8.4: idempotent at line 29 |  |
| PASS | Rule 8.4: idempotent at line 42 |  |
| PASS | Rule 8.4: idempotent at line 49 |  |
| PASS | Rule 8.4: idempotent at line 56 |  |
| PASS | Rule 8.4: idempotent at line 65 |  |
| PASS | Rule 8.4: idempotent at line 70 |  |
| PASS | Rule 8.7: idempotent at line 13 |  |
| PASS | Rule 10.3: idempotent at line 50 |  |
| PASS | Rule 10.3: idempotent at line 51 |  |
| PASS | Rule 12.1: idempotent at line 43 |  |
| PASS | Rule 12.1: idempotent at line 44 |  |
| PASS | Rule 14.4: idempotent at line 31 |  |
| PASS | Rule 14.4: idempotent at line 35 |  |
| PASS | Rule 16.3: idempotent at line 74 |  |
| PASS | Rule 16.4: idempotent at line 72 |  |
| PASS | generate-report 200 |  |

---

## Per-Rule Patch Preview Evidence

### Rule 2.2

**Violation** (line 59): Unreachable code: statement follows an unconditional control transfer (return/break/continue/goto).

**Code snippet**: `return 2;               /* Rule 2.2: unreachable */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `59` |
| original_end_line | `59` |

**Original Source**:

```c
        return 2;               /* Rule 2.2: unreachable */
```

**Replacement Source**:

```c
        /* Dead code removed (MISRA Rule 2.2) */
```

**Unified Diff**:

```diff
--- multi_rule_test.c:59
+++ Refactored Code
@@ -1 +1 @@
-        return 2;               /* Rule 2.2: unreachable */

+        /* Dead code removed (MISRA Rule 2.2) */

```

**Explanation**: MISRA Rule 2.2 — Unreachable or dead code detected on line 59. The automated patch erases the dead statement while maintaining indentation and line numbering.

---

### Rule 2.7

**Violation** (line 65): Parameter 'unused_param' is unused.

**Code snippet**: `int test_unused_param(int a, int unused_param) {`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `65` |
| original_end_line | `65` |

**Original Source**:

```c
int test_unused_param(int a, int unused_param) {
```

**Replacement Source**:

```c
int test_unused_param(int a, int unused_param) {
    (void)unused_param;
```

**Unified Diff**:

```diff
--- multi_rule_test.c:65
+++ Refactored Code
@@ -1 +1,2 @@
 int test_unused_param(int a, int unused_param) {

+    (void)unused_param;

```

**Explanation**: MISRA Rule 2.7 — Parameter 'unused_param' is declared but never read. The automated patch inserts '(void)unused_param;' at the top of the function body to explicitly suppress unused parameter warnings without changing runtime semantics.

---

### Rule 7.1

**Violation** (line 23): Octal constant '077' used. Octal constants and escape sequences shall not be used.

**Code snippet**: `int mask = 077;             /* Rule 7.1: octal literal 077 */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `23` |
| original_end_line | `23` |

**Original Source**:

```c
    int mask = 077;             /* Rule 7.1: octal literal 077 */
```

**Replacement Source**:

```c
    int mask = 63;             /* Rule 7.1: octal literal 63 */
```

**Unified Diff**:

```diff
--- multi_rule_test.c:23
+++ Refactored Code
@@ -1 +1 @@
-    int mask = 077;             /* Rule 7.1: octal literal 077 */

+    int mask = 63;             /* Rule 7.1: octal literal 63 */

```

**Explanation**: MISRA Rule 7.1 — Octal constant in expression 'int mask = 077;             /* Rule 7.1: octal literal 077 */' was converted to a compliant decimal representation to prevent misinterpretation.

---

### Rule 8.4

**Violation** (line 8): Function 'compute_sum' defined without a visible prototype.

**Code snippet**: `int compute_sum(int a, int b) {`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `8` |
| original_end_line | `8` |

**Original Source**:

```c
int compute_sum(int a, int b) {
```

**Replacement Source**:

```c
int compute_sum(int a, int b);
int compute_sum(int a, int b) {
```

**Unified Diff**:

```diff
--- multi_rule_test.c:8
+++ Refactored Code
@@ -1 +1,2 @@
+int compute_sum(int a, int b);

 int compute_sum(int a, int b) {

```

**Explanation**: MISRA Rule 8.4 — Function defined with external linkage but missing a visible prototype declaration. The automated patch prepends the prototype declaration 'int compute_sum(int a, int b);' immediately before the function definition.

---

### Rule 8.7

**Violation** (line 13): Global variable 'g_single_use_var' is only referenced in function 'helper_clamp' and should have block scope or internal linkage.

**Code snippet**: `int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `13` |
| original_end_line | `13` |

**Original Source**:

```c
int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */
```

**Replacement Source**:

```c
static int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */
```

**Unified Diff**:

```diff
--- multi_rule_test.c:13
+++ Refactored Code
@@ -1 +1 @@
-int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */

+static int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */

```

**Explanation**: MISRA Rule 8.7 — Global object is only referenced in a single function and should have internal linkage. The automated patch prepends 'static' to restrict its visibility to this translation unit.

---

### Rule 10.3

**Violation** (line 50): Implicit conversion from 'Signed(32bit)' to narrower/different 'Unsigned(32bit)'.

**Code snippet**: `unsigned int u = 10u;`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `50` |
| original_end_line | `50` |

**Original Source**:

```c
    unsigned int u = 10u;
```

**Replacement Source**:

```c
    unsigned int u = (unsigned int)10u;
```

**Unified Diff**:

```diff
--- multi_rule_test.c:50
+++ Refactored Code
@@ -1 +1 @@
-    unsigned int u = 10u;

+    unsigned int u = (unsigned int)10u;

```

**Explanation**: MISRA Rule 10.3 — Implicit essential type conversion. The patch adds an explicit cast to make the type conversion explicit and compliant.

---

### Rule 12.1

**Violation** (line 43): Operator precedence is not explicit for '+' and '*'.

**Code snippet**: `int x = a + b * c;          /* Rule 12.1: unclear precedence */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `43` |
| original_end_line | `43` |

**Original Source**:

```c
    int x = a + b * c;          /* Rule 12.1: unclear precedence */
```

**Replacement Source**:

```c
    int x = a + (b * c);          /* Rule 12.1: unclear precedence */
```

**Unified Diff**:

```diff
--- multi_rule_test.c:43
+++ Refactored Code
@@ -1 +1 @@
-    int x = a + b * c;          /* Rule 12.1: unclear precedence */

+    int x = a + (b * c);          /* Rule 12.1: unclear precedence */

```

**Explanation**: MISRA Rule 12.1 — Operator precedence is not explicit in expression. The patch adds explicit parentheses around sub-expressions to clarify evaluation order.

---

### Rule 14.4

**Violation** (line 31): Condition of 'while' statement is not essentially Boolean.

**Code snippet**: `while (count) {             /* Rule 14.4: count is int, not bool */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `31` |
| original_end_line | `31` |

**Original Source**:

```c
    while (count) {             /* Rule 14.4: count is int, not bool */
```

**Replacement Source**:

```c
    while (count != 0) {             /* Rule 14.4: count is int, not bool */
```

**Unified Diff**:

```diff
--- multi_rule_test.c:31
+++ Refactored Code
@@ -1 +1 @@
-    while (count) {             /* Rule 14.4: count is int, not bool */

+    while (count != 0) {             /* Rule 14.4: count is int, not bool */

```

**Explanation**: MISRA Rule 14.4 — Controlling expression of if/while/for statement is not essentially Boolean. The patch rewrites the controlling expression to an explicit Boolean comparison (e.g. `count != 0`), preserving exact statement formatting and surrounding code.

---

### Rule 16.3

**Violation** (line 74): Switch clause (case) is non-empty and does not end with an unconditional break statement.

**Code snippet**: `result = 10;        /* Rule 16.3: missing break */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `74` |
| original_end_line | `74` |

**Original Source**:

```c
            result = 10;        /* Rule 16.3: missing break */
```

**Replacement Source**:

```c
            result = 10;        /* Rule 16.3: missing break */
            break;
```

**Unified Diff**:

```diff
--- multi_rule_test.c:74
+++ Refactored Code
@@ -1 +1,2 @@
             result = 10;        /* Rule 16.3: missing break */

+            break;

```

**Explanation**: MISRA Rule 16.3 — Added an explicit `break;` statement at the end of the switch clause to prevent unintentional fall-through behavior.

---

### Rule 16.4

**Violation** (line 72): Switch statement does not contain a default clause.

**Code snippet**: `switch (mode) {             /* Rule 16.4: missing default clause */`

| Field | Value |
|---|---|
| patch_type | `AUTO_PATCH` |
| can_autopatch | `True` |
| applies_cleanly | `True` |
| confidence | `1.0` |
| original_start_line | `72` |
| original_end_line | `72` |

**Original Source**:

```c
    switch (mode) {             /* Rule 16.4: missing default clause */
```

**Replacement Source**:

```c
    switch (mode) {             /* Rule 16.4: missing default clause */
        default:
            break;
```

**Unified Diff**:

```diff
--- multi_rule_test.c:72
+++ Refactored Code
@@ -1 +1,3 @@
     switch (mode) {             /* Rule 16.4: missing default clause */

+        default:

+            break;

```

**Explanation**: MISRA Rule 16.4 — Appended a `default:` clause with `break;` to the switch statement to guarantee all unhandled conditions have explicit control flow.

---

## Bulk Accept & Re-analysis

- Ops applied: **22**
- Parse valid: **True**
- Patched source length: **3365 chars**

- Remaining violations after bulk patch: **0**
- Remaining rules: **[]**

## Report Generation

- PDF: ``
- Size: **0 bytes**