module Counter #(
    parameter CPU_WIDTH = 16
) (
    input  wire                 en,
    input  wire                 clk,
    input  wire [CPU_WIDTH-1:0] cnt,
    output wire                 irq
);

    reg [25:0] counter = 'b0;
    assign irq = ((counter == cnt) && en) ? 'b1 : 'b0;

    always @(posedge clk) begin
        if (counter == cnt) counter <= 'b0;
        else counter <= counter + 'b1;
    end

endmodule
