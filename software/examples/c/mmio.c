#include <opencpu.h>

int main(void) {
    opencpu_mmio_write16(0xff00u, 5);
    opencpu_mmio_write16(0xff30u, 0x1234u);
    return (int)(opencpu_mmio_read16(0xff00u) + opencpu_mmio_read16(0xff30u));
}
