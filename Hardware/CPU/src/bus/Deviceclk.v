
module Deviceclk #(
    parameter EXTEND = 10_000
) (
    input  wire clk,
    input  wire rst_n,
    output wire clk_out
);

    reg [$clog2(EXTEND):0] cnt;
    assign clk_out = (cnt == EXTEND);

    //*****************************************************
    //**                   Counter
    //*****************************************************
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) cnt <= 'b0;
        else if (clk_out) cnt <= 'b0;
        else cnt <= cnt + 'b1;
    end

endmodule
