// ISA v2 architectural state: seven writable registers and a constant zero.
module regfile (
    input wire clk,
    input wire rst_n,
    input wire [2:0] rd,
    input wire [2:0] rs,
    input wire write_enable,
    input wire [2:0] write_address,
    input wire [15:0] write_data,
    input wire clear,
    output wire [15:0] rd_value,
    output wire [15:0] rs_value,
    output wire [127:0] debug_registers
);
    reg [15:0] registers [1:7];
    integer index;
    assign rd_value = rd == 3'b0 ? 16'b0 : registers[rd];
    assign rs_value = rs == 3'b0 ? 16'b0 : registers[rs];
    assign debug_registers = {registers[7], registers[6], registers[5],
                              registers[4], registers[3], registers[2], registers[1], 16'b0};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            for (index = 1; index < 8; index = index + 1) registers[index] <= 16'b0;
        end else if (clear) begin
            for (index = 1; index < 8; index = index + 1) registers[index] <= 16'b0;
        end else if (write_enable && write_address != 3'b0) begin
            registers[write_address] <= write_data;
        end
    end
endmodule
