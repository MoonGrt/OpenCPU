`include "../para.v"

module Counter(
    input  wire        clk,
    input  wire        rst_n,
    input  wire        en,
    input  wire [31:0] data,
    output wire        int
);

    reg [31:0] counter;
    wire [31:0] cnt = data;
    assign int = ((counter == cnt - 1'b1) && en) ? 'b1 : 'b0;

    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) counter <= 'b0;
        else if (counter == cnt - 1'b1) counter <= 'b0;
        else counter <= counter + 1'b1;
    end

endmodule
