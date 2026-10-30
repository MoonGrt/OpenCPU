// Asynchronous assertion and two-clock deassertion. The initial value provides
// an FPGA power-on reset even when async_rst_n is permanently tied high.
module reset_sync (
    input wire clk,
    input wire async_rst_n,
    output wire rst_n
);
    (* ASYNC_REG = "TRUE" *) reg [1:0] synchronizer = 2'b00;
    always @(posedge clk or negedge async_rst_n) begin
        if (!async_rst_n)
            synchronizer <= 2'b00;
        else
            synchronizer <= {synchronizer[0], 1'b1};
    end
    assign rst_n = synchronizer[1];
endmodule
