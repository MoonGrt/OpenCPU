`include "../para.v"

module CPU #(
    parameter CPU_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,

    input wire [7:0] irq,

    output wire [CPU_WIDTH-1:0] inst_addr,
    input  wire [CPU_WIDTH-1:0] inst_data,

    output wire [CPU_WIDTH-1:0] mem_addr,
    output wire [CPU_WIDTH-1:0] mem_wd,
    input  wire [CPU_WIDTH-1:0] mem_rd,
    output wire                 mem_ctrl
);

    wire [CPU_WIDTH-1:0] RD;
    wire [CPU_WIDTH-1:0] RS;
    wire [CPU_WIDTH-1:0] IMM;
    wire [CPU_WIDTH-1:0] DRAMdata;
    wire [CPU_WIDTH-1:0] WB;
    wire [CPU_WIDTH-1:0] ALUout;
    wire [          1:0] CMPout;
    wire [          2:0] ALUop;
    wire                 IMMop;
    wire [CPU_WIDTH-1:0] COMPExOut;
    wire                 cpu_en;
    wire                 PCSel;
    wire                 ABSel;
    wire                 DRAMWE;
    wire                 RWSel;
    wire                 RegWe;
    wire                 IMMSel;

    assign DRAMdata = mem_rd;
    assign mem_addr = ALUout;
    assign mem_wd   = RD;

    Crtl #(
        .CPU_WIDTH(CPU_WIDTH)
    ) ctrl (
        .clk     (clk),
        .rst_n   (rst_n),
        .inst    (inst_data),
        .CMPout  (CMPout),
        .cpu_en  (cpu_en),
        .PCSel   (PCSel),
        .IMMop   (IMMop),
        .ALUop   (ALUop),
        .RegWe   (RegWe),
        .mem_ctrl(mem_ctrl),
        .RWSel   (RWSel),
        .ABSel   (ABSel),
        .IMMSel  (IMMSel)
    );

    IF #(
        .CPU_WIDTH(CPU_WIDTH)
    ) If (
        .clk      (clk),
        .rst_n    (rst_n),
        .inst_data(inst_data),
        .inst_addr(inst_addr),
        .branch_pc(IMM),
        .PCSel    (PCSel),
        .irq      (irq)
    );

    ID #(
        .CPU_WIDTH(CPU_WIDTH)
    ) Id (
        .clk   (clk),
        .rst_n (rst_n),
        .inst  (inst_data),
        .cpu_en(cpu_en),
        .WB    (WB),
        .IMMSel(IMMSel),
        .RegWe (RegWe),

        .RD (RD),
        .RS (RS),
        .IMM(IMM)
    );

    EX #(
        .CPU_WIDTH(CPU_WIDTH)
    ) Ex (
        .RD    (RD),
        .RS    (RS),
        .IMM   (IMM),
        .ABSel (ABSel),
        .IMMop (IMMop),
        .ALUop (ALUop),
        .CMPout(CMPout),
        .ALUout(ALUout)
    );

    WB #(
        .CPU_WIDTH(CPU_WIDTH)
    ) Wb (
        .ALUout  (ALUout),
        .DRAMdata(DRAMdata),
        .RWSel   (RWSel),
        .WB      (WB)
    );

endmodule
