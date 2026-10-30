# One-shot timer: write RAM[0]=1 in the handler, clear elapsed, return and HALT.
# The software simulator measures the period in abstract instruction ticks.
main:
    la a1, handler
    csrw a1, 2
    li a1, 1
    csrw a1, 5
    li a1, 8
    csrw a1, 6
    li a4, 0xff50
    li a1, 12
    sw a1, 0(a4)
    sw zero, 1(a4)
    li a1, 1
    sw a1, 2(a4)
wait:
    lw a1, 0(zero)
    beq a1, zero, wait
    halt
handler:
    li a1, 1
    sw a1, 0(zero)
    sw a1, 5(a4)
    mret
