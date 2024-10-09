`include "../para.v"
// `define HEX_INIT_FILE
`define BIN_INIT_FILE

module RAM_Gen #(
    parameter INIT_FILE = "",
    parameter DP = 512,
    parameter DW = 32,
    parameter MW = 4,
    parameter AW = 32
) (
    input wire          clk,
    input wire          rst,
    input wire [AW-1:0] addr,
    input wire [DW-1:0] wdata,
    input wire [MW-1:0] sel,
    input wire          we,

    output reg [DW-1:0] rdata
);

    reg  [DW-1:0] ram [0:DP-1];
    // Initialize RAM from a file if INIT_FILE not none
    integer j;
    initial begin
        for (j = 0; j < DP; j = j + 1) begin
            ram[j] = 0;  // Default initialization is 0
        end
        if (INIT_FILE != "") begin  // Read and store init mem file
            `ifdef HEX_INIT_FILE
                $readmemh(INIT_FILE, ram);
            `elsif BIN_INIT_FILE
                $readmemb(INIT_FILE, ram);
            `else
                $error("Unsupported INIT_FILE_FORMAT: %s", `INIT_FILE_FORMAT);
            `endif
        end
    end

    wire [MW-1:0] wen =({MW{we}} & sel);
    // assign rdata = ram[addr];
    always @ (*) begin
        if (rst) rdata = 16'b0;
        else rdata = ram[addr];
    end
    // reg [AW-1:0] addr_r;
    // assign rdata = ram[addr_r];
    // always @ (posedge clk) begin
    //     addr_r <= addr;
    // end
    generate
        genvar i;
        for (i = 0; i < MW; i = i + 1) begin
            if ((8 * i + 8) > DW) begin
                always @(posedge clk) 
                    if (wen[i]) 
                        ram[addr][DW-1:8*i] <= wdata[DW-1:8*i];
            end else begin
                always @(posedge clk) 
                    if (wen[i]) 
                        ram[addr][8*i+7:8*i] <= wdata[8*i+7:8*i];
            end
        end
    endgenerate

endmodule
