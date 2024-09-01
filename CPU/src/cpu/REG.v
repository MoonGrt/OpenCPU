`include "../para.v"

module REG #(
    parameter CPU_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,

    input wire [          2:0] rd,
    input wire [          2:0] rs,
    input wire [CPU_WIDTH-1:0] WB,
    input wire                 RegWe,

    output wire [CPU_WIDTH-1:0] RD,
    output wire [CPU_WIDTH-1:0] RS
);

    reg [CPU_WIDTH-1:0] rf[7:0];  // 寄存器

    assign RD = (rd == 0) ? 0 : rf[(rd)];
    assign RS = (rs == 0) ? 0 : rf[(rs)];

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            rf[0][CPU_WIDTH-1:0] <= 16'h0;
            rf[1][CPU_WIDTH-1:0] <= 16'h0;
            rf[2][CPU_WIDTH-1:0] <= 16'h0;
            rf[3][CPU_WIDTH-1:0] <= 16'h0;
            rf[4][CPU_WIDTH-1:0] <= 16'h0;
            rf[5][CPU_WIDTH-1:0] <= 16'h0;
            rf[6][CPU_WIDTH-1:0] <= 16'h0;
            rf[7][CPU_WIDTH-1:0] <= 16'h0;
        end else if (RegWe == `REGWE_WRITE) begin
            rf[(rd)] <= WB;
        end
    end

endmodule
