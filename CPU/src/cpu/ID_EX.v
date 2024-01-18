`include "../para.v"

module ID_EX (
    input wire             clk,
    input wire             rst_n,
    input wire [`CLEARBUS] clear_flag,
    input wire [ `HOLDBUS] hold_flag,

    input wire [     2:0] ID_rd,
    input wire [`DATABUS] ID_RD,
    input wire [`DATABUS] ID_RS,
    input wire [`DATABUS] ID_IMM,

    input wire [ `DATABUS] ID_inst_addr,
    input wire             ID_CSR_wr,
    input wire [      1:0] ID_JUMPop,
    input wire             ID_IMMop,
    input wire [      2:0] ID_ALUop,
    input wire [      1:0] ID_CMPop,
    input wire             ID_RegWe,
    input wire [`WBSelBUS] ID_RWSel,
    input wire             ID_ABSel,
    input wire             ID_IMMSel,
    input wire             ID_mem_ctrl,

    output wire [     2:0] EX_rd,
    output wire [`DATABUS] EX_RD,
    output wire [`DATABUS] EX_RS,
    output wire [`DATABUS] EX_IMM,

    output wire [ `DATABUS] EX_inst_addr,
    output wire             EX_CSR_wr,
    output wire [      1:0] EX_JUMPop,
    output wire             EX_IMMop,
    output wire [      2:0] EX_ALUop,
    output wire [      1:0] EX_CMPop,
    output wire             EX_RegWe,
    output wire [`WBSelBUS] EX_RWSel,
    output wire             EX_ABSel,
    output wire             EX_IMMSel,
    output wire             EX_mem_ctrl
);

    //*****************************************************
    //**                    Register
    //*****************************************************
    wire hold_en = (hold_flag == `Hold_PPL) | (hold_flag == `Hold_EX);
    wire clear_en = (clear_flag == `Clear_PPL) | (clear_flag == `Clear_EX);
    PPLreg #(`CPU_WIDTH) inst_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, ID_inst_addr, EX_inst_addr);
    PPLreg #(3) rd_reg(clk, ~rst_n|clear_en, hold_en, 3'b0, ID_rd, EX_rd);
    PPLreg #(`CPU_WIDTH) RD_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, ID_RD, EX_RD);
    PPLreg #(`CPU_WIDTH) RS_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, ID_RS, EX_RS);
    PPLreg #(`CPU_WIDTH) IMM_reg(clk, ~rst_n|clear_en, hold_en, 16'b0, ID_IMM, EX_IMM);
    PPLreg #(1) CSRwr_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_CSR_wr, EX_CSR_wr);
    PPLreg #(2) JUMPop_reg(clk, ~rst_n|clear_en, hold_en, 2'b0, ID_JUMPop, EX_JUMPop);
    PPLreg #(1) IMMop_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_IMMop, EX_IMMop);
    PPLreg #(3) ALUop_reg(clk, ~rst_n|clear_en, hold_en, 3'b0, ID_ALUop, EX_ALUop);
    PPLreg #(2) CMPop_reg(clk, ~rst_n|clear_en, hold_en, 2'b0, ID_CMPop, EX_CMPop);
    PPLreg #(1) RegWe_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_RegWe, EX_RegWe);
    PPLreg #(2) RWSel_reg(clk, ~rst_n|clear_en, hold_en, 2'b0, ID_RWSel, EX_RWSel);
    PPLreg #(1) ABSel_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_ABSel, EX_ABSel);
    PPLreg #(1) IMMSel_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_IMMSel, EX_IMMSel);
    PPLreg #(1) memctrl_reg(clk, ~rst_n|clear_en, hold_en, 1'b0, ID_mem_ctrl, EX_mem_ctrl);

endmodule
