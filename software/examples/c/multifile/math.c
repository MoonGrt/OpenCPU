#include "math.h"

int shared_counter = 3;
static int local_bias = 2;

int triangle(int value) {
    int total = local_bias;
    for (int index = 1; index <= value; ++index)
        total += index;
    return total;
}
