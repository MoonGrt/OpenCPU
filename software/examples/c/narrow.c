#include <stdbool.h>

volatile signed char initial = -100;
volatile unsigned char adjustment = 20;

static signed char adjust(signed char value, unsigned char bias, bool increase) {
    return increase ? value + bias : value - bias;
}

int main(void) {
    return (int)adjust(initial, adjustment, true) + 130;
}
