`include "isa.vh"

// Pure data-path calculation. Register operands are read in execute after the
// preceding instruction commits, avoiding speculative operand forwarding.
module execute (
    input wire [4:0] opcode,
    input wire [15:0] pc,
    input wire [15:0] rd_value,
    input wire [15:0] rs_value,
    input wire [15:0] immediate,
    output reg [15:0] result,
    output reg redirect,
    output reg [15:0] next_pc
);
    wire [15:0] sequential_pc = pc + 16'd1;

    always @(*) begin
        result = 16'b0;
        redirect = 1'b0;
        next_pc = sequential_pc;
        case (opcode)
            `OC_OP_ADD: result = rd_value + rs_value;
            `OC_OP_SUB: result = rd_value - rs_value;
            `OC_OP_MUL: result = rd_value * rs_value;
            `OC_OP_AND: result = rd_value & rs_value;
            `OC_OP_OR: result = rd_value | rs_value;
            `OC_OP_XOR: result = rd_value ^ rs_value;
            `OC_OP_SLL:
                result = rs_value[15:4] != 12'b0 ? 16'b0 : rd_value << rs_value[3:0];
            `OC_OP_SRL:
                result = rs_value[15:4] != 12'b0 ? 16'b0 : rd_value >> rs_value[3:0];
            `OC_OP_ADDI: result = rd_value + immediate;
            `OC_OP_SUBI: result = rd_value - immediate;
            `OC_OP_MULI: result = rd_value * immediate;
            `OC_OP_ANDI: result = rd_value & immediate;
            `OC_OP_ORI: result = rd_value | immediate;
            `OC_OP_XORI: result = rd_value ^ immediate;
            `OC_OP_SLLI:
                result = immediate[15:4] != 12'b0 ? 16'b0 : rd_value << immediate[3:0];
            `OC_OP_SRLI:
                result = immediate[15:4] != 12'b0 ? 16'b0 : rd_value >> immediate[3:0];
            `OC_OP_LW, `OC_OP_SW: result = rs_value + immediate;
            `OC_OP_LI: result = immediate;
            `OC_OP_LUI: result = {immediate[7:0], 8'b0};
            `OC_OP_BEQ: begin
                redirect = rd_value == rs_value;
                if (redirect) next_pc = sequential_pc + immediate;
            end
            `OC_OP_BLT: begin
                redirect = $signed(rd_value) < $signed(rs_value);
                if (redirect) next_pc = sequential_pc + immediate;
            end
            `OC_OP_J: begin
                redirect = 1'b1;
                next_pc = sequential_pc + immediate;
            end
            `OC_OP_JAL: begin
                result = sequential_pc;
                redirect = 1'b1;
                next_pc = sequential_pc + immediate;
            end
            `OC_OP_JR: begin
                redirect = 1'b1;
                next_pc = rd_value + immediate;
            end
            default: begin end
        endcase
    end
endmodule
