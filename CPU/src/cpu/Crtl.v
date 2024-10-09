`include "../para.v"

// Control module
// Signal pause pipeline
module ctrl (
    input wire rst_n,

    // from ex
    input wire jump_flag,
    input wire hold_flag_ex,
    // from jtag
    input wire jtag_halt_flag,
    // from int
    input wire clear_flag_int,
    input wire int_assert,

    output reg [`CLEARBUS] clear_flag,
    output reg [ `HOLDBUS] hold_flag
);

    always @(*) begin
        if (~rst_n) begin
            clear_flag = `Clear_None;
        end else begin
            clear_flag = `Clear_None;  // default: `Clear_None
            // prioritize requests from different modules
            // if (int_assert) begin
            //     clear_flag = `Clear_None;
            // end else 
            if (jump_flag | clear_flag_int) begin
                clear_flag = `Clear_PPL;  // clear the entire assembly line
            end else begin
                clear_flag = `Clear_None;
            end
        end
    end

    always @(*) begin
        if (~rst_n) begin
            hold_flag = `Hold_None;
        end else begin
            hold_flag = `Hold_None;  // default: `Hold_None
            // prioritize requests from different modules
            if (hold_flag_ex) begin
                // suspend the entire assembly line
                hold_flag = `Hold_PC;
            end else if (jtag_halt_flag) begin
                // suspend the entire assembly line
                hold_flag = `Hold_PPL;
            end else begin
                hold_flag = `Hold_None;
            end
        end
    end

endmodule
