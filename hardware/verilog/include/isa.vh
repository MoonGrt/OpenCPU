`ifndef OPENCPU_ISA_VH
`define OPENCPU_ISA_VH

// ISA v2 has a fixed 16-bit word and three-bit register indices.
// Keep architectural encodings separate from SoC capacities and peripherals.
`define OC_OP_ADD   5'b00000
`define OC_OP_SUB   5'b00001
`define OC_OP_MUL   5'b00010
`define OC_OP_AND   5'b00011
`define OC_OP_OR    5'b00100
`define OC_OP_XOR   5'b00101
`define OC_OP_SLL   5'b00110
`define OC_OP_SRL   5'b00111
`define OC_OP_BEQ   5'b01000
`define OC_OP_BLT   5'b01001
`define OC_OP_HALT  5'b01010
`define OC_OP_MRET  5'b01011
`define OC_OP_LUI   5'b01100
`define OC_OP_J     5'b01101
// 01110 and 01111 are reserved.
`define OC_OP_ADDI  5'b10000
`define OC_OP_SUBI  5'b10001
`define OC_OP_MULI  5'b10010
`define OC_OP_ANDI  5'b10011
`define OC_OP_ORI   5'b10100
`define OC_OP_XORI  5'b10101
`define OC_OP_SLLI  5'b10110
`define OC_OP_SRLI  5'b10111
`define OC_OP_LW    5'b11000
`define OC_OP_SW    5'b11001
`define OC_OP_CSRR  5'b11010
`define OC_OP_CSRW  5'b11011
`define OC_OP_JAL   5'b11100
`define OC_OP_JR    5'b11101
`define OC_OP_LI    5'b11110
`define OC_OP_RC    5'b11111

`define OC_CSR_CYCLE    5'd0
`define OC_CSR_CYCLEH   5'd1
`define OC_CSR_MTVEC    5'd2
`define OC_CSR_MCAUSE   5'd3
`define OC_CSR_MEPC     5'd4
`define OC_CSR_MIE      5'd5
`define OC_CSR_MSTATUS  5'd6
`define OC_CSR_MSCRATCH 5'd7

`endif
