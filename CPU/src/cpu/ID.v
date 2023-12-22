module ID #(
    parameter CPU_WIDTH = 16
) (
    input wire                 clk,
    input wire                 rst_n,
    input wire [CPU_WIDTH-1:0] inst,
    input wire                 cpu_en,
    input wire [CPU_WIDTH-1:0] WB,
    input wire                 IMMSel,
    input wire                 RegWe,

    output wire [CPU_WIDTH-1:0] RD,
    output wire [CPU_WIDTH-1:0] RS,
    output wire [CPU_WIDTH-1:0] IMM
);

    //*****************************************************
    //**                    wire reg
    //*****************************************************
    wire [2:0] rd;
    wire [2:0] rs;

    assign rd = inst[7:5];
    assign rs = inst[10:8];
    //assign IMM = IMMSel ? {{8{1'b0}}, inst[CPU_WIDTH-1: 8]}:{{11{inst[CPU_WIDTH-1]}}, inst[CPU_WIDTH-1: 11]};
    assign IMM = IMMSel ? {{8{1'b0}}, inst[CPU_WIDTH-1: 8]}:{{11{1'b0}}, inst[CPU_WIDTH-1: 11]};   // 立即数设定为无符号数，扩展不考虑负数情况

    // assign rd = cpu_en ? inst[7:5] : 'b0;
    // assign rs = cpu_en ? inst[10:8] : 'b0;
    // //assign IMM = IMMSel ? {{8{1'b0}}, inst[CPU_WIDTH-1: 8]}:{{11{inst[CPU_WIDTH-1]}}, inst[CPU_WIDTH-1: 11]};
    // assign IMM = cpu_en ? (IMMSel ? {{8{1'b0}}, inst[CPU_WIDTH-1: 8]}:{{11{1'b0}}, inst[CPU_WIDTH-1: 11]}) : 'b0;   // 立即数设定为无符号数，扩展不考虑负数情况

    REG Reg (
        .clk  (clk),
        .rst_n(rst_n),
        .rd   (rd),
        .rs   (rs),
        .WB   (WB),
        .RegWe(RegWe),
        .RD   (RD),
        .RS   (RS)
    );

endmodule
