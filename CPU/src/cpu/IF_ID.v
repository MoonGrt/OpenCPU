`include "../para.v"

module IF_ID (
    input wire             clk,
    input wire             rst_n,
    input wire [`CLEARBUS] clear_flag,
    input wire [ `HOLDBUS] hold_flag,

    input  wire [`ADDRBUS] IF_inst_addr,
    input  wire [`DATABUS] IF_inst_data,
    output wire [`ADDRBUS] ID_inst_addr,
    output wire [`DATABUS] ID_inst_data
);

    //*****************************************************
    //**                    Register
    //*****************************************************
    wire hold_en = (hold_flag == `Hold_PPL) | (hold_flag == `Hold_ID);
    wire clear_en = (clear_flag == `Clear_PPL) | (clear_flag == `Clear_ID);
    PPLreg #(`CPU_WIDTH) addr_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, IF_inst_addr, ID_inst_addr);
    PPLreg #(`CPU_WIDTH) data_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, IF_inst_data, ID_inst_data);

endmodule
