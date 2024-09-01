module IF #(
    parameter CPU_WIDTH = 16
) (
    input wire clk,
    input wire rst_n,

    input wire [          7:0] irq,
    input wire                 PCSel,
    input wire [CPU_WIDTH-1:0] branch_pc,

    input  wire [CPU_WIDTH-1:0] inst_data,
    output wire [CPU_WIDTH-1:0] inst_addr
);

    reg [CPU_WIDTH-1:0] pc, npc;
    wire [CPU_WIDTH-1:0] pc4;

    assign pc4 = pc + 1;
    assign inst_addr = pc;

    //*****************************************************
    //**                    main
    //*****************************************************
    always @(posedge clk or negedge rst_n) begin
        // if (~rst_n) pc <= -1;
        if (~rst_n) pc <= 0;
        else pc <= npc;
    end

    always @(*) begin
        case (irq)
            8'b0000_0001:  // timer
            npc = 8'd0;
            8'b0000_0010:  // uart
            npc = 8'd5;
            8'b0000_0100:  // bt
            npc = 8'd5;
            default: npc = (PCSel) ? branch_pc : (inst_data ? pc4 : pc);
        endcase
    end

    //inst_mem inst_mem(
    //       .a(pc[9: 0]),
    //       .spo(inst)
    //   );

endmodule
