#include <stdint.h>

volatile uint64_t dividend = 0xfedcba9876543210ULL;
volatile uint64_t divisor = 0x123456789ULL;

static uint64_t quotient(uint64_t a, uint64_t b) {
    return a / b;
}

int main(void) {
    uint64_t value = quotient(dividend, divisor);
    return (int)((uint16_t)value ^ (uint16_t)(value >> 16)
                 ^ (uint16_t)(value >> 32) ^ (uint16_t)(value >> 48));
}
