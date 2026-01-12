`ifndef PARAM
`define PARAM

//*****************************************************
//**                    Function
//*****************************************************
// `define TUBE
`define UART
`define TIMER
// `define DDR
// `define HDMI

`define ROM_DEPTH 1024
`define RAM_DEPTH 1024

//*****************************************************
//**                   ISA opcode
//*****************************************************
`define ADD 5'b00000
`define SUB 5'b00001
`define MUL 5'b00010
`define AND 5'b00011
`define OR  5'b00100
`define XOR 5'b00101
`define SLL 5'b00110
`define SRL 5'b00111

`define BEQ 5'b01000
`define BLE 5'b01001

`define ADDI 5'b10000
`define SUBI 5'b10001
`define MULI 5'b10010
`define ANDI 5'b10011
`define ORI  5'b10100
`define XORI 5'b10101
`define SLLI 5'b10110
`define SRLI 5'b10111

`define LW 5'b11000
`define SW 5'b11001
`define CSRR 5'b11010
`define CSRW 5'b11011

`define JAL 5'b11100
`define JR 5'b11101
`define LI 5'b11110
`define RC 5'b11111


//*****************************************************
//**                 CPU Parameter
//*****************************************************
`define CPU_WIDTH 16
`define DATABUS `CPU_WIDTH-1:0
`define ADDRBUS `CPU_WIDTH-1:0
`define INTWIDTH 8


//*****************************************************
//**              Hold & Clear Parameter
//*****************************************************
`define HOLDBUS 2:0
`define Hold_None 3'b000
`define Hold_PPL 3'b001
`define Hold_PC 3'b001  // Hold_IF
`define Hold_ID 3'b010
`define Hold_EX 3'b011

`define CLEARBUS 2:0
`define Clear_None 3'b000
`define Clear_PPL 3'b001
`define Clear_PC 3'b001  // Clear_IF
`define Clear_ID 3'b010
`define Clear_EX 3'b011

//*****************************************************
//**                 INT Parameter
//*****************************************************
`define INT_WIDTH 8
`define INT_BUS `INT_WIDTH-1:0
`define INT_NONE 8'h0
`define INT_TIMER 8'b00000001
`define INT_TIMER_ENTRY_ADDR 32'h4
`define INT_UART 8'b00000010
`define INT_UART_ENTRY_ADDR 32'h8

`define CSR_CYCLE 5'd0
`define CSR_CYCLEH 5'd1
`define CSR_MTVEC 5'd2
`define CSR_MCAUSE 5'd3
`define CSR_MEPC 5'd4
`define CSR_MIE 5'd5
`define CSR_MSTATUS 5'd6
`define CSR_MSCRATCH 5'd7


//*****************************************************
//**                   CPU control
//*****************************************************
`define REGWE_READ 1'b0
`define REGWE_WRITE 1'b1


//*****************************************************
//**                  ALU Parameter
//*****************************************************
`define ADD_op 3'b000
`define SUB_op 3'b001
`define MUL_op 3'b010
`define AND_op 3'b011
`define OR_op 3'b100
`define XOR_op 3'b101
`define SLL_op 3'b110
`define SRL_op 3'b111


//*****************************************************
//**                  CMP Parameter
//*****************************************************
`define BEQ_op 2'b01
`define BLE_op 2'b10

`define CMP_EQ 2'b00
`define CMP_L 2'b01
`define CMP_G 2'b10


//*****************************************************
//**                  JUMP Parameter
//*****************************************************
`define JC_op 2'b00  // condition jump
`define JAL_op 2'b01
`define JR_op 2'b10


//*****************************************************
//**               Write Back control
//*****************************************************
`define WBSelBUS 1:0
`define WB_EX 2'b00
`define WB_RAM 2'b01
`define WB_CSR 2'b10

//*****************************************************
//**                   BUS control
//*****************************************************
`define IO_CTRL_READ 1'b0
`define IO_CTRL_WRITE 1'b1


//*****************************************************
//**              Peripheral Configuration
//*****************************************************
`define LED_NUM 4
`define LEDBUS `LED_NUM-1:0
`define SWITCH_NUM 4
`define SWITCHBUS `SWITCH_NUM-1:0
`define BUTTOM_NUM 4
`define BUTTOMBUS `BUTTOM_NUM-1:0
`define TUBE_NUM 4
`define TUBEBUS `TUBE_NUM-1:0

`endif
