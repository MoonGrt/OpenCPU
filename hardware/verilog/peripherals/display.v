// Four active-low hexadecimal digits, refreshed with a clock enable.
module display #(
    parameter CLK_FREQ = 27_000_000,
    parameter SCAN_HZ = 1000
) (
    input wire clk,
    input wire rst_n,
    input wire write_enable,
    input wire [15:0] write_data,
    output wire [15:0] read_data,
    output wire [3:0] digit_enable,
    output wire [7:0] segments
);
    localparam integer RAW_SCAN_CYCLES = CLK_FREQ / (4 * SCAN_HZ);
    localparam integer SCAN_CYCLES = RAW_SCAN_CYCLES < 1 ? 1 : RAW_SCAN_CYCLES;
    localparam integer COUNT_WIDTH = SCAN_CYCLES <= 1 ? 1 : $clog2(SCAN_CYCLES);
    localparam [COUNT_WIDTH-1:0] LAST_CYCLE = SCAN_CYCLES[COUNT_WIDTH-1:0] - 1'b1;
    reg [COUNT_WIDTH-1:0] scan_count;
    reg [1:0] digit;
    reg [15:0] value;
    reg [6:0] glyph;
    wire [3:0] nibble = value[{digit, 2'b00} +: 4];
    assign read_data = value;
    assign digit_enable = ~(4'b0001 << digit);
    assign segments = {1'b1, ~glyph}; // Decimal point remains off.

    always @(*) begin
        case (nibble)
            4'h0: glyph = 7'b0111111;
            4'h1: glyph = 7'b0000110;
            4'h2: glyph = 7'b1011011;
            4'h3: glyph = 7'b1001111;
            4'h4: glyph = 7'b1100110;
            4'h5: glyph = 7'b1101101;
            4'h6: glyph = 7'b1111101;
            4'h7: glyph = 7'b0000111;
            4'h8: glyph = 7'b1111111;
            4'h9: glyph = 7'b1101111;
            4'ha: glyph = 7'b1110111;
            4'hb: glyph = 7'b1111100;
            4'hc: glyph = 7'b0111001;
            4'hd: glyph = 7'b1011110;
            4'he: glyph = 7'b1111001;
            default: glyph = 7'b1110001;
        endcase
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            scan_count <= {COUNT_WIDTH{1'b0}};
            digit <= 2'b0;
            value <= 16'b0;
        end else begin
            if (write_enable) value <= write_data;
            if (scan_count == LAST_CYCLE) begin
                scan_count <= {COUNT_WIDTH{1'b0}};
                digit <= digit + 2'd1;
            end else scan_count <= scan_count + 1'b1;
        end
    end
endmodule
