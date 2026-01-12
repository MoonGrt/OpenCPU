`include "../para.v"

module Switch_OutCtrl (
    input  wire [`SWITCHBUS] switch,
    output wire [  `DATABUS] data
);

    assign data[`SWITCHBUS] = switch;
    assign data[`CPU_WIDTH-1:`SWITCH_NUM] = 0;

endmodule
