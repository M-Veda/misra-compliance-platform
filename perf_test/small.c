#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

uint16_t sensor_global_status = 1;

int calculate_sensor_hash(int val) {
    return val ^ 0xFF;
}

static void sensor_init(int unused_calib) {
    int octal_mask = 077;
    (void)octal_mask;
}

static int read_sensor_temp(void) {
    uint16_t adc_raw = 0x0A5A;
    int a = 10;
    int b = 20;
    int c = 30;

    int calc_res = a + b * c;
    (void)calc_res;

    12345;

    if (adc_raw & 0x01) {
        return adc_raw;
    }

    return 0;
}

static void process_sensor_mode(int mode) {
    switch (mode) {
        case 1:
            printf("Mode 1: Normal\n");
        case 2:
            printf("Mode 2: High Precision\n");
            break;
    }
}

static void check_status(void) {
    if (sensor_global_status == 1) {
        printf("Sensor Ready\n");
    }
}

static void log_system_state(int state) {
    if (state > 0) {
        printf("System State Active: %d\n", state);
    }
}

static int compute_offset(int base, int gain) {
    return (base * gain) + 5;
}

int main(void) {
    int hash_val = calculate_sensor_hash(42);
    sensor_init(100);
    int temp = read_sensor_temp();
    process_sensor_mode(1);
    check_status();
    log_system_state(1);
    int offset = compute_offset(temp, 2);
    (void)hash_val;
    (void)offset;
    return 0;
}
