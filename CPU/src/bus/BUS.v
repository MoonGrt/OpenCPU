`include "../para.v"

module BUS #(
    parameter CPU_WIDTH = 16,
    parameter CLK_FREQ = 2700_0000,
    parameter BUTTOM_NUM = 4,
    parameter SWITCH_NUM = 4,
    parameter TUBE_NUM = 4,
    parameter LED_NUM = 4
) (
    input wire clk,
    input wire rst_n,

    // data
    input wire [CPU_WIDTH-1:0] addr,
    inout wire [CPU_WIDTH-1:0] data,
    input wire                 ctrl,

    // instruction
    input  wire [CPU_WIDTH-1:0] inst_addr,
    output wire [CPU_WIDTH-1:0] inst_data,

    // device
    input wire [BUTTOM_NUM-1:0] buttom,
    input wire [SWITCH_NUM-1:0] switch,

`ifdef TUBE
    output wire [TUBE_NUM-1:0] tube_en,
    output wire [         7:0] seg_led,
`endif

`ifdef UART
    input  wire uart_rx,  // UART rece prot
    output wire uart_tx,  // UART send port
    output wire irq_uart, // UART rece interrupt
`endif

`ifdef TIMER
    output wire irq_timer,
`endif

    output wire [LED_NUM-1:0] led
);

    //*****************************************************
    //**                 Instruction
    //*****************************************************
    inst_mem inst_mem (
        .dout(inst_data),      //output [15:0] dout
        .ad  (inst_addr[9:0])  //input [9:0] ad
    );

    //*****************************************************
    //**                 Device clock
    //*****************************************************
    wire dev_clk;
    Deviceclk #(
        .EXTEND(100)  // Crossover frequency can not be too little, otherwise the equipment operation is not stable
    ) Deviceclk (
        .clk    (clk),
        .rst_n  (rst_n),
        .clk_out(dev_clk)
    );

    //*****************************************************
    //**                 Device Connect
    //*****************************************************
    reg [7:0] BS;  // Bus consent signal
    always @(*) begin
        if (addr[15:8] == 8'hFF) begin  // Peripherals
            case (addr[7:4])
                4'h0: BS = 16'b0000_0010;  // LED
                4'h1: BS = 16'b0000_0100;  // BUTTOM
                4'h2: BS = 16'b0000_1000;  // SWITCH
                4'h3: BS = 16'b0001_0000;  // TUBE
                4'h4: BS = 16'b0010_0000;  // UART
                4'h5: BS = 16'b0100_0000;  // TIMER
                default: BS = 16'b0000_0000;
            endcase
        end else BS = 8'b0000_0001;  // Main MEM
    end

    RAM #(
        .CPU_WIDTH(CPU_WIDTH)
    ) RAM (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .EN     (BS[0]),
        .addr   (addr),
        .ctrl   (ctrl),
        .data   (data)
    );

    LED LED (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .EN     (BS[1]),
        .addr   (addr),
        .ctrl   (ctrl),
        .data   (data),
        .led    (led)
    );

    Buttom Buttom (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .EN     (BS[2]),
        .addr   (addr),
        .ctrl   (ctrl),
        .data   (data),
        .buttom (buttom)
    );

    Switch Switch (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .EN     (BS[3]),
        .addr   (addr),
        .ctrl   (ctrl),
        .data   (data),
        .switch (switch)
    );

    Tube Tube (
        .clk    (clk),
        .dev_clk(dev_clk),
        .rst_n  (rst_n),
        .EN     (BS[4]),
        .addr   (addr),
        .ctrl   (ctrl),
        .data   (data),
        .tube_en(tube_en),
        .seg_led(seg_led)
    );

    UART #(
        .CLK_FREQ(CLK_FREQ),  // Set system clock frequency
        .UART_BPS(115200)  // Set serial port baud rate
    ) UART (
        .clk     (clk),
        .dev_clk (dev_clk),
        .rst_n   (rst_n),
        .EN      (BS[5]),
        .addr    (addr),
        .ctrl    (ctrl),
        .data    (data),
        .uart_rxd(uart_rx),  // UART rece prot
        .uart_txd(uart_tx),  // UART send port
        .irq_uart(irq_uart)  // UART rece interrupt
    );

    Timer Timer (
        .clk      (clk),
        .dev_clk  (dev_clk),
        .rst_n    (rst_n),
        .EN       (BS[6]),
        .addr     (addr),
        .data     (data),
        .ctrl     (ctrl),
        .irq_timer(irq_timer)
    );

endmodule
