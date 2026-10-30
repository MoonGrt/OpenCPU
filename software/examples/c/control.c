#include <stdbool.h>

int main(void) {
    int sum = 0;
    for (int i = 0; i < 10; ++i) {
        if (i & 1)
            sum += i;
        else
            sum -= i;
    }
    bool valid = !(sum != 5);
    switch (sum) {
    case 5: return valid ? 125 : 1;
    default: return 2;
    }
}
