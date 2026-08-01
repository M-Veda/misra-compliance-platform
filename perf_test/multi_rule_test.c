/* multi_rule_test.c — Exercises all 10 deterministic MISRA C:2012 rules
 * Rules covered: 2.2, 2.7, 7.1, 8.4, 8.7, 10.3, 12.1, 14.4, 16.3, 16.4
 */

#include <stdio.h>

/* ── Rule 8.4: Missing prototype for external-linkage function ───────────── */
int compute_sum(int a, int b) {
    return a + b;
}

/* ── Rule 8.7: Function/Object could have internal linkage ──────────────── */
int g_single_use_var = 42;      /* Rule 8.7: global used only in helper_clamp */
int helper_clamp(int val, int lo, int hi) {
    val += g_single_use_var;
    if (val < lo) return lo;
    if (val > hi) return hi;
    return val;
}

/* ── Rule 7.1: Octal constants shall not be used ───────────────────────── */
int test_octal(int flag) {
    int mask = 077;             /* Rule 7.1: octal literal 077 */
    int val = 0123;             /* Rule 7.1: octal literal 0123 */
    return (flag > 0) ? (mask + val) : 0;
}

/* ── Rule 14.4: Non-boolean in if/while condition ────────────────────────── */
int test_bool_condition(int count) {
    int total = 0;
    while (count) {             /* Rule 14.4: count is int, not bool */
        total += count;
        count--;
    }
    if (total) {                /* Rule 14.4: total is int, not bool */
        return total;
    }
    return 0;
}

/* ── Rule 12.1: Operator precedence not clarified ───────────────────────── */
int test_precedence(int a, int b, int c) {
    int x = a + b * c;          /* Rule 12.1: unclear precedence */
    int y = a | b & c;          /* Rule 12.1: bitwise unclear precedence */
    return x + y;
}

/* ── Rule 10.3: Value assigned to wrong-category essential type ─────────── */
int test_essential_type(void) {
    unsigned int u = 10u;
    int s = u;                  /* Rule 10.3: unsigned -> signed */
    return s;
}

/* ── Rule 2.2: Dead code ─────────────────────────────────────────────────── */
int test_dead_code(int x) {
    if (x > 0) {
        return 1;
        return 2;               /* Rule 2.2: unreachable */
    }
    return 0;
}

/* ── Rule 2.7: Unused parameter ─────────────────────────────────────────── */
int test_unused_param(int a, int unused_param) {
    return a * 2;               /* Rule 2.7: unused_param never used */
}

/* ── Rule 16.3 & Rule 16.4: Switch case missing break & missing default ──── */
int test_switch_rules(int mode) {
    int result = 0;
    switch (mode) {             /* Rule 16.4: missing default clause */
        case 1:
            result = 10;        /* Rule 16.3: missing break */
        case 2:
            result = 20;
            break;
    }
    return result;
}

int main(void) {
    int a = compute_sum(3, 4);
    int b = helper_clamp(a, 0, 10);
    int c = test_octal(a);
    int d = test_bool_condition(b);
    int e = test_precedence(a, b, d);
    int f = test_essential_type();
    int g = test_dead_code(e);
    int h = test_unused_param(f, g);
    int i = test_switch_rules(c);

    printf("Results: %d\n", h + i);
    return 0;
}
