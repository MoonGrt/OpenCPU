`include "../para.v"

module RAM (
    input wire            clk,
    input wire            dev_clk,
    input wire            rst_n,
    input wire            EN,
    input wire [`ADDRBUS] addr,
    inout wire [`DATABUS] data,
    input wire            ctrl
);

    // 输入线
    wire [`DATABUS] data_input;  // 数据 -> 缓冲
    wire [`DATABUS] input_data;  // 缓冲 -> 数据
    // 输出线
    wire [`DATABUS] data_output;  // 数据 -> 缓冲
    wire [`DATABUS] output_data;  // 缓冲 -> 数据

    //*****************************************************
    //**                    控制逻辑
    //*****************************************************
    // 输入输出控制
    wire            input_call;  // 输入
    wire            output_call;  // 输出

    // 读写控制
    assign input_call = ((EN == 1'b1) && (ctrl == `IO_CTRL_WRITE)) ? 1'b1 : 1'b0;
    assign output_call = ((EN == 1'b1) && (ctrl == `IO_CTRL_READ)) ? 1'b1 : 1'b0;

    //*****************************************************
    //**                    数据交叉开关
    //*****************************************************
    // 地址译码和控制逻辑内部耦合，无需数据交叉开关控制
    // data输出控制
    assign data = (output_call) ? output_data :  // 总线同意，数据输出
       16'dz;                // 未定义状况
    // data输入控制
    assign data_input = data;

    //*****************************************************
    //**                    输入输出无缓冲
    //*****************************************************
    // 连接主存
    // data_mem data_mem (
    //     .dout (output_data),  //output [15:0] dout
    //     .clk  (clk),          //input clk
    //     .oce  ('b0),          //input oce
    //     .ce   ('b1),          //input ce
    //     .reset('b0),          //input reset
    //     .wre  (input_call),   //input wre
    //     .ad   (addr),         //input [9:0] ad
    //     .din  (data_input)    //input [15:0] din
    // );
    RAM_Gen #(
        .INIT_FILE(""),
        .DP(`RAM_DEPTH),
        .DW(`CPU_WIDTH),
        .MW(`CPU_WIDTH/8),  // (WIDTH/8)
        .AW(`CPU_WIDTH)
    ) data_mem (
        .clk  (clk),
        .rst  (~rst_n),
        .addr (addr),
        .wdata(data_input),
        .sel  ({2{input_call}}),
        .we   (input_call),
        .rdata(output_data)
    );


endmodule
