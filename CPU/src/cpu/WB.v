`include "../para.v"

module WB #(
    parameter CPU_WIDTH = 16
) (
    input  wire [CPU_WIDTH-1:0] ALUout,
    input  wire [CPU_WIDTH-1:0] DRAMdata,
    input  wire                 RWSel,
    output wire [CPU_WIDTH-1:0] WB
);

    reg [CPU_WIDTH-1:0] reg_RegWd;
    assign WB = RWSel ? DRAMdata : ALUout;

endmodule
