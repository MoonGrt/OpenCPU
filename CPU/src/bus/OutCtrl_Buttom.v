module OutCtrl_Buttom #(
    parameter CPU_WIDTH  = 16,
    parameter BUTTOM_NUM = 4
) (
    input  wire [BUTTOM_NUM-1:0] buttom,
    output wire [ CPU_WIDTH-1:0] data
);

    assign data[BUTTOM_NUM-1:0] = buttom;
    assign data[CPU_WIDTH-1:BUTTOM_NUM] = 'b0;

endmodule
