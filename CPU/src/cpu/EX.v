`include "../para.v"

module EX #(
    parameter CPU_WIDTH = 16
) (
    input wire [CPU_WIDTH-1:0] RD,
    input wire [CPU_WIDTH-1:0] RS,
    input wire [CPU_WIDTH-1:0] IMM,

    input wire       ABSel,
    input wire       IMMop,
    input wire [2:0] ALUop,

    output wire [          1:0] CMPout,
    output wire [CPU_WIDTH-1:0] ALUout
);

    //*****************************************************
    //**                    wire reg
    //*****************************************************
    wire [CPU_WIDTH-1:0] ALU_Ain, ALU_Bin, CMP_Ain, CMP_Bin;

    assign ALU_Ain = ABSel ? RS : RD;
    assign ALU_Bin = IMMop ? IMM : RS;
    assign CMP_Ain = RD;
    assign CMP_Bin = IMMop ? IMM : RS;

    //*****************************************************
    //**                    main
    //*****************************************************
    ALU ALU (
        .A       (ALU_Ain),
        .B       (ALU_Bin),
        .ALUop   (ALUop),
        .ALUout  (ALUout),
        .overflow()
    );

    CMP CMP (
        .A     (CMP_Ain),
        .B     (CMP_Bin),
        .CMPout(CMPout)
    );

endmodule
