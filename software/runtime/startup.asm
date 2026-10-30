# OpenCPU LLVM ABI v1; all addresses below are hardware word addresses.
_start:
    li sp, 1024
    li fp, 0
    call main
    halt
