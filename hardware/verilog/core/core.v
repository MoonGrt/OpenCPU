// Fixed-word ISA v2 core with fetch, staging and execute/retire stages.
// Asynchronous instruction/data reads and rising-edge writes are required.
// A redirect discards both younger slots; there are no architectural delay slots.
module core #(
    parameter ROM_DEPTH = 1024
) (
    input wire clk,
    input wire rst_n,
    input wire [7:0] irq,
    output wire [7:0] irq_ack,
    output wire [15:0] imem_addr,
    input wire [15:0] imem_rdata,
    output wire [15:0] dmem_addr,
    output wire [15:0] dmem_wdata,
    input wire [15:0] dmem_rdata,
    output wire dmem_read,
    output wire dmem_write,
    output reg halted,
    output reg faulted,
    output reg [15:0] fault_pc,
    output reg [15:0] fault_inst,
    output reg [1:0] fault_code,
    output wire retire_valid,
    output wire [15:0] retire_pc,
    output wire [15:0] retire_inst,
    output wire [15:0] retire_next_pc,
    output wire retire_irq,
    output wire [127:0] debug_registers,
    output wire [95:0] debug_csrs,
    output wire [31:0] debug_cycle,
    output wire debug_in_interrupt
);
    reg [15:0] fetch_pc, staged_pc, staged_instruction, execute_pc, execute_instruction;
    reg staged_valid, execute_valid;
    wire [4:0] opcode;
    wire [2:0] rd, rs;
    wire [15:0] immediate, rd_value, rs_value, execute_result, execute_next_pc, csr_read_data;
    wire illegal, register_write, decoded_read, decoded_write, csr_read, csr_write;
    wire register_clear, decoded_halt, decoded_mret, execute_redirect;
    wire csr_redirect;
    wire [15:0] csr_redirect_pc;
    wire [15:0] writeback = decoded_read ? dmem_rdata : csr_read ? csr_read_data : execute_result;
    wire execute_in_range = {16'b0, execute_pc} < ROM_DEPTH;
    wire fetch_in_range = {16'b0, fetch_pc} < ROM_DEPTH;
    wire redirect = csr_redirect || (retire_valid && execute_redirect);

    assign imem_addr = fetch_in_range ? fetch_pc : 16'b0;
    assign retire_valid = rst_n && execute_valid && !halted && !faulted && execute_in_range && !illegal;
    assign retire_pc = execute_pc;
    assign retire_inst = execute_instruction;
    // This is the final architectural PC, including a newly accepted IRQ.
    assign retire_next_pc = csr_redirect ? csr_redirect_pc : execute_next_pc;
    assign dmem_read = retire_valid && decoded_read;
    assign dmem_write = retire_valid && decoded_write;
    assign dmem_addr = dmem_read || dmem_write ? execute_result : 16'b0;
    assign dmem_wdata = dmem_write ? rd_value : 16'b0;

    decode decode (
        .instruction(execute_instruction), .opcode(opcode), .rd(rd), .rs(rs),
        .immediate(immediate), .illegal(illegal), .register_write(register_write),
        .memory_read(decoded_read), .memory_write(decoded_write), .csr_read(csr_read),
        .csr_write(csr_write), .register_clear(register_clear),
        .halt(decoded_halt), .mret(decoded_mret)
    );
    regfile register_file (
        .clk(clk), .rst_n(rst_n), .rd(rd), .rs(rs),
        .write_enable(retire_valid && register_write), .write_address(rd), .write_data(writeback),
        .clear(retire_valid && register_clear), .rd_value(rd_value), .rs_value(rs_value),
        .debug_registers(debug_registers)
    );
    execute execute (
        .opcode(opcode), .pc(execute_pc), .rd_value(rd_value), .rs_value(rs_value),
        .immediate(immediate), .result(execute_result), .redirect(execute_redirect),
        .next_pc(execute_next_pc)
    );
    csr control_status (
        .clk(clk), .rst_n(rst_n), .retire_valid(retire_valid),
        .retire_halt(decoded_halt), .retire_mret(decoded_mret),
        .instruction_next_pc(execute_next_pc), .irq(irq),
        .write_enable(csr_write), .address(immediate[4:0]), .write_data(rd_value),
        .read_data(csr_read_data), .redirect(csr_redirect), .redirect_pc(csr_redirect_pc),
        .irq_taken(retire_irq), .irq_ack(irq_ack), .debug_csrs(debug_csrs),
        .debug_cycle(debug_cycle), .debug_in_interrupt(debug_in_interrupt)
    );

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            fetch_pc <= 16'b0;
            staged_pc <= 16'b0;
            staged_instruction <= 16'b0;
            execute_pc <= 16'b0;
            execute_instruction <= 16'b0;
            staged_valid <= 1'b0;
            execute_valid <= 1'b0;
            halted <= 1'b0;
            faulted <= 1'b0;
            fault_pc <= 16'b0;
            fault_inst <= 16'b0;
            fault_code <= 2'b0;
        end else if (!halted && !faulted) begin
            if (execute_valid && (!execute_in_range || illegal)) begin
                faulted <= 1'b1;
                fault_pc <= execute_pc;
                fault_inst <= execute_instruction;
                fault_code <= !execute_in_range ? 2'd2 : 2'd1;
                staged_valid <= 1'b0;
                execute_valid <= 1'b0;
            end else if (retire_valid && decoded_halt) begin
                halted <= 1'b1;
                fetch_pc <= retire_next_pc;
                staged_valid <= 1'b0;
                execute_valid <= 1'b0;
            end else if (redirect) begin
                fetch_pc <= retire_next_pc;
                staged_valid <= 1'b0;
                execute_valid <= 1'b0;
            end else begin
                fetch_pc <= fetch_pc + 16'd1;
                staged_pc <= fetch_pc;
                staged_instruction <= imem_rdata;
                staged_valid <= 1'b1;
                execute_pc <= staged_pc;
                execute_instruction <= staged_instruction;
                execute_valid <= staged_valid;
            end
        end
    end
endmodule
