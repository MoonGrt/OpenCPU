// Convert external event pulses into levels held until CPU acknowledgement.
// Multiple events of one source coalesce; a new event wins a simultaneous ack.
module irq_pending (
    input wire clk,
    input wire rst_n,
    input wire [7:0] events,
    input wire [7:0] acknowledge,
    output reg [7:0] pending
);
    always @(posedge clk or negedge rst_n) begin
        if (!rst_n)
            pending <= 8'b0;
        else
            pending <= (pending & ~acknowledge) | events;
    end
endmodule
