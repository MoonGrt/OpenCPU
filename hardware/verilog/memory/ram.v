// FPGA-initialized 16-bit words, asynchronous read and synchronous write.
// CPU reset intentionally does not erase RAM or an uploaded instruction image.
module ram #(
    parameter integer DEPTH = 1024,
    parameter INIT_FILE = "",
    parameter [15:0] INITIAL_WORD = 16'h0000
) (
    input wire clk,
    input wire read_enable,
    input wire write_enable,
    input wire [15:0] address,
    input wire [15:0] write_data,
    output wire [15:0] read_data
);
    localparam integer INDEX_WIDTH = DEPTH <= 1 ? 1 : $clog2(DEPTH);
    reg [15:0] words [0:DEPTH-1];
    wire address_valid = {16'b0, address} < DEPTH;
    wire [INDEX_WIDTH-1:0] index = address[INDEX_WIDTH-1:0];
    integer word_index;

    initial begin
        for (word_index = 0; word_index < DEPTH; word_index = word_index + 1)
            words[word_index] = INITIAL_WORD;
        if (INIT_FILE != "")
            $readmemb(INIT_FILE, words);
    end

    assign read_data = read_enable && address_valid ? words[index] : 16'h0000;
    always @(posedge clk) begin
        if (write_enable && address_valid)
            words[index] <= write_data;
    end
endmodule
