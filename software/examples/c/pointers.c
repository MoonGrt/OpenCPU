#include <stdint.h>

volatile unsigned index_value = 3;

static int *element_address(int *values, unsigned index) {
    return values + index;
}

static int element(int *values, unsigned index) {
    return *element_address(values, index) + *(values + 2);
}

int main(void) {
    uint16_t words[2] = {0x1234u, 0xabcdu};
    unsigned char *bytes = (unsigned char *)words;
    bytes[1] = 0x56u;
    bytes[2] = 0xefu;
    int values[6] = {3, 5, 7, 11, 13, 17};
    return (int)((words[0] ^ words[1]) + (unsigned)element(values, index_value));
}
