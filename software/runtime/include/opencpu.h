#ifndef OPENCPU_H
#define OPENCPU_H
#include <stdint.h>
/* MMIO addresses are hardware WORD addresses, not ordinary C byte pointers. */
#define opencpu_mmio_read16(address) __builtin_opencpu_mmio_read16((uint16_t)(address))
#define opencpu_mmio_write16(address, value) \
    __builtin_opencpu_mmio_write16((uint16_t)(address), (uint16_t)(value))
#endif
