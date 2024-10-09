`include "../para.v"

module Tube_InCtrl (
    input  wire            clk,
    input  wire            dev_clk,
    input  wire            rst_n,
    input  wire            we,
    input  wire [`DATABUS] data,
    output wire [     3:0] tube_en,
    output wire [     7:0] seg_led
);

    // Number of digits displayed
    reg [3:0] num;
    // Status: Higher eight bits as digital pipe enable signal
    reg [3:0] statu;
    assign tube_en = statu;

    //*****************************************************
    //**                Display Logic
    //*****************************************************
    reg [6:0] led;
    assign seg_led[6:0] = led[6:0];
    assign seg_led[7]   = 'b0;

    always @(*) begin
        case (num)
            4'h0: led[6:0] = 7'b0111111;  // "0"
            4'h1: led[6:0] = 7'b0000110;  // "1"
            4'h2: led[6:0] = 7'b1011011;  // "2"
            4'h3: led[6:0] = 7'b1001111;  // "3"
            4'h4: led[6:0] = 7'b1100110;  // "4"
            4'h5: led[6:0] = 7'b1101101;  // "5"
            4'h6: led[6:0] = 7'b1111101;  // "6"
            4'h7: led[6:0] = 7'b0000111;  // "7"
            4'h8: led[6:0] = 7'b1111111;  // "8"
            4'h9: led[6:0] = 7'b1101111;  // "9"
            4'ha: led[6:0] = 7'b1110111;  // "a"
            4'hb: led[6:0] = 7'b1111100;  // "b"
            4'hc: led[6:0] = 7'b0111001;  // "c"
            4'hd: led[6:0] = 7'b1011110;  // "d"
            4'he: led[6:0] = 7'b1111001;  // "e"
            4'hf: led[6:0] = 7'b1110001;  // "f"
        endcase
    end

    //*****************************************************
    //**                Data Logic
    //*****************************************************
    always @(*) begin
        case (tube_en)
            4'b0001: num = data[3:0];
            4'b0010: num = data[7:4];
            4'b0100: num = data[11:8];
            4'b1000: num = data[15:12];
            default: num = 'd0;
        endcase
    end

    //*****************************************************
    //**                 State Logic
    //*****************************************************
    always @(posedge dev_clk or negedge rst_n) begin
        if (~rst_n) statu[3:0] <= 4'b0000;
        else begin
            if (statu[3:0] == 8'b0000) statu[3:0] <= 8'b0001;
            else statu[3:0] <= {statu[2:0], statu[3]};
        end
    end

endmodule
