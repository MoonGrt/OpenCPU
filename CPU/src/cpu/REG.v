`include "../para.v"

module REG (
    input wire clk,
    input wire rst_n,

    input wire [2:0] rd,
    input wire [2:0] rs,

    input wire [     2:0] WB_addr,
    input wire [`DATABUS] WB_data,
    input wire            RegWe,
    input wire            reg_clear,

    output wire [`DATABUS] RD,
    output wire [`DATABUS] RS
);

    //*****************************************************
    //**                    Forwarding
    //*****************************************************
    reg [2:0] last_rd, last_rd_reg;
    // wire [2:0] last_rs;  // only write data to rd
    wire rd_forward = (rd == last_rd) && RegWe;
    wire rs_forward = (rs == last_rd) && RegWe;
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            last_rd <= 3'b0;
            last_rd_reg <= 3'b0;
            // last_rs <= 3'b0;
        end else begin
            last_rd <= rd;
            // last_rs <= rs;
        end
    end

    //*****************************************************
    //**                  Write Data
    //*****************************************************
    reg [`DATABUS] rf[7:0];  // 寄存器
    integer i;
    initial
        for (i = 0; i < 8; i = i + 1)
            rf[i] = 0;  // Default initialization is 0

    assign RD = rd_forward ? WB_data : rf[rd];
    assign RS = rs_forward ? WB_data : rf[rs];
    always @(posedge clk) begin
    // always @(posedge clk or negedge rst_n or posedge reg_clear) begin
        if (~rst_n | reg_clear) for (i = 0; i < 8; i = i + 1) rf[i] <= 16'b0;
        // if (~rst_n) for (i = 0; i < 8; i = i + 1) rf[i] <= 16'b0;
        else if (RegWe && WB_addr) rf[WB_addr] <= WB_data;
    end

endmodule
