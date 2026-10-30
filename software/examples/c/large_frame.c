int main(void) {
    volatile unsigned values[48];
    unsigned sum = 0;
    for (unsigned index = 0; index < 48; ++index)
        values[index] = index * 3u + 1u;
    for (unsigned index = 0; index < 48; ++index)
        sum += values[index];
    return (int)sum;
}
