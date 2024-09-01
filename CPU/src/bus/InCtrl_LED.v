module InCtrl_LED #(
    parameter CPU_WIDTH = 16,
    parameter LED_NUM   = 4
) (
    input  wire [CPU_WIDTH-1:0] data,
    output wire [  LED_NUM-1:0] led
);

    // assign led[LED_NUM-1:0] = data[LED_NUM-1:0];
    assign led[LED_NUM-1:0] = ~data[LED_NUM-1:0];

endmodule
