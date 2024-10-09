`include "../para.v"

module WB (
    input wire [`DATABUS] CSRout,
    input wire [`DATABUS] ALUout,
    input wire [`DATABUS] RAMdata,
    input wire            CSR_wr,
    input wire [     1:0] RWSel,

    output reg [`DATABUS] WB_data = 16'b0
);

    always @(*) begin
        if (RWSel == `WB_EX) WB_data = ALUout;
        else if (RWSel == `WB_RAM) WB_data = RAMdata;
        else if (RWSel == `WB_CSR) WB_data = CSRout;
        else WB_data = ALUout;
    end

endmodule
