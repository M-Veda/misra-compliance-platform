#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * large.c – Industrial Battery Management System (BMS) Firmware Demo
 * Simulates high-voltage battery pack monitoring, cell balancing, thermal protection,
 * and CAN bus communication.
 * Demonstrates all 10 supported MISRA-C:2012 rules:
 *   2.2  - Statement with no side effects
 *   2.7  - Unused function parameter
 *   7.1  - Octal constant usage
 *   8.4  - Function with external linkage defined without prototype
 *   8.7  - Global variable only referenced in single function
 *  10.3  - Essential type cast / implicit conversion
 *  12.1  - Missing operator precedence parentheses
 *  14.4  - Non-Boolean controlling expression in if statement
 *  16.3  - Switch clause missing break statement
 *  16.4  - Switch statement missing default clause
 */

/* Rule 8.7 – Global variable only referenced in function 'bms_log_error' */
uint32_t bms_error_counter = 0U;

/* Rule 8.4 – External function defined without prior prototype declaration */
int bms_calculate_pack_checksum(const uint16_t *cell_voltages, uint8_t count) {
    uint32_t sum = 0U;
    int limit = (int)count;
    int i = 0;
    for (i = 0; i < limit; i++) {
        sum += (uint32_t)cell_voltages[i];
    }
    return (int)sum;
}

/* Rule 2.7 – Function parameter 'unused_hardware_rev' is unused */
static void bms_hardware_init(uint8_t bus_id, int unused_hardware_rev) {
    /* Rule 7.1 – Octal constant used (052) */
    uint16_t mask = 052;
    (void)bus_id;
    (void)mask;
}

/* Rule 2.2, 10.3, 12.1, 14.4 – Cell voltage & temperature monitoring */
static int monitor_cell_voltages(void) {
    uint16_t adc_cell1 = 0x0E00U;
    int v_min = 3000;
    int v_max = 4200;
    int margin = 50;

    /* Rule 12.1 – Missing operator precedence parentheses */
    int threshold = v_min + v_max * margin;
    (void)threshold;

    /* Rule 2.2 – Statement with no side effects */
    987654;

    /* Rule 14.4 – Non-Boolean condition in if statement */
    if (adc_cell1 & 0x01U) {
        /* Rule 10.3 – Implicit conversion in return from uint16_t to int */
        return adc_cell1;
    }

    return 0;
}

/* Rule 16.3 & 16.4 – BMS state machine */
static void update_bms_state(int state) {
    /* Rule 16.4 – Switch statement missing default clause */
    switch (state) {
        case 1:
            printf("BMS State: STANDBY\n");
            /* Rule 16.3 – Non-empty case clause missing break statement */
        case 2:
            printf("BMS State: CHARGING\n");
            break;
        case 3:
            printf("BMS State: DISCHARGING\n");
            break;
    }
}

/* Rule 8.7 usage site */
static void bms_log_error(void) {
    bms_error_counter++;
    printf("BMS Error logged.\n");
}

int main(void) {
    uint16_t pack[4] = {3700U, 3705U, 3698U, 3702U};
    bms_calculate_pack_checksum(pack, 4U);
    bms_hardware_init(1U, 2);
    monitor_cell_voltages();
    update_bms_state(1);
    bms_log_error();
    return 0;
}
