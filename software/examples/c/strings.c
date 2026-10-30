#include <string.h>

int main(void) {
    char text[] = "OpenCPU";
    char destination[6];
    memcpy(destination, "bytes", sizeof(destination));
    memmove(destination + 1, destination, 4);
    memset(destination + 2, '!', 2);
    if (memcmp(text, "OpenCPU", 7) != 0)
        return 1;
    return text[0] + text[6] + destination[0] + destination[1]
        + destination[2] + destination[3] + destination[4];
}
