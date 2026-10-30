# OpenCPU LLVM ABI v2; all addresses below are hardware word addresses.
_start:
    li sp, 1024
    li fp, 0
    call __opencpu_init_data
    call main
    halt
