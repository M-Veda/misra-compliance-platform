#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * small.c – Embedded Temperature Sensor Firmware Demo
 * Demonstrates all 10 supported MISRA-C:2012 rules:
 *   2.2  - Statement with no side effects
 *   2.7  - Unused function parameter
 *   7.1  - Octal constant usage
 *   8.4  - Function with external linkage defined without prototype
 *   8.7  - Global variable only used in one function
 *  10.3  - Essential type cast / implicit conversion
 *  12.1  - Missing operator precedence parentheses
 *  14.4  - Non-Boolean controlling expression in if statement
 *  16.3  - Switch clause missing break statement
 *  16.4  - Switch statement missing default clause
 */

/* Rule 8.7 – Global variable only referenced in one function */
uint16_t sensor_global_status = 1;

/* Rule 8.4 – External function defined without a visible prototype */
int calculate_sensor_hash(int val) {
    return val ^ 0xFF;
}

/* Rule 2.7 – Unused function parameter 'unused_calib' */
static void sensor_init(int unused_calib) {
    /* Rule 7.1 – Octal constant used (077) */
    int octal_mask = 077;
    (void)octal_mask;
}

/* Rule 2.2, 10.3, 12.1, 14.4 – Core sensor reading function */
static int read_sensor_temp(void) {
    uint16_t adc_raw = 0x0A5A;
    int a = 10;
    int b = 20;
    int c = 30;

    /* Rule 12.1 – Missing parentheses on operator precedence */
    int calc_res = a + b * c;
    (void)calc_res;

    /* Rule 2.2 – Statement with no side effects */
    12345;

    /* Rule 14.4 – Non-Boolean condition in if statement */
    if (adc_raw & 0x01) {
        /* Rule 10.3 – Implicit conversion in return from uint16_t to int */
        return adc_raw;
    }

    return 0;
}

/* Rule 16.3 & 16.4 – Switch statement control flow */
static void process_sensor_mode(int mode) {
    /* Rule 16.4 – Switch statement missing default clause */
    switch (mode) {
        case 1:
            printf("Mode 1: Normal\n");
            /* Rule 16.3 – Non-empty case clause missing break */
        case 2:
            printf("Mode 2: High Precision\n");
            break;
    }
}

/* Rule 8.7 usage check */
static void check_status(void) {
    if (sensor_global_status == 1) {
        printf("Sensor Ready\n");
    }
}

int main(void) {
    calculate_sensor_hash(42);
    sensor_init(100);
    read_sensor_temp();
    process_sensor_mode(1);
    check_status();
    return 0;
}
