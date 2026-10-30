`include "isa.vh"

// A UART image is high-byte first. Only explicit programming mode can write.
// Releasing that mode abandons an incomplete word and resets the upload cursor.
module rom #(
    parameter integer DEPTH = 1024,
    parameter INIT_FILE = ""
) (
    input wire clk,
    input wire program_enable,
    input wire program_valid,
    input wire [7:0] program_byte,
    input wire [15:0] fetch_address,
    output wire [15:0] instruction
);
    reg [16:0] upload_address = 17'b0;
    reg [7:0] upper_byte = 8'b0;
    reg upper_valid = 1'b0;
    wire upload_in_range = {15'b0, upload_address} < DEPTH;
    wire upload_write = program_enable && program_valid && upper_valid && upload_in_range;
    wire [15:0] memory_address = program_enable ? upload_address[15:0] : fetch_address;

    always @(posedge clk) begin
        if (!program_enable) begin
            upload_address <= 17'b0;
            upper_byte <= 8'b0;
            upper_valid <= 1'b0;
        end else if (program_valid) begin
            upper_valid <= !upper_valid;
            if (!upper_valid)
                upper_byte <= program_byte;
            else if (upload_in_range)
                upload_address <= upload_address + 17'd1;
        end
    end

    ram #(
        .DEPTH(DEPTH), .INIT_FILE(INIT_FILE), .INITIAL_WORD({11'b0, `OC_OP_HALT})
    ) storage (
        .clk(clk), .read_enable(!program_enable), .write_enable(upload_write),
        .address(memory_address), .write_data({upper_byte, program_byte}), .read_data(instruction)
    );
endmodule
