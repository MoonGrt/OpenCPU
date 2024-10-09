`include "../para.v"

// CSR module
module CSR (
    input wire clk,
    input wire rst_n,

    // form ex
    input wire            EX_we,     // EX模块写CSR寄存器标志
    input wire [`ADDRBUS] EX_raddr,  // EX模块读CSR寄存器地址
    input wire [`ADDRBUS] EX_waddr,  // EX模块写CSR寄存器地址
    input wire [`DATABUS] EX_wdata,  // EX模块写CSR寄存器数据
    // from int
    input wire [     2:0] int_we,       // CLINT写CSR寄存器标志
    input wire [`DATABUS] int_mepc,     // mepc寄存器
    input wire [`DATABUS] int_mcause,   // mcause寄存器
    input wire [`DATABUS] int_mstatus,  // mstatus寄存器

    // to int
    output wire [`DATABUS] csr_mtvec,      // mtvec
    output wire [`DATABUS] csr_mepc,       // mepc
    output wire [`DATABUS] csr_mstatus,    // mstatus
    output wire            global_int_en,  // 全局中断使能标志
    // to ex
    output reg  [`DATABUS] EX_rdata        // EX模块读寄存器数据
);

    reg [    31:0]  cycle;
    reg [`DATABUS]  mtvec;
    reg [`DATABUS]  mcause;
    reg [`DATABUS]  mepc;
    reg [`DATABUS]  mie;
    reg [`DATABUS]  mstatus;
    reg [`DATABUS]  mscratch;

    assign global_int_en = mstatus[3] ? 1'b1 : 1'b0;
    assign csr_mtvec = mtvec;
    assign csr_mepc = mepc;
    assign csr_mstatus = mstatus;

    // cycle counter
    // 复位撤销后就一直计数
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            cycle <= 32'b0;
        end else begin
            cycle <= cycle + 1'b1;
        end
    end

    // write reg
    // 写寄存器操作
    always @(posedge clk or negedge rst_n) begin
        if (~rst_n) begin
            mtvec <= 16'b0;
            mcause <= 16'b0;
            mepc <= 16'b0;
            mie <= 16'b0;
            mstatus <= 16'b0;
            mscratch <= 16'b0;
        end else begin
            // 优先响应ex模块的写操作
            if (EX_we) begin
                case (EX_waddr[11:0])
                    `CSR_MTVEC: begin
                        mtvec <= EX_wdata;
                    end
                    `CSR_MCAUSE: begin
                        mcause <= EX_wdata;
                    end
                    `CSR_MEPC: begin
                        mepc <= EX_wdata;
                    end
                    `CSR_MIE: begin
                        mie <= EX_wdata;
                    end
                    `CSR_MSTATUS: begin
                        mstatus <= EX_wdata;
                    end
                    `CSR_MSCRATCH: begin
                        mscratch <= EX_wdata;
                    end
                    default: begin

                    end
                endcase
            // int模块写操作
            end else if (int_we) begin
                if (int_we[2])
                    mepc <= int_mepc;
                if (int_we[1])
                    mcause <= int_mcause;
                if (int_we[0])
                    mstatus <= int_mstatus;
            end
        end
    end

    // read reg
    // ex模块读CSR寄存器
    always @(*) begin
        if ((EX_waddr[11:0] == EX_raddr[11:0]) && EX_we) begin
            EX_rdata = EX_wdata;
        end else begin
            case (EX_raddr[11:0])
                `CSR_CYCLE: begin
                    EX_rdata = cycle[15:0];
                end
                `CSR_CYCLEH: begin
                    EX_rdata = cycle[31:16];
                end
                `CSR_MTVEC: begin
                    EX_rdata = mtvec;
                end
                `CSR_MCAUSE: begin
                    EX_rdata = mcause;
                end
                `CSR_MEPC: begin
                    EX_rdata = mepc;
                end
                `CSR_MIE: begin
                    EX_rdata = mie;
                end
                `CSR_MSTATUS: begin
                    EX_rdata = mstatus;
                end
                `CSR_MSCRATCH: begin
                    EX_rdata = mscratch;
                end
                default: begin
                    EX_rdata = 16'b0;
                end
            endcase
        end
    end

endmodule
