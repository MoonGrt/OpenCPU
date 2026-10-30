// GPIO uses logical active-high register bits and active-low LED board pins.
module gpio (
    input wire clk,
    input wire rst_n,
    input wire [3:0] buttons,
    input wire [3:0] switches,
    input wire led_write,
    input wire [15:0] write_data,
    output wire [15:0] led_data,
    output wire [15:0] button_data,
    output wire [15:0] switch_data,
    output wire [3:0] led
);
    reg [3:0] led_value;
    reg [3:0] button_meta, button_sync;
    reg [3:0] switch_meta, switch_sync;
    assign led = ~led_value;
    assign led_data = {12'b0, led_value};
    assign button_data = {12'b0, button_sync};
    assign switch_data = {12'b0, switch_sync};

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            led_value <= 4'b0;
            button_meta <= 4'b0;
            button_sync <= 4'b0;
            switch_meta <= 4'b0;
            switch_sync <= 4'b0;
        end else begin
            button_meta <= buttons;
            button_sync <= button_meta;
            switch_meta <= switches;
            switch_sync <= switch_meta;
            if (led_write) led_value <= write_data[3:0];
        end
    end
endmodule
