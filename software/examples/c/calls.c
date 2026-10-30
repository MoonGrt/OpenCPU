/* The fourth argument crosses the a4 / stack argument boundary. */
static long combine(int first, int second, int third, long wide, int tail) {
    return wide + first + second + third + tail;
}

int main(void) {
    unsigned long value = (unsigned long)combine(1, 2, 3, 0x12340000L, 4);
    return (int)((unsigned)value ^ (unsigned)(value >> 16));
}
