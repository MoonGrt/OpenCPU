`include "para.v"

module top #(
    parameter CLK_FREQ = 27_000_000,  // clock frequency(Mhz)
    parameter UART_BPS = 115200     // serial baud rate
) (
    input wire clk,
    input wire rst_n,

    input wire [`BUTTOMBUS] buttom,
    input wire [`SWITCHBUS] switch,

`ifdef TUBE
    output wire [`TUBEBUS] tube_en,
    output wire [     7:0] seg_led,
`endif

`ifdef UART
    input  wire uart_rx,  // UART接收端口
    output wire uart_tx,  // UART发送端口
`endif

`ifdef DDR
    output [13:0] ddr_addr,     // ROW_WIDTH = 14
    output [ 2:0] ddr_bank,     // BANK_WIDTH = 3
    output        ddr_cs,
    output        ddr_ras,
    output        ddr_cas,
    output        ddr_we,
    output        ddr_ck,
    output        ddr_ck_n,
    output        ddr_cke,
    output        ddr_odt,
    output        ddr_reset_n,
    output [ 1:0] ddr_dm,       // DM_WIDTH = 2
    inout  [15:0] ddr_dq,       // DQ_WIDTH = 16
    inout  [ 1:0] ddr_dqs,      // DQS_WIDTH = 2
    inout  [ 1:0] ddr_dqs_n,    // DQS_WIDTH = 2
`endif

`ifdef HDMI
    output       O_tmds_clk_p,
    output       O_tmds_clk_n,
    output [2:0] O_tmds_data_p,  // {r, g, b}
    output [2:0] O_tmds_data_n,
`endif

    output wire [`LEDBUS] led
);

    // data
    wire            mem_ctrl;
    wire            mem_we;
    wire [`DATABUS] mem_wd;
    wire [`DATABUS] mem_rd;
    wire [`DATABUS] mem_addr, inst_addr;
    wire [`DATABUS] mem_data, inst_data;

    // interrupt
    wire [7:0] interrupt;
    wire       int_uart;
    wire       int_bt;
    wire       int_timer;

    assign mem_rd    = mem_data;
    assign mem_data  = (mem_ctrl) ? mem_wd : 16'hzzzz;  // Access inputs only when writing
    assign interrupt = {{7{1'b0}}, int_timer};  // 5'b0, int_bt, int_uart, int_timer

    //*****************************************************
    //**                     CPU
    //*****************************************************
    CPU CPU (
        .clk  (clk),
        .rst_n(rst_n),
        .int  (interrupt),

        .inst_data(inst_data),
        .inst_addr(inst_addr),

        .mem_addr(mem_addr),
        .mem_ctrl(mem_ctrl),
        .mem_wd  (mem_wd),
        .mem_rd  (mem_rd)
    );

    //*****************************************************
    //**                 Device Connect
    //*****************************************************
    BUS #(
        .CLK_FREQ(CLK_FREQ),  // Set system clock frequency
        .UART_BPS(UART_BPS)   // Set serial port baud rate
    ) BUS (
        .clk  (clk),
        .rst_n(rst_n),

        // data
        .addr(mem_addr),
        .ctrl(mem_ctrl),
        .data(mem_data),

        // instruction
        .inst_data(inst_data),
        .inst_addr(inst_addr),

        // device
        .buttom(buttom),
        .switch(switch),

`ifdef TUBE
        .tube_en(tube_en),
        .seg_led(seg_led),
`endif

`ifdef UART
        .uart_rx (uart_rx),
        .uart_tx (uart_tx),
        .int_uart(int_uart),
`endif

`ifdef TIMER
        .int_timer(int_timer),
`endif

        .led(led)
    );

endmodule
