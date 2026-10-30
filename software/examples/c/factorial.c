static int factorial(int value) {
    return value <= 1 ? 1 : value * factorial(value - 1);
}

int main(void) {
    return factorial(5);
}
