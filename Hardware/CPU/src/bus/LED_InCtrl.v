`include "../para.v"

module LED_InCtrl (
    input  wire [`DATABUS] data,
    output wire [ `LEDBUS] led
);

    // assign led[`LEDBUS] = data[`LEDBUS];
    assign led[`LEDBUS] = ~data[`LEDBUS];

endmodule
