int initialized = 123;
static int zeroed[3];
static unsigned char bytes[3] = {0x12u, 0x34u, 0x56u};
static int *chosen = &initialized;

static int counter(void) {
    static int hits;
    return ++hits;
}

int main(void) {
    zeroed[2] = 7;
    return *chosen + counter() + counter() + bytes[0] + bytes[1] + bytes[2] + zeroed[2];
}
