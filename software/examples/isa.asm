# OpenCPU ISA v2: 16-bit constants, a signed stack offset and a function call.
main:
    li sp, 1024
    li a1, 0xabcd
    addi sp, -1
    sw a1, 0(sp)
    li a1, 0
    lw a1, 0(sp)
    call decrement
    sw a1, 0(zero)
    halt
decrement:
    addi a1, -1
    ret
