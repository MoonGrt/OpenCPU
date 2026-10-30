# Echo three bytes injected into simulated UART RX, then HALT.
# CLI: --uart-rx-hex "41 00 ff"; TX is drained automatically after HALT.
main:
    li a4, 0xff40
    li a3, 3
wait_rx:
    lw a1, 1(a4)
    andi a1, 1
    beq a1, zero, wait_rx
    lw a2, 0(a4)
wait_tx:
    lw a1, 1(a4)
    andi a1, 2
    beq a1, zero, wait_tx
    sw a2, 0(a4)
    addi a3, -1
    beq a3, zero, done
    j wait_rx
done:
    halt
