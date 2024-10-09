module PPLreg #(
    parameter DW = 32
) (
    input wire clk,
    input wire rst,
    input wire hold_en,

    input  wire [DW-1:0] def,
    input  wire [DW-1:0] din,
    output reg  [DW-1:0] qout = 'b0
);

    always @(posedge clk) begin
        if (rst) qout <= def;
        else if (hold_en) qout <= qout;
        else qout <= din;
    end

endmodule
