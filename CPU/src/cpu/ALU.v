`include "../para.v"

module ALU #(
    parameter CPU_WIDTH = 16
) (
    input  wire [CPU_WIDTH-1:0] A,
    input  wire [CPU_WIDTH-1:0] B,
    input  wire [          2:0] ALUop,
    output wire [CPU_WIDTH-1:0] ALUout,
    output wire                 overflow
);

    wire [CPU_WIDTH-1:0] Ain;
    wire [CPU_WIDTH-1:0] Bin;
    wire                 suben;

    wire [CPU_WIDTH-1:0] addOut;
    wire [CPU_WIDTH-1:0] subOut;
    wire [CPU_WIDTH-1:0] andOut;
    wire [CPU_WIDTH-1:0] orOut;
    wire [CPU_WIDTH-1:0] xorOut;
    wire [CPU_WIDTH-1:0] sllOut;
    wire [CPU_WIDTH-1:0] srlOut;
    wire [CPU_WIDTH-1:0] sraOut;

    reg  [CPU_WIDTH-1:0] out_reg;

    //*****************************************************
    //**                    wire
    //*****************************************************
    assign suben = (ALUop == `SUB_op);
    assign Ain = A;
    assign Bin = (suben) ? (~B + 1'b1) : B;

    assign overflow = ((ALUop == `ADD_op) | (ALUop == `SUB_op)) && (Ain[CPU_WIDTH-1] == Bin[CPU_WIDTH-1]) && (Ain[CPU_WIDTH-1] != addOut[CPU_WIDTH-1]);
    assign addOut = Ain + Bin;
    assign andOut = A & B;
    assign orOut = A | B;
    assign xorOut = A ^ B;

    assign sllOut = A << B;
    assign srlOut = A >> B;

    //*****************************************************
    //**                    main
    //*****************************************************
    assign ALUout = out_reg;
    always @(*) begin
        case (ALUop)
            `AND_op: begin
                out_reg = andOut;
            end
            `OR_op: begin
                out_reg = orOut;
            end
            `XOR_op: begin
                out_reg = xorOut;
            end
            `SLL_op: begin
                out_reg = sllOut;
            end
            `SRL_op: begin
                out_reg = sraOut;
            end
            default: begin  // ADD or SUB
                out_reg = addOut;
            end
        endcase
    end

endmodule
