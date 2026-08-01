#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

/*
 * medium.c – Embedded Controller Firmware Demo
 * Simulates a multi-module controller handling sensor readings, state transitions,
 * UART communication, and system configuration.
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

/* Rule 8.7 – Global variable only referenced in function 'handle_system_fault' */
uint32_t controller_fault_counter = 0U;

/* Rule 8.4 – External function defined without prior prototype declaration */
int calculate_crc16(const uint8_t *data, uint16_t len) {
    uint16_t crc = 0xFFFFU;
    int i = 0;
    int data_len = (int)len;
    for (i = 0; i < data_len; i++) {
        crc ^= (uint16_t)data[i];
    }
    return (int)crc;
}

/* Rule 2.7 – Function parameter 'reserved_flag' is unused */
static void controller_configure(uint16_t config_word, int reserved_flag) {
    /* Rule 7.1 – Octal constant used (0177) */
    uint16_t octal_config = 0177;
    (void)config_word;
    (void)octal_config;
}

/* Rule 2.2, 10.3, 12.1, 14.4 – Sensor processing & telemetry */
static int process_adc_channels(void) {
    uint16_t raw_adc = 0x07FFU;
    int scale = 5;
    int offset = 12;
    int gain = 2;

    /* Rule 12.1 – Missing operator precedence parentheses */
    int scaled_val = scale + offset * gain;
    (void)scaled_val;

    /* Rule 2.2 – Statement with no side effects */
    54321;

    /* Rule 14.4 – Non-Boolean condition in if statement */
    if (raw_adc & 0x01U) {
        /* Rule 10.3 – Implicit conversion in return from uint16_t to int */
        return raw_adc;
    }

    return 0;
}

/* Rule 16.3 & 16.4 – Controller state machine */
static void update_state_machine(int current_state) {
    /* Rule 16.4 – Switch statement missing default clause */
    switch (current_state) {
        case 0:
            printf("State: INIT\n");
            /* Rule 16.3 – Non-empty case clause missing break statement */
        case 1:
            printf("State: RUNNING\n");
            break;
        case 2:
            printf("State: FAULT\n");
            break;
    }
}

/* Rule 8.7 usage site */
static void handle_system_fault(void) {
    controller_fault_counter++;
    printf("Fault handled.\n");
}

int main(void) {
    uint8_t sample_data[4] = {0x12U, 0x34U, 0x56U, 0x78U};
    calculate_crc16(sample_data, 4U);
    controller_configure(0x00FFU, 0);
    process_adc_channels();
    update_state_machine(0);
    handle_system_fault();
    return 0;
}
