// Board-facing pin names are retained; all implementation lives in the SoC.
module top #(
    parameter integer CLK_FREQ = 27_000_000,
    parameter integer UART_BPS = 115200,
    parameter ROM_INIT_FILE = "",
    parameter integer ROM_DEPTH = 1024,
    parameter integer RAM_DEPTH = 1024,
    parameter integer ENABLE_UART = 1,
    parameter integer ENABLE_TIMER = 1
) (
    input wire clk,
    input wire rst_n,
    input wire [3:0] buttom,
    input wire [3:0] switch,
`ifdef TUBE
    output wire [3:0] tube_en,
    output wire [7:0] seg_led,
`endif
    input wire uart_rx,
    output wire uart_tx,
    output wire [3:0] led
);
    soc #(
        .CLK_FREQ(CLK_FREQ), .UART_BPS(UART_BPS), .ROM_INIT_FILE(ROM_INIT_FILE),
        .ROM_DEPTH(ROM_DEPTH), .RAM_DEPTH(RAM_DEPTH),
        .ENABLE_UART(ENABLE_UART), .ENABLE_TIMER(ENABLE_TIMER),
`ifdef TUBE
        .ENABLE_DISPLAY(1)
`else
        .ENABLE_DISPLAY(0)
`endif
    ) soc (
        .clk(clk), .rst_n(rst_n), .buttons(buttom), .switches(switch),
        .uart_rx(uart_rx), .uart_tx(uart_tx), .led(led),
`ifdef TUBE
        .digit_enable(tube_en), .segments(seg_led)
`else
        .digit_enable(), .segments()
`endif
    );
endmodule
