`include "isa.vh"

// Decode instruction fields and architectural effects. The core qualifies
// every effect with retirement; this combinational module has no state.
module decode (
    input wire [15:0] instruction,
    output wire [4:0] opcode,
    output wire [2:0] rd,
    output wire [2:0] rs,
    output reg [15:0] immediate,
    output reg illegal,
    output reg register_write,
    output reg memory_read,
    output reg memory_write,
    output reg csr_read,
    output reg csr_write,
    output reg register_clear,
    output wire halt,
    output wire mret
);
    assign opcode = instruction[4:0];
    assign rd = instruction[7:5];
    assign rs = instruction[10:8];
    assign halt = opcode == `OC_OP_HALT;
    assign mret = opcode == `OC_OP_MRET;

    always @(*) begin
        immediate = 16'b0;
        case (opcode)
            `OC_OP_ADDI, `OC_OP_SUBI, `OC_OP_MULI, `OC_OP_JAL, `OC_OP_JR:
                immediate = {{8{instruction[15]}}, instruction[15:8]};
            `OC_OP_ANDI, `OC_OP_ORI, `OC_OP_XORI,
            `OC_OP_SLLI, `OC_OP_SRLI, `OC_OP_LI, `OC_OP_LUI:
                immediate = {8'b0, instruction[15:8]};
            `OC_OP_BEQ, `OC_OP_BLT, `OC_OP_LW, `OC_OP_SW:
                immediate = {{11{instruction[15]}}, instruction[15:11]};
            `OC_OP_J:
                immediate = {{5{instruction[15]}}, instruction[15:5]};
            `OC_OP_CSRR, `OC_OP_CSRW:
                immediate = {11'b0, instruction[15:11]};
            default: begin end
        endcase
    end

    always @(*) begin
        illegal = 1'b0;
        register_write = 1'b0;
        memory_read = 1'b0;
        memory_write = 1'b0;
        csr_read = 1'b0;
        csr_write = 1'b0;
        register_clear = 1'b0;
        case (opcode)
            `OC_OP_ADD, `OC_OP_SUB, `OC_OP_MUL, `OC_OP_AND,
            `OC_OP_OR, `OC_OP_XOR, `OC_OP_SLL, `OC_OP_SRL: begin
                illegal = instruction[15:11] != 5'b0;
                register_write = 1'b1;
            end
            `OC_OP_ADDI, `OC_OP_SUBI, `OC_OP_MULI, `OC_OP_ANDI,
            `OC_OP_ORI, `OC_OP_XORI, `OC_OP_SLLI, `OC_OP_SRLI,
            `OC_OP_LI, `OC_OP_LUI, `OC_OP_JAL:
                register_write = 1'b1;
            `OC_OP_LW: begin
                register_write = 1'b1;
                memory_read = 1'b1;
            end
            `OC_OP_SW:
                memory_write = 1'b1;
            `OC_OP_CSRR: begin
                illegal = instruction[10:8] != 3'b0;
                register_write = 1'b1;
                csr_read = 1'b1;
            end
            `OC_OP_CSRW: begin
                illegal = instruction[10:8] != 3'b0;
                csr_write = 1'b1;
            end
            `OC_OP_RC: begin
                illegal = instruction[15:5] != 11'b0;
                register_clear = 1'b1;
            end
            `OC_OP_HALT, `OC_OP_MRET:
                illegal = instruction[15:5] != 11'b0;
            `OC_OP_BEQ, `OC_OP_BLT, `OC_OP_J, `OC_OP_JR: begin end
            default:
                illegal = 1'b1;
        endcase
    end
endmodule
