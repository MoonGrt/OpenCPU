module Buffer_Shift #(
    parameter NUM   = 1,
    parameter WIDTH = 16
) (
    input  wire                 clk,
    input  wire                 rst_n,
    input  wire                 we,
    input  wire [    WIDTH-1:0] din,
    output wire [WIDTH*NUM-1:0] dout
);

    reg [NUM*WIDTH-1:0] buff;
    assign dout = buff;

    //*****************************************************
    //**                 Write Buffer
    //*****************************************************
    generate
        if (NUM == 1) begin
            // NUM > 1 case, simple Register Behavior
            always @(posedge clk or negedge rst_n) begin
                if (~rst_n) buff <= 0;
                else if (we) buff <= din;  // No shifting, direct write
            end
        end else begin
            // NUM > 1 case, shift register behavior
            always @(posedge clk or negedge rst_n) begin
                if (~rst_n) buff <= 0;
                else if (we) buff <= {buff[(NUM-1)*WIDTH-1:0], din};  // Shift and insert new data
            end
        end
    endgenerate

endmodule
