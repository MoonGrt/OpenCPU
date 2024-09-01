`include "../para.v"

module Tube #(
    parameter CPU_WIDTH = 16
) (
    input wire                 clk,
    input wire                 dev_clk,
    input wire                 rst_n,
    input wire                 EN,
    input wire [CPU_WIDTH-1:0] addr,
    inout wire [CPU_WIDTH-1:0] data,
    input wire                 ctrl,

    // 输出设备--LED数码管
    output wire [7:0] tube_en,
    output wire [7:0] seg_led
);

    //*****************************************************
    //**                    控制逻辑
    //*****************************************************
    // 输入输出控制
    wire input_call;  // 输入
    wire output_call;  // 输出

    // 读写控制
    assign input_call  = ((EN == 1'b1) && (ctrl == `IO_CTRL_WRITE)) ? 1'b1 : 1'b0;
    assign output_call = ((EN == 1'b1) && (ctrl == `IO_CTRL_READ)) ? 1'b1 : 1'b0;

    //*****************************************************
    //**                    数据交叉开关
    //*****************************************************
    wire [CPU_WIDTH-1:0] data_input;
    wire [CPU_WIDTH-1:0] data_output;
    // 地址译码和控制逻辑内部耦合，无需数据交叉开关控制
    // data输出控制
    assign data =  (output_call) ? data_output :  // 总线同意，数据输出
       16'dz;                   // 未定义状况
    // data输入控制
    assign data_input = data;

    // 数据转换
    InCtrl_Tube InCtrl_Tube (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .we     (input_call),
        .num_in (data_input),
        .tube_en(tube_en),
        .seg_led(seg_led)
    );

endmodule
