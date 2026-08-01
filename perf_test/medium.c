#include <stdio.h>
#include <stdint.h>
#include <stdlib.h>
#include <string.h>

uint32_t controller_fault_counter = 0U;

int calculate_crc16(const uint8_t *data, uint16_t len) {
    uint16_t crc = 0xFFFFU;
    int i = 0;
    int data_len = (int)len;
    for (i = 0; i < data_len; i++) {
        crc ^= (uint16_t)data[i];
    }
    return (int)crc;
}

static void controller_configure(uint16_t config_word, int reserved_flag) {
    uint16_t octal_config = 0177;
    (void)config_word;
    (void)octal_config;
}

static int process_adc_channels(void) {
    uint16_t raw_adc = 0x07FFU;
    int scale = 5;
    int offset = 12;
    int gain = 2;

    int scaled_val = scale + offset * gain;
    (void)scaled_val;

    54321;

    if (raw_adc & 0x01U) {
        return raw_adc;
    }

    return 0;
}

static void update_state_machine(int current_state) {
    switch (current_state) {
        case 0:
            printf("State: INIT\n");
        case 1:
            printf("State: RUNNING\n");
            break;
        case 2:
            printf("State: FAULT\n");
            break;
    }
}

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
