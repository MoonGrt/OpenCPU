module OutCtrl_Switch #(
    parameter CPU_WIDTH  = 16,
    parameter SWITCH_NUM = 4
) (
    input  wire [SWITCH_NUM-1:0] switch,
    output wire [ CPU_WIDTH-1:0] data
);

    assign data[SWITCH_NUM-1:0] = switch;
    assign data[CPU_WIDTH-1:SWITCH_NUM] = 0;

endmodule
