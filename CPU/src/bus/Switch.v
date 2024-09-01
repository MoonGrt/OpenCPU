`include "../para.v"

module Switch #(
    parameter CPU_WIDTH  = 16,
    parameter SWITCH_NUM = 4
) (
    input wire                 clk,
    input wire                 dev_clk,
    input wire                 rst_n,
    input wire                 EN,       // 总线同意信号
    input wire [CPU_WIDTH-1:0] addr,
    inout wire [CPU_WIDTH-1:0] data,     // 与总线连接
    input wire                 ctrl,

    // 输入设备--拨码开关
    input wire [SWITCH_NUM-1:0] switch
);

    // 输入线
    wire [CPU_WIDTH-1:0] data_input;  // 数据 -> 缓冲
    wire [CPU_WIDTH-1:0] input_data;  // 缓冲 -> 数据
    // 输出线
    wire [CPU_WIDTH-1:0] data_output;  // 数据 -> 缓冲
    wire [CPU_WIDTH-1:0] output_data;  // 缓冲 -> 数据

    //*****************************************************
    //**                    控制逻辑
    //*****************************************************
    // 输入输出控制
    wire                 input_call;  // 输入
    wire                 output_call;  // 输出

    // 读写控制
    assign input_call = ((EN == 1'b1) && (ctrl == `IO_CTRL_WRITE)) ? 1'b1 : 1'b0;
    assign output_call = ((EN == 1'b1) && (ctrl == `IO_CTRL_READ)) ? 1'b1 : 1'b0;

    //*****************************************************
    //**                    数据交叉开关
    //*****************************************************
    // 地址译码和控制逻辑内部耦合，无需数据交叉开关控制
    // data输出控制
    assign data =  (output_call) ? data_output :  // 总线同意，数据输出
       16'dz;                   // 未定义状况
    // data输入控制
    assign data_input = data;

    //*****************************************************
    //**                    输入到 外设
    //*****************************************************
    //wire clk_input;
    //assign clk_input = clk; // 时钟上升沿读取输入

    //// 输入缓冲
    //Buffer #(.WIDTH(32))
    //input_buf (
    //    .clk(clk_input),
    //    .rst_n(rst_n),
    //    .din(data_input),
    //    .we(input_call),
    //    .dout(input_data)
    //);

    //*****************************************************
    //**                    输出到 CPU
    //*****************************************************
    wire clk_output;
    assign clk_output = clk;

    Buffer #(
        .WIDTH(CPU_WIDTH)
    ) output_buf (
        .clk  (clk_output),
        .rst_n(rst_n),
        .we   (1'b1),
        .din  (output_data),
        .dout (data_output)
    );

    // 外设连接
    OutCtrl_Switch switchCtrl (
        .switch(switch),
        .data  (output_data)
    );

endmodule
