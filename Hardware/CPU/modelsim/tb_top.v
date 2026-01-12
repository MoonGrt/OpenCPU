`timescale 1ns / 1ps
// `define UART_DEBGE

module tb_top;

    parameter CLK_FREQ = 50_000_000;  // clock frequency(Mhz)
    parameter UART_BPS = 10_000_000;  // serial baud rate
    parameter CLK_PERIOD = 10;  // Clock period in ns (50 MHz)
    parameter CYCLE = CLK_FREQ / UART_BPS;

    reg        clk;
    reg        rst_n;
    reg  [3:0] buttom;
    reg  [3:0] switch;
    wire [3:0] led;
    reg        uart_rx = 1'b1;  // UART接收端口
    wire       uart_tx;  // UART发送端口

    always #5 clk <= ~clk;

    initial begin
        clk <= 0;
        rst_n <= 0;
        buttom <= 4'h1;
        switch <= 4'h2;
        #15 rst_n <= 1'b1;
        // #20 rst_n <= 1'b1;  // rst_n 的上升沿不能位于与 clk 的上升沿
`ifdef UART_DEBGE
        #100 rst_n <= 1'b0;
`endif
    end

    top #(
        .CLK_FREQ(CLK_FREQ),  // Set system clock frequency
        .UART_BPS(UART_BPS)   // Set serial port baud rate
    )  top (
        .clk      (clk),
        .rst_n    (rst_n),
        .buttom   (buttom),
        .switch   (switch),
        .led      (led),
        .uart_rx  (uart_rx),
        .uart_tx  (uart_tx)
    );

`ifdef UART_DEBGE
    // Testbench procedure
    initial begin
        // Initialize signals
        uart_rx = 1'b1;  // Idle state of UART line is high
        // Wait a bit and then send a byte
        #300;
        uart_send_byte(8'h00);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
        uart_send_byte(8'h1f);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
        uart_send_byte(8'h01);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
        uart_send_byte(8'h3e);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
        uart_send_byte(8'h00);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
        uart_send_byte(8'h00);  // Send byte 0xA5
        // Wait for reception to complete
        #500;
    end

    // Task to simulate a UART transmission (start bit, 8 data bits, stop bit)
    task uart_send_byte(input [7:0] byte_data);
        integer i;
        begin
            // Start bit (low)
            uart_rx = 1'b0;
            #(CYCLE * CLK_PERIOD);
            // Send 8 data bits (LSB first)
            for (i = 0; i < 8; i = i + 1) begin
                uart_rx = byte_data[i];
                #(CYCLE * CLK_PERIOD);
            end
            // Stop bit (high)
            uart_rx = 1'b1;
            #(CYCLE * CLK_PERIOD);
        end
    endtask
`endif

endmodule
