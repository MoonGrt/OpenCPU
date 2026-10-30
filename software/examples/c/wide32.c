#include <stdint.h>

volatile uint32_t left = 0xf1234567UL;
volatile uint32_t right = 0x101UL;

static uint32_t product(uint32_t a, uint32_t b) {
    return a * b;
}

int main(void) {
    uint32_t value = product(left, right);
    return (int)((uint16_t)value ^ (uint16_t)(value >> 16));
}
