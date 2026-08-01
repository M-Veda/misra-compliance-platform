/* heavy_multi_occurrence_test.c — 10+ occurrences for all 10 MISRA C:2012 rules */
#include <stdio.h>

static int g_single_var_1 = 10;  /* Rule 8.7 occurrence 1 */
static int g_single_var_2 = 20;  /* Rule 8.7 occurrence 2 */
static int g_single_var_3 = 30;  /* Rule 8.7 occurrence 3 */
static int g_single_var_4 = 40;  /* Rule 8.7 occurrence 4 */
static int g_single_var_5 = 50;  /* Rule 8.7 occurrence 5 */
static int g_single_var_6 = 60;  /* Rule 8.7 occurrence 6 */
static int g_single_var_7 = 70;  /* Rule 8.7 occurrence 7 */
static int g_single_var_8 = 80;  /* Rule 8.7 occurrence 8 */
static int g_single_var_9 = 90;  /* Rule 8.7 occurrence 9 */
static int g_single_var_10 = 100;  /* Rule 8.7 occurrence 10 */

int ext_func_1(int val);
int ext_func_1(int val) { return val + g_single_var_1; }  /* Rule 8.4 occurrence 1 */
int ext_func_2(int val);
int ext_func_2(int val) { return val + g_single_var_2; }  /* Rule 8.4 occurrence 2 */
int ext_func_3(int val);
int ext_func_3(int val) { return val + g_single_var_3; }  /* Rule 8.4 occurrence 3 */
int ext_func_4(int val);
int ext_func_4(int val) { return val + g_single_var_4; }  /* Rule 8.4 occurrence 4 */
int ext_func_5(int val);
int ext_func_5(int val) { return val + g_single_var_5; }  /* Rule 8.4 occurrence 5 */
int ext_func_6(int val);
int ext_func_6(int val) { return val + g_single_var_6; }  /* Rule 8.4 occurrence 6 */
int ext_func_7(int val);
int ext_func_7(int val) { return val + g_single_var_7; }  /* Rule 8.4 occurrence 7 */
int ext_func_8(int val);
int ext_func_8(int val) { return val + g_single_var_8; }  /* Rule 8.4 occurrence 8 */
int ext_func_9(int val);
int ext_func_9(int val) { return val + g_single_var_9; }  /* Rule 8.4 occurrence 9 */
int ext_func_10(int val);
int ext_func_10(int val) { return val + g_single_var_10; }  /* Rule 8.4 occurrence 10 */

int func_unused_param_1(int active, int unused_arg_1);
int func_unused_param_1(int active, int unused_arg_1) {  /* Rule 2.7 occurrence 1 */
    (void)unused_arg_1;
    return active + 1;
}

int func_unused_param_2(int active, int unused_arg_2);
int func_unused_param_2(int active, int unused_arg_2) {  /* Rule 2.7 occurrence 2 */
    (void)unused_arg_2;
    return active + 2;
}

int func_unused_param_3(int active, int unused_arg_3);
int func_unused_param_3(int active, int unused_arg_3) {  /* Rule 2.7 occurrence 3 */
    (void)unused_arg_3;
    return active + 3;
}

int func_unused_param_4(int active, int unused_arg_4);
int func_unused_param_4(int active, int unused_arg_4) {  /* Rule 2.7 occurrence 4 */
    (void)unused_arg_4;
    return active + 4;
}

int func_unused_param_5(int active, int unused_arg_5);
int func_unused_param_5(int active, int unused_arg_5) {  /* Rule 2.7 occurrence 5 */
    (void)unused_arg_5;
    return active + 5;
}

int func_unused_param_6(int active, int unused_arg_6);
int func_unused_param_6(int active, int unused_arg_6) {  /* Rule 2.7 occurrence 6 */
    (void)unused_arg_6;
    return active + 6;
}

int func_unused_param_7(int active, int unused_arg_7);
int func_unused_param_7(int active, int unused_arg_7) {  /* Rule 2.7 occurrence 7 */
    (void)unused_arg_7;
    return active + 7;
}

int func_unused_param_8(int active, int unused_arg_8);
int func_unused_param_8(int active, int unused_arg_8) {  /* Rule 2.7 occurrence 8 */
    (void)unused_arg_8;
    return active + 8;
}

int func_unused_param_9(int active, int unused_arg_9);
int func_unused_param_9(int active, int unused_arg_9) {  /* Rule 2.7 occurrence 9 */
    (void)unused_arg_9;
    return active + 9;
}

int func_unused_param_10(int active, int unused_arg_10);
int func_unused_param_10(int active, int unused_arg_10) {  /* Rule 2.7 occurrence 10 */
    (void)unused_arg_10;
    return active + 10;
}

int func_dead_code_1(int x);
int func_dead_code_1(int x) {
    if (x > 1) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_2(int x);
int func_dead_code_2(int x) {
    if (x > 2) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_3(int x);
int func_dead_code_3(int x) {
    if (x > 3) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_4(int x);
int func_dead_code_4(int x) {
    if (x > 4) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_5(int x);
int func_dead_code_5(int x) {
    if (x > 5) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_6(int x);
int func_dead_code_6(int x) {
    if (x > 6) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_7(int x);
int func_dead_code_7(int x) {
    if (x > 7) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_8(int x);
int func_dead_code_8(int x) {
    if (x > 8) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_9(int x);
int func_dead_code_9(int x) {
    if (x > 9) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_dead_code_10(int x);
int func_dead_code_10(int x) {
    if (x > 10) {
        return 1;
        /* Dead code removed (MISRA Rule 2.2) */
    }
    return 0;
}

int func_octal_constants(void);
int func_octal_constants(void) {
    int total = 0;
    total += 15;  /* Rule 7.1 occurrence 1 */
    total += 23;  /* Rule 7.1 occurrence 2 */
    total += 31;  /* Rule 7.1 occurrence 3 */
    total += 39;  /* Rule 7.1 occurrence 4 */
    total += 47;  /* Rule 7.1 occurrence 5 */
    total += 55;  /* Rule 7.1 occurrence 6 */
    total += 63;  /* Rule 7.1 occurrence 7 */
    total += 79;  /* Rule 7.1 occurrence 8 */
    total += 87;  /* Rule 7.1 occurrence 9 */
    total += 95;  /* Rule 7.1 occurrence 10 */
    return total;
}

int func_implicit_narrowing(void);
int func_implicit_narrowing(void) {
    unsigned int u = (unsigned int)50u;
    int sum = 0;
    int s_1 = (int)u + 1; /* Rule 10.3 occurrence 1 */
    sum += s_1;
    int s_2 = (int)u + 2; /* Rule 10.3 occurrence 2 */
    sum += s_2;
    int s_3 = (int)u + 3; /* Rule 10.3 occurrence 3 */
    sum += s_3;
    int s_4 = (int)u + 4; /* Rule 10.3 occurrence 4 */
    sum += s_4;
    int s_5 = (int)u + 5; /* Rule 10.3 occurrence 5 */
    sum += s_5;
    int s_6 = (int)u + 6; /* Rule 10.3 occurrence 6 */
    sum += s_6;
    int s_7 = (int)u + 7; /* Rule 10.3 occurrence 7 */
    sum += s_7;
    int s_8 = (int)u + 8; /* Rule 10.3 occurrence 8 */
    sum += s_8;
    int s_9 = (int)u + 9; /* Rule 10.3 occurrence 9 */
    sum += s_9;
    int s_10 = (int)u + 10; /* Rule 10.3 occurrence 10 */
    sum += s_10;
    return sum;
}

int func_operator_precedence(int x, int y, int z);
int func_operator_precedence(int x, int y, int z) {
    int res = 0;
    res += x + (y * z) + 1;  /* Rule 12.1 occurrence 1 */
    res += x + (y * z) + 2;  /* Rule 12.1 occurrence 2 */
    res += x + (y * z) + 3;  /* Rule 12.1 occurrence 3 */
    res += x + (y * z) + 4;  /* Rule 12.1 occurrence 4 */
    res += x + (y * z) + 5;  /* Rule 12.1 occurrence 5 */
    res += x + (y * z) + 6;  /* Rule 12.1 occurrence 6 */
    res += x + (y * z) + 7;  /* Rule 12.1 occurrence 7 */
    res += x + (y * z) + 8;  /* Rule 12.1 occurrence 8 */
    res += x + (y * z) + 9;  /* Rule 12.1 occurrence 9 */
    res += x + (y * z) + 10;  /* Rule 12.1 occurrence 10 */
    return res;
}

int func_non_bool_conditions(int c);
int func_non_bool_conditions(int c) {
    int acc = 0;
    if ((c + 1) != 0) { acc += 1; }  /* Rule 14.4 occurrence 1 */
    if ((c + 2) != 0) { acc += 2; }  /* Rule 14.4 occurrence 2 */
    if ((c + 3) != 0) { acc += 3; }  /* Rule 14.4 occurrence 3 */
    if ((c + 4) != 0) { acc += 4; }  /* Rule 14.4 occurrence 4 */
    if ((c + 5) != 0) { acc += 5; }  /* Rule 14.4 occurrence 5 */
    if ((c + 6) != 0) { acc += 6; }  /* Rule 14.4 occurrence 6 */
    if ((c + 7) != 0) { acc += 7; }  /* Rule 14.4 occurrence 7 */
    if ((c + 8) != 0) { acc += 8; }  /* Rule 14.4 occurrence 8 */
    if ((c + 9) != 0) { acc += 9; }  /* Rule 14.4 occurrence 9 */
    if ((c + 10) != 0) { acc += 10; }  /* Rule 14.4 occurrence 10 */
    return acc;
}

int func_switch_rules(int mode);
int func_switch_rules(int mode) {
    int res = 0;
    switch (mode + 1) {  /* Rule 16.4 occurrence 1 */
        default:
            break;
        case 1:
            res += 1;  /* Rule 16.3 occurrence 1 */
            break;
        case 2:
            res += 1 * 2;
            break;
    }
    switch (mode + 2) {  /* Rule 16.4 occurrence 2 */
        default:
            break;
        case 1:
            res += 2;  /* Rule 16.3 occurrence 2 */
            break;
        case 2:
            res += 2 * 2;
            break;
    }
    switch (mode + 3) {  /* Rule 16.4 occurrence 3 */
        default:
            break;
        case 1:
            res += 3;  /* Rule 16.3 occurrence 3 */
            break;
        case 2:
            res += 3 * 2;
            break;
    }
    switch (mode + 4) {  /* Rule 16.4 occurrence 4 */
        default:
            break;
        case 1:
            res += 4;  /* Rule 16.3 occurrence 4 */
            break;
        case 2:
            res += 4 * 2;
            break;
    }
    switch (mode + 5) {  /* Rule 16.4 occurrence 5 */
        default:
            break;
        case 1:
            res += 5;  /* Rule 16.3 occurrence 5 */
            break;
        case 2:
            res += 5 * 2;
            break;
    }
    switch (mode + 6) {  /* Rule 16.4 occurrence 6 */
        default:
            break;
        case 1:
            res += 6;  /* Rule 16.3 occurrence 6 */
            break;
        case 2:
            res += 6 * 2;
            break;
    }
    switch (mode + 7) {  /* Rule 16.4 occurrence 7 */
        default:
            break;
        case 1:
            res += 7;  /* Rule 16.3 occurrence 7 */
            break;
        case 2:
            res += 7 * 2;
            break;
    }
    switch (mode + 8) {  /* Rule 16.4 occurrence 8 */
        default:
            break;
        case 1:
            res += 8;  /* Rule 16.3 occurrence 8 */
            break;
        case 2:
            res += 8 * 2;
            break;
    }
    switch (mode + 9) {  /* Rule 16.4 occurrence 9 */
        default:
            break;
        case 1:
            res += 9;  /* Rule 16.3 occurrence 9 */
            break;
        case 2:
            res += 9 * 2;
            break;
    }
    switch (mode + 10) {  /* Rule 16.4 occurrence 10 */
        default:
            break;
        case 1:
            res += 10;  /* Rule 16.3 occurrence 10 */
            break;
        case 2:
            res += 10 * 2;
            break;
    }
    return res;
}
