# OpenCPU Verilog

当前 RTL 只保留一套 ISA v2 实现。板级入口为
[verilog/top.v](verilog/top.v)，指令行为以 [ISA 规范](../docs/ISA.md) 为准。
源码为 Verilog-2005，使用单个系统时钟；没有内部三态总线或生成的外设时钟。

```text
hardware/
  verilog/
    top.v                       板级管脚包装
    include/isa.vh              opcode、CSR 地址
    core/                       流水线、译码、执行、寄存器、CSR/中断
    memory/                     字存储与串口镜像装载
    peripherals/                GPIO、UART、Timer、四位数码管
    soc/                        地址译码、复位域、中断 pending、SoC 连接
    files.f                     唯一生产源码清单
  common/tb/                    Verilator testbench、驱动、回归与使用说明
  Makefile                      lint、仿真与测试入口
```

旧流水线、旧 UART、分频器、Buffer 包装和重复版本已移除。
`common/tb` 是测试平台源码，编译产物放在其 `build/` 目录，不混入生产源码。

## 板级入口与参数

默认端口名称和宽度保持为 `clk`、`rst_n`、`buttom[3:0]`、`switch[3:0]`、
`uart_rx`、`uart_tx`、`led[3:0]`。保留 `buttom` 的原拼写以兼容原管脚命名。
定义 `TUBE` 时增加 `tube_en[3:0]` 和 `seg_led[7:0]`，均低有效。
没有保留未实现的 DDR/HDMI 管脚占位。

| 参数 | 默认 | 含义 |
|---|---|---|
| CLK_FREQ | 27000000 | 实际输入时钟频率，决定 UART 位周期和显示扫描 |
| UART_BPS | 115200 | UART 波特率；硬件格式固定 8N1 |
| ROM_DEPTH / RAM_DEPTH | 1024 / 1024 | 16 位字数，合法范围 1..65536 |
| ROM_INIT_FILE | 空 | 可选 `$readmemb` 二进制文本镜像 |
| ENABLE_UART / ENABLE_TIMER | 1 / 1 | 可在 elaboration 时关闭相应外设 |

`TUBE` 控制板级显示管脚；内部 `soc.ENABLE_DISPLAY` 控制显示模块生成。
关闭的外设和保留地址读零、写忽略。`0xff00..0xffff` 保留为外设地址页，扩大 RAM 不会覆盖该页。

工作区当前没有 FPGA 工程或引脚/时序约束文件，因此不声称已验证具体管脚位置、资源适配或频率。
导入 FPGA 工具时，按 [files.f](verilog/files.f) 加入全部源码，将 `verilog/include` 加入头文件路径，
选择 `top` 为顶层，再为实际板卡配置管脚与时钟约束。文件清单中的路径相对于 `hardware/verilog`。

## CPU 与存储接口

核采用 F 取指、D 缓存指令、X 译码/读寄存器/执行/提交的三级顺序结构。
每条真实指令的寄存器、CSR、存储和控制副作用均由同一个退休有效位约束。
跳转或中断冲刷两个年轻槽，无软件可见的延迟槽。

- `imem_addr/imem_rdata`：16 位字地址与异步指令读数据。
- `dmem_addr/dmem_wdata/dmem_rdata`：独立数据通道；`dmem_read/dmem_write` 表示真实访问。
- `irq/irq_ack`：请求电平和实际接受源的 one-hot 确认。
- `retire_valid/pc/inst/next_pc/irq`：上升沿前的退休事件；next_pc 包含当次被接受的 IRQ 重定向。
- `debug_registers`：r0 在低 16 位；`debug_csrs` 从低到高为 mtvec/mcause/mepc/mie/mstatus/mscratch。

存储器保持**异步读、上升沿写**契约。不能直接换成同步 BRAM，否则需要同时增加 CPU 等待接口。
ROM 的默认字是 HALT，显式全零字是 NOP；RAM 在 FPGA 配置时初始化为零。
CPU 复位不擦除 ROM/RAM；未映射数据访问读零、写忽略。取指越界或非法编码进入 fault，直到复位。
通用综合可能将异步存储映射为 LUT/触发器，需要目标 FPGA 工程单独评估资源。

## 复位与串口下载

CPU/运行态外设复位采用异步断言、两时钟同步释放。
UART 接收器使用独立的 FPGA 上电复位，因而 CPU 保持复位时仍可接收镜像；
运行态 FIFO、发送器和错误状态随 CPU 复位清理。

1. 构建镜像，例如在仓库根目录执行：

   ```bash
   cd software
   python3 -m opencpu assemble examples/simple/isa.asm --pad-rom -o /tmp/opencpu.bin
   cd ..
   ```

2. 将 CPU 的 `rst_n` 保持为低，通过软件独立下载器发送该镜像，串口选 **115200、8 数据位、无校验、1 停止位**，
   与实际硬件参数匹配。软件不会自动替你切换板上的 CPU 复位。
3. 每字按高字节、低字节装入。等待最后一个完整 UART 帧传输完成后释放复位，CPU 从字地址 0 执行。

只有外部复位仍为低时，接收字节才可写 ROM。退出编程模式会丢弃半个字并重置写地址；
满容量后继续到达的字节不会回绕覆盖地址 0。短镜像不擦除旧尾部，`--pad-rom` 可用 HALT 补齐覆盖。
运行期收到的字节进入 RX FIFO，不修改 ROM。
当前装载协议是原始字节流，没有设备应答或 CRC；发生传输错误时应重新完整装载。

## MMIO 寄存器

地址全部以 16 位字计数，保留偏移读零、写忽略。

| 地址 | 读 | 写 |
|---|---|---|
| 0xff00 | LED 逻辑值低 4 位 | 锁存低 4 位，板级引脚输出其反相 |
| 0xff10 | 双级同步后的按键低 4 位 | 忽略 |
| 0xff20 | 双级同步后的开关低 4 位 | 忽略 |
| 0xff30 | 显示字 | 锁存 4 个十六进制数字；显示关闭时忽略 |
| 0xff40 | RX FIFO 队首，读后出队；空队列为零 | 低 8 位进入 TX FIFO |
| 0xff41 | UART 状态 | 忽略 |
| 0xff42 | UART 错误位，与状态 bit3..5 对齐 | 对 bit3..5 写 1 清除对应错误 |
| 0xff50 | Timer 周期低 16 位 | 设置周期低位 |
| 0xff51 | Timer 周期高 16 位 | 设置周期高位 |
| 0xff52 | Timer control | bit0=enable，bit1=periodic |
| 0xff53 | Timer 计数低位 | 忽略 |
| 0xff54 | Timer 计数高位 | 忽略 |
| 0xff55 | Timer elapsed bit0 | bit0 写 1 清除到期状态 |

UART 状态：bit0=RX 非空，bit1=TX 可写，bit2=发送中或队列未空，
bit3=RX 溢出，bit4=TX 溢出，bit5=帧错误。
默认 RX/TX 各 16 字节 FIFO；软件应先轮询 TX 可写再提交数据。
满队列保留已有数据并设置溢出位；清除错误与新错误同时发生时，新错误优先。
UART 检查起始位中心和停止位；错误帧不会写入镜像或 RX FIFO。

Timer 的周期单位为系统时钟，周期零禁用计数；写周期或控制会从零重新计数。
periodic=0 时到期一次后关闭 enable；periodic=1 时持续按周期触发。
elapsed 为粘滞状态，到期与清除同拍时到期优先。
调整周期时应先关闭 enable，再写高/低周期字，最后重新启用，避免配置中间值提前到期。

**外设迁移**：地址窗口和 ISA 编码保留，但旧 Timer 的“向任意地址依次写两个字”没有清晰寄存器约定，
现改为上述明确地址。此前 LED/Timer 的未驱动读值改为确定的寄存器读回，数码管现会保存写入值。
原先被忽略的地址低位现在用于选择寄存器；软件应使用表中的精确地址，不再依赖任意偏移的别名。

## 中断

Timer 到期产生 IRQ0 事件，有效 UART 接收产生 IRQ1 事件。
pending 锁存保证气泡和软件屏蔽期间到达的事件不会因单周期脉冲消失；同源事件会合并。
核只确认实际接受的源；同拍确认与新事件时保留新事件。多个有效源按最低位优先。
核在指令提交后判断 CSR 使能、保存实际下一 PC；MRET 恢复使能，不允许 ISR 嵌套。
HALT/fault 不再执行新访问，周期 CSR 仍计数。

## 检查与 Verilator 仿真

工具：Python 3.10+、Verilator、g++ 和 make，无需 Qt 或第三方 Python 测试包。
仿真入口兼容 Verilator 4.216，使用 `--cc --exe --build` 构建 C++ 驱动。
从仓库根目录执行：

```bash
make -C hardware lint
make -C hardware test
make -C hardware run
# all 执行 lint 和 test；clean 清理仿真产物
make -C hardware all
```

lint 覆盖默认、显示开启、UART/Timer 关闭和小存储配置。
[common/tb](common/tb/README.md) 保存 `tb_soc.v`、C++ 时钟/串口驱动与 Python 自检；
其 Makefile 也可直接使用。默认运行会汇编 `software/examples/simple/isa.asm`，经真实 UART RX 引脚上传，
释放复位后执行到 HALT。测试平台包装实际板级 `top`，开启 `TUBE`，ROM/RAM 各 1024 字。
为缩短仿真时间，平台采用 1 MHz 时钟和 62500 波特率，每个 UART 位保持 16 拍。
这些是测试平台参数，板级默认时钟和波特率仍按上表配置。

从仓库根目录构建自己的二进制文本镜像，返回根目录后运行仿真并保存波形：

```bash
cd software
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/opencpu.bin
cd ..
make -C hardware/common/tb run IMAGE=/tmp/opencpu.bin TRACE=build/wave.vcd MAX_CYCLES=10000
```

构建和波形集中放在 `common/tb/build/`，已被 Git 忽略。
C++ 驱动在 HALT 时返回 0，fault 时返回 2，超过执行周期上限时返回 3；
通过 make 运行时，相应失败会使目标失败。驱动不会连接实际串口设备。

回归包括纯 ISA 程序的逐提交软件模型对照、当前汇编/编译器示例、
GPIO/显示/UART 的 MMIO、运行态 UART 接收与中断、Timer 中断、非法指令、取指越界和超时。
软件指令级模拟器不模拟 UART/Timer 的物理时钟和 FIFO，这些行为由整机 RTL 自检。
这些检查不代替带目标器件约束的综合、布局布线和实板验证。

## 两套编译器的产物验证

极简 `.oc` 与原生 LLVM `.ll` 都通过共享汇编器生成同样的 16 位字文本镜像，板级协议和 RTL 不变。
默认 `make -C hardware all` 保持独立，不要求安装 LLVM。

按 [LLVM 构建说明](../toolchain/llvm/README.md)构建真实后端后，从仓库根目录运行：

```bash
make -C hardware test-llvm
```

该显式目标在 LLVM 不可用时失败，验证独立返回值、从 `_start` 地址零启动、SP/FP 恢复，
并将 LLVM 产物通过真实 UART RX 引脚上传，逐退休对照软件模型。
LLVM 支持范围及字节/字地址映射见 [ABI](../docs/ABI.md)。首版仅支持受限 `i16` IR，
不宣称支持 C、ELF、一般指针或两个编译器的函数混合调用。
