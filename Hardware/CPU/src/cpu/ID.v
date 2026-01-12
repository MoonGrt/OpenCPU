`include "../para.v"

module ID (
    input wire rst_n,
    input wire [`DATABUS] inst,

    output wire [2:0] rd,
    output wire [2:0] rs,
    output wire [`DATABUS] IMM,

    output reg       CSR_wr,
    output reg [1:0] JUMPop,
    output reg       IMMop,
    output reg [2:0] ALUop,
    output reg [1:0] CMPop,
    output reg       RegWe,
    output reg       mem_ctrl,
    output reg [1:0] RWSel,
    output reg       ABSel,
    output reg       IMMSel,
    output reg       reg_clear
);

    //*****************************************************
    //**                    wire reg
    //*****************************************************
    assign rd = inst[7:5];
    assign rs = inst[10:8];
    assign IMM = IMMSel ? {{8{1'b0}}, inst[`CPU_WIDTH-1: 8]}:{{11{1'b0}}, inst[`CPU_WIDTH-1: 11]};   // 立即数设定为无符号数，扩展不考虑负数情况

    //*****************************************************
    //**              Instruction Decode
    //*****************************************************
    wire [4:0] opecode = inst[4:0];
    always @(*) begin
        if (~rst_n) begin
            CSR_wr = 1'b0;
            JUMPop = 2'b0;
            ALUop = 3'b0;
            CMPop = 2'b0;
            RWSel = `WB_EX;
            IMMop = 1'b0;
            RegWe = 1'b0;
            ABSel = 1'b0;
            IMMSel = 1'b0;
            mem_ctrl = 1'b0;
            reg_clear = 1'b0;
        end else
            // default
            CSR_wr = 1'b0;
            JUMPop = 2'b0;
            ALUop = 3'b0;
            CMPop = 2'b0;
            RWSel = `WB_EX;
            IMMop = 1'b0;
            RegWe = 1'b0;
            ABSel = 1'b0;
            IMMSel = 1'b0;
            mem_ctrl = 1'b0;
            reg_clear = 1'b0;

            // 
            case (opecode)
                `ADD: begin
                    ALUop = `ADD_op;
                    RegWe = 1'b1;
                end
                `SUB: begin
                    ALUop = `SUB_op;
                    RegWe = 1'b1;
                end
                `MUL: begin
                    ALUop = `MUL_op;
                    RegWe = 1'b1;
                end
                `AND: begin
                    ALUop = `AND_op;
                    RegWe = 1'b1;
                end
                `OR: begin
                    ALUop = `OR_op;
                    RegWe = 1'b1;
                end
                `XOR: begin
                    ALUop = `XOR_op;
                    RegWe = 1'b1;
                end
                `SLL: begin
                    ALUop = `SLL_op;
                    RegWe = 1'b1;
                end
                `SRL: begin
                    ALUop = `SRL_op;
                    RegWe = 1'b1;
                end
                `BEQ: begin
                    CMPop = `BEQ_op;
                end
                `BLE: begin
                    CMPop = `BLE_op;
                end

                `ADDI: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `SUBI: begin
                    ALUop = `SUB_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `MULI: begin
                    ALUop = `MUL_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `ANDI: begin
                    ALUop = `AND_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `ORI: begin
                    ALUop = `OR_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `XORI: begin
                    ALUop = `XOR_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `SLLI: begin
                    ALUop = `SLL_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end
                `SRLI: begin
                    ALUop = `SRL_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                end

                `LW: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    RWSel = `WB_RAM;
                    ABSel = 1'b1;
                end
                `SW: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    ABSel = 1'b1;
                    mem_ctrl = 1'b1;
                end
                `CSRR: begin
                    CSR_wr = 1'b0;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    RWSel = `WB_CSR;
                end
                `CSRW: begin
                    CSR_wr = 1'b1;
                    IMMop = 1'b1;
                end

                `JAL: begin
                    JUMPop = `JAL_op;
                    RegWe = 1'b1;
                    IMMop = 1'b1;
                    IMMSel = 1'b1;
                end
                `JR: begin
                    JUMPop = `JR_op;
                    IMMop = 1'b1;
                    IMMSel = 1'b1;
                end
                `LI: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    IMMSel = 1'b1;
                end
                `RC: begin
                    reg_clear= 1'b1;
                end
                default: begin

                end
            endcase
    end

endmodule
