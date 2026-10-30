// Simulation-only probes around the real board top. Images enter through UART;
// no test port writes the CPU, ROM, RAM or peripheral state.
module tb_soc (
    input wire clk,
    input wire rst_n,
    input wire [3:0] buttons,
    input wire [3:0] switches,
    input wire uart_rx,
    output wire uart_tx,
    output wire [3:0] led,
    output wire [3:0] digit_enable,
    output wire [7:0] segments,
    output wire halted,
    output wire faulted,
    output wire [1:0] fault_code,
    output wire [15:0] fault_pc,
    output wire [15:0] fault_inst,
    output wire retire_valid,
    output wire [15:0] retire_pc,
    output wire [15:0] retire_inst,
    output wire [15:0] retire_next_pc,
    output wire retire_irq,
    output wire [7:0] irq_ack,
    output wire [127:0] registers,
    output wire [95:0] csrs,
    output wire [31:0] cycle,
    output wire in_interrupt,
    output wire uart_busy,
    output wire [15:0] display_value,
    input wire [15:0] probe_address,
    output wire [15:0] ram_probe,
    output wire [15:0] rom_probe
);
    // 1 MHz and 62500 baud retain 16 clock edges per UART bit, shortening
    // simulation without changing the 8N1 protocol or clock/reset topology.
    top #(
        .CLK_FREQ(1_000_000), .UART_BPS(62500),
        .ROM_DEPTH(1024), .RAM_DEPTH(1024)
    ) dut (
        .clk(clk), .rst_n(rst_n), .buttom(buttons), .switch(switches),
        .uart_rx(uart_rx), .uart_tx(uart_tx), .led(led),
        .tube_en(digit_enable), .seg_led(segments)
    );

    assign halted = dut.soc.cpu.halted;
    assign faulted = dut.soc.cpu.faulted;
    assign fault_code = dut.soc.cpu.fault_code;
    assign fault_pc = dut.soc.cpu.fault_pc;
    assign fault_inst = dut.soc.cpu.fault_inst;
    assign retire_valid = dut.soc.cpu.retire_valid;
    assign retire_pc = dut.soc.cpu.retire_pc;
    assign retire_inst = dut.soc.cpu.retire_inst;
    assign retire_next_pc = dut.soc.cpu.retire_next_pc;
    assign retire_irq = dut.soc.cpu.retire_irq;
    assign irq_ack = dut.soc.cpu.irq_ack;
    assign registers = dut.soc.cpu.debug_registers;
    assign csrs = dut.soc.cpu.debug_csrs;
    assign cycle = dut.soc.cpu.debug_cycle;
    assign in_interrupt = dut.soc.cpu.debug_in_interrupt;
    assign uart_busy = dut.soc.with_uart.uart.status[2];
    assign display_value = dut.soc.display_data;
    assign ram_probe = probe_address < 16'd1024 ? dut.soc.ram.words[probe_address[9:0]] : 16'b0;
    assign rom_probe = probe_address < 16'd1024 ? dut.soc.rom.storage.words[probe_address[9:0]] : 16'b0;
endmodule
