`include "isa.vh"

// CSR state and interrupt decisions share the same retirement boundary.
// Ordinary CSRW effects happen first; an accepted IRQ then saves the actual
// instruction next PC and updates status. No speculative slot can enter here.
module csr (
    input wire clk,
    input wire rst_n,
    input wire retire_valid,
    input wire retire_halt,
    input wire retire_mret,
    input wire [15:0] instruction_next_pc,
    input wire [7:0] irq,
    input wire write_enable,
    input wire [4:0] address,
    input wire [15:0] write_data,
    output reg [15:0] read_data,
    output reg redirect,
    output reg [15:0] redirect_pc,
    output reg irq_taken,
    output reg [7:0] irq_ack,
    output wire [95:0] debug_csrs,
    output wire [31:0] debug_cycle,
    output reg debug_in_interrupt
);
    reg [31:0] cycle;
    reg [15:0] mtvec, mcause, mepc, mie, mstatus, mscratch;
    wire committed_write = retire_valid && write_enable;
    wire [15:0] effective_mtvec = committed_write && address == `OC_CSR_MTVEC ? write_data : mtvec;
    wire [15:0] effective_mepc = committed_write && address == `OC_CSR_MEPC ? write_data : mepc;
    wire [7:0] effective_mie = committed_write && address == `OC_CSR_MIE ? write_data[7:0] : mie[7:0];
    wire [15:0] effective_mstatus = committed_write && address == `OC_CSR_MSTATUS ? write_data : mstatus;
    wire [7:0] eligible = irq & effective_mie;
    reg [15:0] trap_status, trap_cause;
    reg selected;
    integer index;

    assign debug_csrs = {mscratch, mstatus, mie, mepc, mcause, mtvec};
    assign debug_cycle = cycle;

    always @(*) begin
        case (address)
            `OC_CSR_CYCLE: read_data = cycle[15:0];
            `OC_CSR_CYCLEH: read_data = cycle[31:16];
            `OC_CSR_MTVEC: read_data = mtvec;
            `OC_CSR_MCAUSE: read_data = mcause;
            `OC_CSR_MEPC: read_data = mepc;
            `OC_CSR_MIE: read_data = mie;
            `OC_CSR_MSTATUS: read_data = mstatus;
            `OC_CSR_MSCRATCH: read_data = mscratch;
            default: read_data = 16'b0;
        endcase
    end

    always @(*) begin
        redirect = 1'b0;
        redirect_pc = 16'b0;
        irq_taken = 1'b0;
        irq_ack = 8'b0;
        trap_status = effective_mstatus;
        trap_cause = 16'b0;
        selected = 1'b0;
        index = 0;
        if (rst_n && retire_valid && !retire_halt) begin
            if (retire_mret) begin
                redirect = 1'b1;
                redirect_pc = effective_mepc;
                trap_status[3] = effective_mstatus[7];
                trap_status[7] = 1'b1;
            end else if (!debug_in_interrupt && effective_mstatus[3] && eligible != 8'b0) begin
                redirect = 1'b1;
                redirect_pc = effective_mtvec;
                irq_taken = 1'b1;
                trap_status[7] = effective_mstatus[3];
                trap_status[3] = 1'b0;
                for (index = 0; index < 8; index = index + 1) begin
                    if (!selected && eligible[index]) begin
                        selected = 1'b1;
                        trap_cause = index[15:0];
                        irq_ack[index] = 1'b1;
                    end
                end
            end
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            cycle <= 32'b0;
            mtvec <= 16'b0;
            mcause <= 16'b0;
            mepc <= 16'b0;
            mie <= 16'b0;
            mstatus <= 16'b0;
            mscratch <= 16'b0;
            debug_in_interrupt <= 1'b0;
        end else begin
            cycle <= cycle + 32'd1;
            if (committed_write) begin
                case (address)
                    `OC_CSR_MTVEC: mtvec <= write_data;
                    `OC_CSR_MCAUSE: mcause <= write_data;
                    `OC_CSR_MEPC: mepc <= write_data;
                    `OC_CSR_MIE: mie <= write_data;
                    `OC_CSR_MSTATUS: mstatus <= write_data;
                    `OC_CSR_MSCRATCH: mscratch <= write_data;
                    default: begin end // Cycle counters are read-only; reserved writes are ignored.
                endcase
            end
            if (retire_valid && retire_mret && !retire_halt) begin
                mstatus <= trap_status;
                debug_in_interrupt <= 1'b0;
            end else if (irq_taken) begin
                mepc <= instruction_next_pc;
                mcause <= trap_cause;
                mstatus <= trap_status;
                debug_in_interrupt <= 1'b1;
            end
        end
    end
endmodule
