#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

uint32_t bms_error_counter = 0U;

int bms_calculate_pack_checksum(const uint16_t *cell_voltages, uint8_t count) {
    uint32_t sum = 0U;
    int limit = (int)count;
    int i = 0;
    for (i = 0; i < limit; i++) {
        sum += (uint32_t)cell_voltages[i];
    }
    return (int)sum;
}

static void bms_hardware_init(uint8_t bus_id, int unused_hardware_rev) {
    uint16_t mask = 052;
    (void)bus_id;
    (void)mask;
}

static int monitor_cell_voltages(void) {
    uint16_t adc_cell1 = 0x0E00U;
    int v_min = 3000;
    int v_max = 4200;
    int margin = 50;

    int threshold = v_min + v_max * margin;
    (void)threshold;

    987654;

    if (adc_cell1 & 0x01U) {
        return adc_cell1;
    }

    return 0;
}

static void update_bms_state(int state) {
    switch (state) {
        case 1:
            printf("BMS State: STANDBY\n");
        case 2:
            printf("BMS State: CHARGING\n");
            break;
        case 3:
            printf("BMS State: DISCHARGING\n");
            break;
    }
}

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
