`include "../para.v"

module BUS #(
    parameter CLK_FREQ = 50_000_000,
    parameter UART_BPS = 115200
) (
    input wire clk,
    input wire rst_n,

    // data
    input wire [`ADDRBUS] addr,
    inout wire [`DATABUS] data,
    input wire            ctrl,

    // instruction
    input  wire [`ADDRBUS] inst_addr,
    output wire [`DATABUS] inst_data,

    // device
    input wire [`BUTTOMBUS] buttom,
    input wire [`SWITCHBUS] switch,

`ifdef TUBE
    output wire [`TUBEBUS] tube_en,
    output wire [     7:0] seg_led,
`endif

`ifdef UART
    input  wire uart_rx,  // UART rece prot
    output wire uart_tx,  // UART send port
    output wire int_uart, // UART rece interrupt
`endif

`ifdef TIMER
    output wire int_timer,
`endif

    output wire [`LEDBUS] led
);

    //*****************************************************
    //**                 Instruction
    //*****************************************************
    wire [7:0] int_data;
    ROM #(
        .INIT_FILE("F:/Project/Sipeed/FPGA/Tang_Primer/CPU/code/int")
    ) ROM (
        .clk  (clk),
        .rst_n(rst_n),
        .EN   (1'b1),
        .ctrl (int_uart),
        .addr (inst_addr),
        .wdata(int_data),
        .rdata(inst_data)
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

    RAM RAM (
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

`ifdef TUBE
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
`endif

`ifdef UART
    UART #(
        .CLK_FREQ(CLK_FREQ),  // Set system clock frequency
        .UART_BPS(UART_BPS)   // Set serial port baud rate
    ) UART (
        .clk     (clk),
        .dev_clk (dev_clk),
        // .rst_n   (rst_n),
        .rst_n   (1'b1),
        .EN      (BS[5]),
        .addr    (addr),
        .ctrl    (ctrl),
        .data    (data),
        .uart_rxd(uart_rx),  // UART rece prot
        .uart_txd(uart_tx),  // UART send port
        .int_uart(int_uart), // UART rece interrupt
        .int_data(int_data)
    );
`endif

`ifdef TIMER
    Timer Timer (
        .clk      (clk),
        .dev_clk  (dev_clk),
        .rst_n    (rst_n),
        .EN       (BS[6]),
        .addr     (addr),
        .data     (data),
        .ctrl     (ctrl),
        .int_timer(int_timer)
    );
`endif

endmodule
