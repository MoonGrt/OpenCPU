# Verilator 整机仿真

在仓库根目录执行：

```bash
make -C hardware test                  # 构建并运行自动自检
make -C hardware run                   # 运行 software/examples/isa.asm
make -C hardware run TRACE=build/wave.vcd
gtkwave hardware/common/tb/build/wave.vcd
```

需要 Verilator、g++、GNU make；汇编示例和自检还需要 Python 3.10+。
不需要安装 GUI 依赖或第三方 Python 包。已验证 Verilator 4.216，使用
`--cc --exe --build`，不依赖 `--binary` 或 `--timing`。

## 文件与仿真过程

| 文件 | 用途 |
|---|---|
| [tb_soc.v](tb_soc.v) | 包装实际板级 `top`，只读导出 CPU 状态、退休事件及 ROM/RAM 探针 |
| [sim_main.cpp](sim_main.cpp) | C++ 时钟、复位、UART RX 激励、独立 TX 解码、VCD 和 JSON 输出 |
| [test_soc.py](test_soc.py) | Python 自动自检及逐指令软件参考模型对照 |
| [Makefile](Makefile) | 从生产源码清单构建仿真，提供 lint/build/test/run/clean |

构建使用 [files.f](../../verilog/files.f)，测试平台不加入生产源码清单。
仿真开启 `TUBE`，ROM/RAM 各 1024 个 16 位字。时钟为 1 MHz，UART 为
62500 波特、8N1，每位保持 16 拍；这些参数用于加快仿真，不修改板级默认参数。

驱动先保持外部 `rst_n=0`，等待 UART 上电复位结束，再从真实 RX 引脚逐帧发送
高字节、低字节。完整接收后逐字读回 ROM 校验，随后释放 CPU 复位，从 PC=0 执行。
驱动不直接写入内部数组，也不访问实际串口设备。默认示例完成时 RAM[0] 为 `0xabcc`。

## 自定义镜像与波形

镜像格式与 IDE 一致：每个非空行是一个 16 位二进制字，最多 1024 字。
可运行汇编器或编译器生成的镜像；以下从仓库根目录开始：

```bash
cd software
python3 -m opencpu compile examples/functions.oc -o /tmp/functions.bin
cd ..
make -C hardware/common/tb run IMAGE=/tmp/functions.bin TRACE=build/functions.vcd MAX_CYCLES=10000
```

`IMAGE`、`TRACE` 的相对路径以 `hardware/common/tb` 为基准；省略 `TRACE` 时不生成波形。
`MAX_CYCLES` 限制释放外部复位后的执行时钟数，不包含上传镜像的时间。
HALT 后驱动继续提供时钟，等待已排队的 UART TX 帧发送完毕再退出。
构建产物和示例波形保存在被 Git 忽略的 `build/` 中，`make -C hardware clean` 可清理。

需要指定输入引脚、接收字节或保留逐指令记录时，可以直接使用可执行文件：

```bash
hardware/common/tb/build/obj_dir/Vtb_soc \
  --image /tmp/functions.bin --max-cycles 10000 \
  --buttons 0x3 --switches 0xc \
  --retire-log /tmp/retirement.jsonl --trace /tmp/functions.vcd
```

重复传入 `--rx-byte 0xa5` 可发送多个运行态 RX 字节；第一帧从释放复位后的第 64 拍开始，
相邻帧之间额外空闲一位。程序需要轮询 UART 或启用接收中断来消费这些字节。
`--buttons`、`--switches` 默认分别为 `0xa`、`0x5`，合法范围为 0..15。
这些额外参数也可通过 Makefile 的 `ARGS='--rx-byte 0xa5'` 传递。

驱动 stdout 输出一个 JSON 对象，包含 HALT/fault 状态、架构 PC、执行周期数、
全部寄存器、六个可写 CSR、非零 RAM 字、解码后的 TX 字节及显示/GPIO 状态。
`pc` 是最后退休后的架构下一地址，fault 时为故障地址。
CSR 数组按 mtvec、mcause、mepc、mie、mstatus、mscratch 排列。
退休日志每行一个 JSON：PC、机器字、next_pc、IRQ/ack 在上升沿前采样，
寄存器、CSR、中断状态和 cycle 在该上升沿之后记录。

| 退出码 | 含义 |
|---|---|
| 0 | 执行 HALT |
| 1 | 参数、镜像、输出文件或仿真平台错误，包括 UART 上传校验失败 |
| 2 | CPU fault；JSON 给出 fault_code、fault_pc、fault_inst |
| 3 | 达到执行周期上限，尚未 HALT/fault |

通过 make 调用时，非零驱动退出码会使目标失败；需要区分具体状态时直接调用可执行文件。

## 自动自检范围

`make -C hardware test` 执行 9 项自检，包括三个现有示例和四种非法编码子用例：

- 纯 ISA 程序逐退休比较 PC、机器字、全部寄存器、六个可写 CSR、中断状态和最终 RAM；
  覆盖常数、算术/移位、分支冲刷、负访存偏移、函数调用和递归。
- GPIO 读写与低有效 LED、数码管读回及引脚编码、UART TX 的真实引脚解码，以及 HALT 后排空发送队列。
- 运行态 UART RX 中断、Timer 单次到期和 elapsed 清除，以及 IRQ 确认、MRET 返回。
- 非法编码、取指越界和无限循环超时，检查故障信息和对应退出码。

周期 CSR 在 RTL 中按物理时钟计数，软件模型按执行步骤计数，因此不要求二者逐值相等。
`make -C hardware lint` 另外检查默认、显示开启、UART/Timer 禁用和小存储配置。
`uart.v` 合并保存 UART 及 RX/TX 子模块，因此构建关闭 `DECLFILENAME` 告警；
其余过滤针对有意未用的调试信号、空端口和现有板级 `switch` 名称，其他 lint 告警仍视为失败。
