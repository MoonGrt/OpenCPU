`include "../para.v"

module UART #(
    parameter CLK_FREQ  = 27000000,  //系统时钟频率
    parameter UART_BPS  = 115200,    //串口波特率
    parameter CPU_WIDTH = 16
) (
    input wire                 clk,
    input wire                 dev_clk,
    input wire                 rst_n,
    input wire                 EN,       // 总线同意信号
    input wire [CPU_WIDTH-1:0] addr,
    inout wire [CPU_WIDTH-1:0] data,
    input wire                 ctrl,

    input  uart_rxd,  //UART接收端口
    output uart_txd,  //UART发送端口
    output irq_uart   //UART接收完成
);

    //wire define   
    wire [          7:0] uart_recv_data;  //UART接收数据
    wire [          7:0] uart_send_data;  //UART发送数据
    wire                 uart_tx_busy;  //UART发送忙状态标志

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
    wire clk_input;
    assign clk_input = clk;  // 时钟上升沿读取输入

    // 输入缓冲
    Buffer #(
        .WIDTH(CPU_WIDTH)
    ) input_buf (
        .clk  (clk_input),
        .rst_n(rst_n),
        .din  (data_input),
        .we   (input_call),
        .dout (input_data)
    );

    //串口发送模块    
    uart_send #(
        .CLK_FREQ(CLK_FREQ),  //设置系统时钟频率
        .UART_BPS(UART_BPS)
    )  //设置串口发送波特率
        u_uart_send (
        .sys_clk  (clk),
        .sys_rst_n(rst_n),

        .uart_en     (input_call),
        .uart_din    (input_data[7:0]),
        .uart_tx_busy(uart_tx_busy),
        .uart_txd    (uart_txd)
    );

    //*****************************************************
    //**                    输出到 CPU
    //*****************************************************
    wire clk_output;
    assign clk_output  = clk;
    assign output_data = {24'b0, uart_recv_data};

    Buffer #(
        .WIDTH(CPU_WIDTH)
    ) output_buf (
        .clk  (clk_output),
        .rst_n(rst_n),
        .we   (1'b1),
        .din  (output_data),
        .dout (data_output)
    );

    //串口接收模块     
    uart_recv #(
        .CLK_FREQ(CLK_FREQ),  //设置系统时钟频率
        .UART_BPS(UART_BPS)
    )  //设置串口接收波特率
        u_uart_recv (
        .sys_clk  (clk),
        .sys_rst_n(rst_n),

        .uart_rxd (uart_rxd),
        .uart_done(),
        .done_flag(irq_uart),
        .uart_data(uart_recv_data)
    );

endmodule
