// Word registers: period low/high, control, count low/high, elapsed W1C.
module timer (
    input wire clk,
    input wire rst_n,
    input wire read_enable,
    input wire write_enable,
    input wire [3:0] address,
    input wire [15:0] write_data,
    output reg [15:0] read_data,
    output reg irq
);
    reg [31:0] period, counter;
    reg enabled, periodic, elapsed;
    wire reconfigure = write_enable && address <= 4'd2;

    always @(*) begin
        read_data = 16'b0;
        if (read_enable) begin
            case (address)
                4'd0: read_data = period[15:0];
                4'd1: read_data = period[31:16];
                4'd2: read_data = {14'b0, periodic, enabled};
                4'd3: read_data = counter[15:0];
                4'd4: read_data = counter[31:16];
                4'd5: read_data = {15'b0, elapsed};
                default: read_data = 16'b0;
            endcase
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            period <= 32'b0;
            counter <= 32'b0;
            enabled <= 1'b0;
            periodic <= 1'b0;
            elapsed <= 1'b0;
            irq <= 1'b0;
        end else begin
            irq <= 1'b0;
            if (write_enable && address == 4'd5 && write_data[0]) elapsed <= 1'b0;
            if (reconfigure) begin
                counter <= 32'b0;
                case (address)
                    4'd0: period[15:0] <= write_data;
                    4'd1: period[31:16] <= write_data;
                    4'd2: begin
                        enabled <= write_data[0];
                        periodic <= write_data[1];
                    end
                    default: begin end
                endcase
            end else if (enabled && period != 32'b0) begin
                if (counter == period - 32'd1) begin
                    counter <= 32'b0;
                    elapsed <= 1'b1; // An expiry wins over a simultaneous W1C.
                    irq <= 1'b1;
                    if (!periodic) enabled <= 1'b0;
                end else counter <= counter + 32'd1;
            end else counter <= 32'b0;
        end
    end
endmodule
