<!-- https://www.min2k.com/tools/markmap/ -->

# SOC

## Hardware

### CPU
#### 指令集
- 基础指令集
- 扩展运算指令集
#### Core
##### Interrupt
- CLINT
- PLIC
##### 分支预测
##### Cache
##### FPU


### BUS
- APB
- AXI

### Peripheral
#### SYS
##### Timer
- 计数模式：向上计数、向下计数、中心对称计数模式
- 预分频器：设置时钟分频以调整计数频率
- 自动重载寄存器：配置计数到何值后重载
- PWM模式：设置占空比和频率用于产生PWM信号
- 中断使能
##### DMA
##### Watchdog
#### MEM
##### ROM
- LUTRAM
- BRAM
##### RAM
- LUTRAM
- BRAM
- DDR
#### GPIO
-模式配置：输入、输出、复用
-速度配置：低、中、高
##### UART
- 波特率
- 数据格式：数据位、停止位、校验位
- 中断
##### SPI
- 工作模式：主模式或从模式、时钟极性、时钟相位
- 数据位宽：8位、16位、32位
- 时钟频率：设置SPI时钟频率
- 双向模式：选择单向或双向数据传输
- 中断
##### I2C
- 时钟频率：100kHz、400kHz
- 从设备地址：设置从设备的地址和读写模式
- 工作模式：主模式或从模式
- 中断
##### PWM
#### Driver
- USB
- Ethernet
- Camera
- LCD
- Touch
- Sensor





## Software

### IDE
#### 编译器
- llvm
- 自制
#### 调试器 & 仿真器
- JTAG
- UART

### OS
- Linux
- RTOS
