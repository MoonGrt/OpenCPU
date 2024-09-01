`include "../para.v"

module CMP #(
    parameter CPU_WIDTH = 16
) (
    input  wire [CPU_WIDTH-1:0] A,
    input  wire [CPU_WIDTH-1:0] B,
    output wire [          1:0] CMPout
);

    wire       equal;
    wire       less;
    reg  [1:0] out_reg = 0;

    //*****************************************************
    //**                    运算
    //*****************************************************
    // 比较运算
    assign equal  = ($signed(A) == $signed(B)) ? 1'b1 : 1'b0;
    assign less   = ($signed(A) < $signed(B)) ? 1'b1 : 1'b0;

    //*****************************************************
    //**                    输出选择
    //*****************************************************
    assign CMPout = out_reg;

    always @(*) begin
        if (equal) begin
            out_reg = `COMP_EQ;
        end else if (less) begin
            out_reg = `COMP_LE;
        end else begin
            out_reg = `COMP_GE;
        end
    end

endmodule
