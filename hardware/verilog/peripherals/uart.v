// 8N1 UART with independent programming reception and runtime RX/TX FIFOs.
// Registers: data=0, status=1, error W1C=2. Error bits are status[5:3].
module uart #(
    parameter CLK_FREQ = 27_000_000,
    parameter UART_BPS = 115200,
    parameter FIFO_DEPTH = 16
) (
    input wire clk,
    input wire rst_n,
    input wire cpu_rst_n,
    input wire read_enable,
    input wire write_enable,
    input wire [3:0] address,
    input wire [15:0] write_data,
    output reg [15:0] read_data,
    input wire rx_pin,
    output wire tx_pin,
    output wire program_valid,
    output wire [7:0] program_byte,
    output wire irq
);
    localparam integer PTR_WIDTH = FIFO_DEPTH <= 1 ? 1 : $clog2(FIFO_DEPTH);
    localparam integer COUNT_WIDTH = FIFO_DEPTH <= 1 ? 1 : $clog2(FIFO_DEPTH + 1);
    localparam [PTR_WIDTH-1:0] LAST_PTR = FIFO_DEPTH[PTR_WIDTH-1:0] - 1'b1;
    localparam [COUNT_WIDTH-1:0] CAPACITY = FIFO_DEPTH[COUNT_WIDTH-1:0];
    reg [7:0] rx_fifo [0:FIFO_DEPTH-1];
    reg [7:0] tx_fifo [0:FIFO_DEPTH-1];
    reg [PTR_WIDTH-1:0] rx_head, rx_tail, tx_head, tx_tail;
    reg [COUNT_WIDTH-1:0] rx_count, tx_count;
    reg rx_overflow, tx_overflow, bad_frame;
    wire runtime_rst_n = rst_n && cpu_rst_n;
    wire received, framing_error, tx_ready;
    wire [7:0] received_byte;
    wire rx_pop = cpu_rst_n && read_enable && address == 4'b0 && rx_count != 0;
    wire tx_pop = cpu_rst_n && tx_ready && tx_count != 0;
    wire tx_request = cpu_rst_n && write_enable && address == 4'b0;
    wire rx_push = cpu_rst_n && received && (rx_count < CAPACITY || rx_pop);
    wire tx_push = tx_request && (tx_count < CAPACITY || tx_pop);
    wire [5:0] status = {bad_frame, tx_overflow, rx_overflow,
                        (!tx_ready || tx_count != 0), (tx_count < CAPACITY || tx_pop), (rx_count != 0)};

    assign program_valid = received;
    assign program_byte = received_byte;
    assign irq = cpu_rst_n && received;
    uart_rx #(.CLK_FREQ(CLK_FREQ), .UART_BPS(UART_BPS)) receiver (
        .clk(clk), .rst_n(rst_n), .rx_pin(rx_pin), .byte_valid(received),
        .byte_data(received_byte), .frame_error(framing_error)
    );
    uart_tx #(.CLK_FREQ(CLK_FREQ), .UART_BPS(UART_BPS)) transmitter (
        .clk(clk), .rst_n(runtime_rst_n), .valid(tx_count != 0),
        .data(tx_fifo[tx_head]), .ready(tx_ready), .tx_pin(tx_pin)
    );

    always @(*) begin
        read_data = 16'b0;
        if (read_enable && cpu_rst_n) begin
            case (address)
                4'd0: if (rx_count != 0) read_data = {8'b0, rx_fifo[rx_head]};
                4'd1: read_data = {10'b0, status};
                4'd2: read_data = {10'b0, bad_frame, tx_overflow, rx_overflow, 3'b0};
                default: read_data = 16'b0;
            endcase
        end
    end

    always @(posedge clk or negedge runtime_rst_n) begin
        if (!runtime_rst_n) begin
            rx_head <= {PTR_WIDTH{1'b0}};
            rx_tail <= {PTR_WIDTH{1'b0}};
            tx_head <= {PTR_WIDTH{1'b0}};
            tx_tail <= {PTR_WIDTH{1'b0}};
            rx_count <= {COUNT_WIDTH{1'b0}};
            tx_count <= {COUNT_WIDTH{1'b0}};
            rx_overflow <= 1'b0;
            tx_overflow <= 1'b0;
            bad_frame <= 1'b0;
        end else begin
            if (write_enable && address == 4'd2) begin
                if (write_data[3]) rx_overflow <= 1'b0;
                if (write_data[4]) tx_overflow <= 1'b0;
                if (write_data[5]) bad_frame <= 1'b0;
            end
            if (received && !rx_push) rx_overflow <= 1'b1;
            if (tx_request && !tx_push) tx_overflow <= 1'b1;
            if (framing_error) bad_frame <= 1'b1;
            if (rx_push) begin
                rx_fifo[rx_tail] <= received_byte;
                rx_tail <= rx_tail == LAST_PTR ? {PTR_WIDTH{1'b0}} : rx_tail + 1'b1;
            end
            if (rx_pop) rx_head <= rx_head == LAST_PTR ? {PTR_WIDTH{1'b0}} : rx_head + 1'b1;
            if (tx_push) begin
                tx_fifo[tx_tail] <= write_data[7:0];
                tx_tail <= tx_tail == LAST_PTR ? {PTR_WIDTH{1'b0}} : tx_tail + 1'b1;
            end
            if (tx_pop) tx_head <= tx_head == LAST_PTR ? {PTR_WIDTH{1'b0}} : tx_head + 1'b1;
            case ({rx_push, rx_pop})
                2'b10: rx_count <= rx_count + 1'b1;
                2'b01: rx_count <= rx_count - 1'b1;
                default: begin end
            endcase
            case ({tx_push, tx_pop})
                2'b10: tx_count <= tx_count + 1'b1;
                2'b01: tx_count <= tx_count - 1'b1;
                default: begin end
            endcase
        end
    end
endmodule

// Fixed 8N1 transmitter: every start, data and stop bit spans BIT_CYCLES.
module uart_tx #(
    parameter CLK_FREQ = 27_000_000,
    parameter UART_BPS = 115200
) (
    input wire clk,
    input wire rst_n,
    input wire valid,
    input wire [7:0] data,
    output wire ready,
    output reg tx_pin
);
    localparam integer RAW_BIT_CYCLES = CLK_FREQ / (UART_BPS > 0 ? UART_BPS : 1);
    localparam integer BIT_CYCLES = RAW_BIT_CYCLES < 2 ? 2 : RAW_BIT_CYCLES;
    localparam integer COUNT_WIDTH = BIT_CYCLES <= 2 ? 1 : $clog2(BIT_CYCLES);
    localparam [COUNT_WIDTH-1:0] BIT_LAST = BIT_CYCLES[COUNT_WIDTH-1:0] - 1'b1;
    localparam [1:0] IDLE = 2'd0, START = 2'd1, DATA = 2'd2, STOP = 2'd3;
    reg [1:0] state;
    reg [COUNT_WIDTH-1:0] count;
    reg [2:0] bit_index;
    reg [7:0] shift;
    assign ready = state == IDLE;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            count <= {COUNT_WIDTH{1'b0}};
            bit_index <= 3'b0;
            shift <= 8'b0;
            tx_pin <= 1'b1;
        end else begin
            case (state)
                IDLE: begin
                    count <= {COUNT_WIDTH{1'b0}};
                    tx_pin <= 1'b1;
                    if (valid) begin
                        shift <= data;
                        bit_index <= 3'b0;
                        state <= START;
                        tx_pin <= 1'b0;
                    end
                end
                START: begin
                    if (count == BIT_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        tx_pin <= shift[0];
                        state <= DATA;
                    end else count <= count + 1'b1;
                end
                DATA: begin
                    if (count == BIT_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        if (bit_index == 3'd7) begin
                            tx_pin <= 1'b1;
                            state <= STOP;
                        end else begin
                            bit_index <= bit_index + 3'd1;
                            tx_pin <= shift[bit_index + 3'd1];
                        end
                    end else count <= count + 1'b1;
                end
                STOP: begin
                    if (count == BIT_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        state <= IDLE;
                    end else count <= count + 1'b1;
                end
                default: begin
                    state <= IDLE;
                    tx_pin <= 1'b1;
                end
            endcase
        end
    end
endmodule

// Fixed 8N1 receiver. A false start is ignored; a bad stop enters break wait.
module uart_rx #(
    parameter CLK_FREQ = 27_000_000,
    parameter UART_BPS = 115200
) (
    input wire clk,
    input wire rst_n,
    input wire rx_pin,
    output reg byte_valid,
    output reg [7:0] byte_data,
    output reg frame_error
);
    localparam integer RAW_BIT_CYCLES = CLK_FREQ / (UART_BPS > 0 ? UART_BPS : 1);
    localparam integer BIT_CYCLES = RAW_BIT_CYCLES < 2 ? 2 : RAW_BIT_CYCLES;
    localparam integer COUNT_WIDTH = BIT_CYCLES <= 2 ? 1 : $clog2(BIT_CYCLES);
    localparam [COUNT_WIDTH-1:0] BIT_LAST = BIT_CYCLES[COUNT_WIDTH-1:0] - 1'b1;
    localparam integer HALF_CYCLES = BIT_CYCLES / 2;
    localparam [COUNT_WIDTH-1:0] HALF_LAST = HALF_CYCLES[COUNT_WIDTH-1:0] - 1'b1;
    localparam [2:0] IDLE = 3'd0, START = 3'd1, DATA = 3'd2, STOP = 3'd3, BREAK = 3'd4;
    reg [2:0] state;
    reg [COUNT_WIDTH-1:0] count;
    reg [2:0] bit_index;
    reg [7:0] shift;
    reg rx_meta, rx_sync;

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            rx_meta <= 1'b1;
            rx_sync <= 1'b1;
        end else begin
            rx_meta <= rx_pin;
            rx_sync <= rx_meta;
        end
    end

    always @(posedge clk or negedge rst_n) begin
        if (!rst_n) begin
            state <= IDLE;
            count <= {COUNT_WIDTH{1'b0}};
            bit_index <= 3'b0;
            shift <= 8'b0;
            byte_valid <= 1'b0;
            byte_data <= 8'b0;
            frame_error <= 1'b0;
        end else begin
            byte_valid <= 1'b0;
            frame_error <= 1'b0;
            case (state)
                IDLE: begin
                    count <= {COUNT_WIDTH{1'b0}};
                    if (!rx_sync) state <= START;
                end
                START: begin
                    if (count == HALF_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        if (!rx_sync) begin
                            bit_index <= 3'b0;
                            state <= DATA;
                        end else state <= IDLE;
                    end else count <= count + 1'b1;
                end
                DATA: begin
                    if (count == BIT_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        shift[bit_index] <= rx_sync;
                        if (bit_index == 3'd7) state <= STOP;
                        else bit_index <= bit_index + 3'd1;
                    end else count <= count + 1'b1;
                end
                STOP: begin
                    if (count == BIT_LAST) begin
                        count <= {COUNT_WIDTH{1'b0}};
                        if (rx_sync) begin
                            byte_data <= shift;
                            byte_valid <= 1'b1;
                            state <= IDLE;
                        end else begin
                            frame_error <= 1'b1;
                            state <= BREAK;
                        end
                    end else count <= count + 1'b1;
                end
                BREAK: begin
                    count <= {COUNT_WIDTH{1'b0}};
                    if (rx_sync) state <= IDLE;
                end
                default: state <= IDLE;
            endcase
        end
    end
endmodule
