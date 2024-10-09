`include "../para.v"

module IF (
    input wire clk,
    input wire rst_n,

    input wire            jump_flag,
    input wire [`ADDRBUS] jump_pc,
    input wire [`CLEARBUS] clear_flag,
    input wire [ `HOLDBUS] hold_flag,

    input  wire [`DATABUS] inst_data,
    output wire [`ADDRBUS] inst_addr,
    output wire            hold_pc
);

    //*****************************************************
    //**                    jump
    //*****************************************************
    wire [4:0] opecode = inst_data[4:0];
    assign hold_pc = (opecode == `BEQ) | (opecode == `BLE) | (opecode == `JAL) | (opecode == `JR);
    wire hold_en = (hold_flag == `Hold_PPL) | (hold_flag == `Hold_PC);
    wire clear_en = (clear_flag == `Clear_PPL) | (clear_flag == `Clear_PC);


    //*****************************************************
    //**                     pc
    //*****************************************************
    reg [`ADDRBUS] pc = 16'b0;
    // assign inst_addr = jump_flag ? jump_pc : pc;
    assign inst_addr = pc;
    always @(posedge clk) begin
        if (~rst_n) 
            pc <= 16'b0;
        else if (jump_flag)
            pc <= jump_pc;
        else if (hold_en | clear_en)
            pc <= pc;
        else if (pc == `ROM_DEPTH - 1'b1 || inst_data == 1'b0)
        // else if (pc == `ROM_DEPTH - 1'b1)
            pc <= pc;
        else
            pc <= pc + 1'b1;
    end

endmodule
