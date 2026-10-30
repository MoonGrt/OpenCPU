// Single-clock SoC: separate instruction/data paths, no internal tri-state bus.
module soc #(
    parameter integer CLK_FREQ = 27_000_000,
    parameter integer UART_BPS = 115200,
    parameter integer ROM_DEPTH = 1024,
    parameter integer RAM_DEPTH = 1024,
    parameter integer ENABLE_UART = 1,
    parameter integer ENABLE_TIMER = 1,
    parameter integer ENABLE_DISPLAY = 0,
    parameter ROM_INIT_FILE = ""
) (
    input wire clk,
    input wire rst_n,
    input wire [3:0] buttons,
    input wire [3:0] switches,
    input wire uart_rx,
    output wire uart_tx,
    output wire [3:0] led,
    output wire [3:0] digit_enable,
    output wire [7:0] segments
);
    wire cpu_rst_n, uart_rst_n;
    reset_sync cpu_reset(.clk(clk), .async_rst_n(rst_n), .rst_n(cpu_rst_n));
    reset_sync uart_power_reset(.clk(clk), .async_rst_n(1'b1), .rst_n(uart_rst_n));

    wire [15:0] instruction_address, instruction;
    wire [15:0] data_address, write_data;
    reg [15:0] read_data;
    wire read_enable, write_enable;
    wire [7:0] irq_events, irq_pending, irq_ack;
    wire uart_irq, timer_irq;
    assign irq_events = {6'b0, uart_irq, timer_irq};
    irq_pending pending_interrupts(
        .clk(clk), .rst_n(cpu_rst_n), .events(irq_events), .acknowledge(irq_ack), .pending(irq_pending)
    );

    core #(.ROM_DEPTH(ROM_DEPTH)) cpu (
        .clk(clk), .rst_n(cpu_rst_n), .irq(irq_pending), .irq_ack(irq_ack),
        .imem_addr(instruction_address), .imem_rdata(instruction),
        .dmem_addr(data_address), .dmem_wdata(write_data), .dmem_rdata(read_data),
        .dmem_read(read_enable), .dmem_write(write_enable),
        .halted(), .faulted(), .fault_pc(), .fault_inst(), .fault_code(),
        .retire_valid(), .retire_pc(), .retire_inst(), .retire_next_pc(), .retire_irq(),
        .debug_registers(), .debug_csrs(), .debug_cycle(), .debug_in_interrupt()
    );

    wire program_valid;
    wire [7:0] program_byte;
    rom #(.DEPTH(ROM_DEPTH), .INIT_FILE(ROM_INIT_FILE)) rom (
        .clk(clk), .program_enable(!rst_n), .program_valid(program_valid), .program_byte(program_byte),
        .fetch_address(instruction_address), .instruction(instruction)
    );

    wire peripheral_page = data_address[15:8] == 8'hff;
    wire led_select = peripheral_page && data_address[7:4] == 4'h0;
    wire button_select = peripheral_page && data_address[7:4] == 4'h1;
    wire switch_select = peripheral_page && data_address[7:4] == 4'h2;
    wire display_select = peripheral_page && data_address[7:4] == 4'h3;
    wire uart_select = peripheral_page && data_address[7:4] == 4'h4;
    wire timer_select = peripheral_page && data_address[7:4] == 4'h5;
    wire first_register = data_address[3:0] == 4'h0;

    wire [15:0] ram_data, led_data, button_data, switch_data, display_data, uart_data, timer_data;
    ram #(.DEPTH(RAM_DEPTH)) ram (
        .clk(clk), .read_enable(read_enable && !peripheral_page),
        .write_enable(write_enable && !peripheral_page), .address(data_address),
        .write_data(write_data), .read_data(ram_data)
    );
    gpio gpio (
        .clk(clk), .rst_n(cpu_rst_n), .buttons(buttons), .switches(switches),
        .led_write(write_enable && led_select && first_register), .write_data(write_data),
        .led_data(led_data), .button_data(button_data), .switch_data(switch_data), .led(led)
    );

    generate
        if (ENABLE_UART != 0) begin: with_uart
            uart #(.CLK_FREQ(CLK_FREQ), .UART_BPS(UART_BPS)) uart (
                .clk(clk), .rst_n(uart_rst_n), .cpu_rst_n(cpu_rst_n),
                .read_enable(read_enable && uart_select), .write_enable(write_enable && uart_select),
                .address(data_address[3:0]), .write_data(write_data), .read_data(uart_data),
                .rx_pin(uart_rx), .tx_pin(uart_tx), .program_valid(program_valid),
                .program_byte(program_byte), .irq(uart_irq)
            );
        end else begin: without_uart
            assign uart_data = 16'b0;
            assign uart_tx = 1'b1;
            assign program_valid = 1'b0;
            assign program_byte = 8'b0;
            assign uart_irq = 1'b0;
        end
        if (ENABLE_TIMER != 0) begin: with_timer
            timer timer (
                .clk(clk), .rst_n(cpu_rst_n), .read_enable(read_enable && timer_select),
                .write_enable(write_enable && timer_select), .address(data_address[3:0]),
                .write_data(write_data), .read_data(timer_data), .irq(timer_irq)
            );
        end else begin: without_timer
            assign timer_data = 16'b0;
            assign timer_irq = 1'b0;
        end
        if (ENABLE_DISPLAY != 0) begin: with_display
            display #(.CLK_FREQ(CLK_FREQ)) display (
                .clk(clk), .rst_n(cpu_rst_n), .write_enable(write_enable && display_select && first_register),
                .write_data(write_data), .read_data(display_data), .digit_enable(digit_enable), .segments(segments)
            );
        end else begin: without_display
            assign display_data = 16'b0;
            assign digit_enable = 4'b1111;
            assign segments = 8'hff;
        end
    endgenerate

    always @(*) begin
        read_data = 16'b0;
        if (read_enable) begin
            if (!peripheral_page)
                read_data = ram_data;
            else if (led_select && first_register)
                read_data = led_data;
            else if (button_select && first_register)
                read_data = button_data;
            else if (switch_select && first_register)
                read_data = switch_data;
            else if (display_select && first_register)
                read_data = display_data;
            else if (uart_select)
                read_data = uart_data;
            else if (timer_select)
                read_data = timer_data;
        end
    end
endmodule
