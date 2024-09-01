`include "../para.v"

module Crtl #(
    parameter CPU_WIDTH = 16
) (
    input wire                 clk,
    input wire                 rst_n,
    input wire [CPU_WIDTH-1:0] inst,
    input wire [          1:0] CMPout,

    output reg       cpu_en,
    output reg       PCSel,
    output reg       IMMop,
    output reg [2:0] ALUop,
    output reg       RegWe,
    output reg       mem_ctrl,
    output reg       RWSel,
    output reg       ABSel,
    output reg       IMMSel
);

    //*****************************************************
    //**                     FSM
    //*****************************************************
    // localparam CPU_INIT = 2'd0;
    // localparam CPU_RUN = 2'd1;
    // localparam CPU_END = 2'd2;

    // // State Machine
    // reg [1:0] cpu_state = CPU_RUN;
    // always @(posedge clk or negedge rst_n) begin
    //     if (~rst_n) begin
    //         cpu_en <= 'b0;
    //         cpu_state = CPU_RUN;
    //     end else begin
    //         case (cpu_state)
    //             CPU_INIT: begin
    //                 cpu_state <= CPU_RUN;
    //                 cpu_en <= 'b0;
    //             end
    //             CPU_RUN: begin
    //                 if (!inst) cpu_state <= CPU_END;
    //                 cpu_en <= 'b1;
    //             end
    //             CPU_END: begin
    //                 // cpu_en <= 'b0;
    //             end
    //             default: cpu_state <= CPU_INIT;
    //         endcase
    //     end
    // end

    //*****************************************************
    //**              Instruction Decode
    //*****************************************************
    wire [4:0] opecode;
    assign opecode = inst[4:0];

    always @(*) begin
        if (~rst_n) begin
            ALUop = 3'b0;
            RWSel = 1'b0;
            IMMop = 1'b0;
            RegWe = 1'b0;
            PCSel = 1'b0;
            IMMSel = 1'b0;
            ABSel = 1'b0;
            mem_ctrl = 1'b0;
        end else
            case (opecode)
                `ADD: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SUB: begin
                    ALUop = `SUB_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `AND: begin
                    ALUop = `AND_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `OR: begin
                    ALUop = `OR_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `XOR: begin
                    ALUop = `XOR_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SLL: begin
                    ALUop = `SLL_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SRL: begin
                    ALUop = `SRL_op;
                    IMMop = 1'b0;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `ADDI: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SUBI: begin
                    ALUop = `SUB_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SLLI: begin
                    ALUop = `SLL_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `SRLI: begin
                    ALUop = `SRL_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    PCSel = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                `BEQ: begin
                    ALUop = 3'b0;
                    IMMop = 1'b0;
                    RegWe = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                    if (CMPout == `COMP_EQ) PCSel = 1'b1;
                    else PCSel = 1'b0;
                end
                `BLE: begin
                    ALUop = 3'b0;
                    IMMop = 1'b0;
                    RegWe = 1'b0;
                    RWSel = 1'b0;
                    IMMSel = 1'b0;
                    ABSel = 1'b0;
                    mem_ctrl = 1'b0;
                    if (CMPout == `COMP_LE) PCSel = 1'b1;
                    else PCSel = 1'b0;
                end
                `LI: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    RWSel = 1'b0;
                    PCSel = 1'b0;
                    ABSel = 1'b0;
                    IMMSel = 1'b1;
                    mem_ctrl = 1'b0;
                end
                `SW: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b0;
                    RWSel = 1'b0;
                    PCSel = 1'b0;
                    ABSel = 1'b1;
                    IMMSel = 1'b0;
                    mem_ctrl = 1'b1;  // 1是写数据
                end
                `LW: begin
                    ALUop = `ADD_op;
                    IMMop = 1'b1;
                    RegWe = 1'b1;
                    RWSel = 1'b1;
                    PCSel = 1'b0;
                    ABSel = 1'b1;
                    IMMSel = 1'b0;
                    mem_ctrl = 1'b0;
                end
                default: begin
                    ALUop = 3'b0;
                    IMMop = 1'b0;
                    RegWe = 1'b0;
                    RWSel = 1'b0;
                    PCSel = 1'b0;
                    ABSel = 1'b0;
                    IMMSel = 1'b1;
                    mem_ctrl = 1'b0;
                end
            endcase
    end

endmodule
