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




//*****************************************************
//**                   ALU Parameter
//*****************************************************
`define ADD_op 3'b000
`define SUB_op 3'b001
`define AND_op 3'b010
`define OR_op 3'b011
`define XOR_op 3'b100
`define SLL_op 3'b101
`define SRL_op 3'b110

`define ADD 5'b00000
`define SUB 5'b00001
`define AND 5'b00010
`define OR 5'b00011
`define XOR 5'b00100
`define SLL 5'b00101
`define SRL 5'b00110

`define ADDI 5'b10000
`define SUBI 5'b10001
`define ANDI 5'b10010
`define ORI 5'b10011
`define XORI 5'b10100
`define SLLI 5'b10101
`define SRLI 5'b10110

`define BEQ 5'b10111
`define BLE 5'b11000
`define LI 5'b11001
`define LW 5'b11010
`define SW 5'b11011

`define REGWE_READ 1'b0
`define REGWE_WRITE 1'b1

// 比较结果
`define COMP_EQ 2'b00
`define COMP_LE 2'b01
`define COMP_GE 2'b10

/****************************************************************
                        外设配置
*****************************************************************/
`define DEVICE_NUM_LED 8
`define DEVICE_NUM_SWITCH 8
`define DEVICE_NUM_NUMLED 8
`define DEVICE_NUM_NUMLED_EN 8
`define DEVICE_NUM_KB_ROW 4
`define DEVICE_NUM_KB_COL 4

// 控制总线读写
`define IO_CTRL_READ 1'b0    // 不写
`define IO_CTRL_WRITE 1'b1    // 写

`endif
