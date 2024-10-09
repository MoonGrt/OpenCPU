`include "../para.v"

module ALU (
    input  wire [`DATABUS] A,
    input  wire [`DATABUS] B,
    input  wire [     2:0] ALUop,
    output wire [`DATABUS] ALUout,
    output wire            overflow
);

    wire [`DATABUS] Ain;
    wire [`DATABUS] Bin;
    wire            suben;

    wire [`DATABUS] addOut;
    wire [`DATABUS] mulOut;
    wire [`DATABUS] andOut;
    wire [`DATABUS] orOut;
    wire [`DATABUS] xorOut;
    wire [`DATABUS] sllOut;
    wire [`DATABUS] srlOut;

    reg  [`DATABUS] out_reg;

    //*****************************************************
    //**                    wire
    //*****************************************************
    assign suben = (ALUop == `SUB_op);
    assign Ain = A;
    assign Bin = (suben) ? (~B + 1'b1) : B;

    assign overflow = ((ALUop == `ADD_op) | (ALUop == `SUB_op)) && (Ain[`CPU_WIDTH-1] == Bin[`CPU_WIDTH-1]) && (Ain[`CPU_WIDTH-1] != addOut[`CPU_WIDTH-1]);
    assign addOut = Ain + Bin;
    assign mulOut = A * B;
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
            `ADD_op: begin
                out_reg = addOut;
            end
            `SUB_op: begin
                out_reg = addOut;
            end
            `MUL_op: begin
                out_reg = mulOut;
            end
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
                out_reg = srlOut;
            end
            default: begin
                out_reg = 'b0;
            end
        endcase
    end

endmodule
