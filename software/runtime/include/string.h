#ifndef OPENCPU_STRING_H
#define OPENCPU_STRING_H
#include <stddef.h>
void *memcpy(void *restrict destination, const void *restrict source, size_t size);
void *memmove(void *destination, const void *source, size_t size);
void *memset(void *destination, int value, size_t size);
int memcmp(const void *left, const void *right, size_t size);
#endif
