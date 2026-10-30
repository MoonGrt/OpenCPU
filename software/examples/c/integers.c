#include <stdint.h>

volatile uint16_t left = 0xfff0u;
volatile uint16_t right = 37u;

int main(void) {
    uint16_t a = left, b = right;
    return (int)((a + b) ^ (a - b) ^ (a & b) ^ (a | b) ^ (a ^ b));
}
