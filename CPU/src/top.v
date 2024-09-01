`include "../para.v"

module top #(
    parameter CPU_WIDTH = 16,
    parameter BUTTOM_NUM = 4,
    parameter SWITCH_NUM = 4,
    parameter TUBE_NUM = 4,
    parameter LED_NUM = 4
) (
    input wire clk,
    input wire rst_n,

    input wire [BUTTOM_NUM-1:0] buttom,
    input wire [SWITCH_NUM-1:0] switch,

`ifdef TUBE
    output wire [TUBE_NUM-1:0] tube_en,
    output wire [         7:0] seg_led,
`endif

`ifdef UART
    input  wire uart_rx,  //UART接收端口
    output wire uart_tx,  //UART发送端口
`endif

`ifdef DDR
    output [         13:0] ddr_addr,     // ROW_WIDTH=14
    output [          2:0] ddr_bank,     // BANK_WIDTH=3
    output                 ddr_cs,
    output                 ddr_ras,
    output                 ddr_cas,
    output                 ddr_we,
    output                 ddr_ck,
    output                 ddr_ck_n,
    output                 ddr_cke,
    output                 ddr_odt,
    output                 ddr_reset_n,
    output [          1:0] ddr_dm,       // DM_WIDTH=2
    inout  [CPU_WIDTH-1:0] ddr_dq,       // DQ_WIDTH=16
    inout  [          1:0] ddr_dqs,      // DQS_WIDTH=2
    inout  [          1:0] ddr_dqs_n,    // DQS_WIDTH=2
`endif

`ifdef HDMI
    output       O_tmds_clk_p,
    output       O_tmds_clk_n,
    output [2:0] O_tmds_data_p,  // {r,g,b}
    output [2:0] O_tmds_data_n,
`endif

    output wire [LED_NUM-1:0] led
);

    // 
    wire [CPU_WIDTH-1:0] mem_wd;
    wire [CPU_WIDTH-1:0] mem_rd;
    wire [CPU_WIDTH-1:0] mem_addr, inst_addr;
    wire mem_ctrl;
    wire mem_we;
    wire [CPU_WIDTH-1:0] mem_data, inst_data;

    // interrupt
    wire [7:0] irq;
    wire       irq_uart;
    wire       irq_bt;
    wire       irq_timer;

    assign mem_rd   = mem_data;
    assign mem_data = (mem_ctrl) ? mem_wd : 16'hzzzz;  // Access inputs only when writing
    assign irq      = {{5{1'b0}}, irq_bt, irq_uart, irq_timer};

    //*****************************************************
    //**                     CPU
    //*****************************************************
    CPU #(
        .CPU_WIDTH(CPU_WIDTH)
    ) CPU (
        .clk      (clk),
        .rst_n    (rst_n),
        .inst_data(inst_data),
        .inst_addr(inst_addr),
        .mem_addr (mem_addr),
        .mem_ctrl (mem_ctrl),
        .mem_wd   (mem_wd),
        .mem_rd   (mem_rd),
        .irq      (irq)
    );

    //*****************************************************
    //**                 Device Connect
    //*****************************************************
    BUS #(
        .CPU_WIDTH (CPU_WIDTH),
        .BUTTOM_NUM(BUTTOM_NUM),
        .SWITCH_NUM(SWITCH_NUM),
        .TUBE_NUM  (TUBE_NUM),
        .LED_NUM   (LED_NUM)
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
        .irq_uart(irq_uart),
`endif

`ifdef TIMER
        .irq_timer(irq_timer),
`endif

        .led(led)
    );

endmodule
