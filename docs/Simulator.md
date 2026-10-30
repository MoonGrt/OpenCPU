# 软件模拟器

IDE 和 CLI 共用指令级 `Simulator`。它执行 ISA v2，包含 RAM、CSR、GPIO、显示寄存器、
UART FIFO、Timer 和中断 pending，并支持单步、撤销、PC 断点及执行跟踪。
`.oc`、C 和 LLVM IR 编译后的镜像使用同一个模拟器。

## 时间和外设

每条成功执行的真实指令推进一个软件 tick；暂停、HALT 和 fault 后 CPU 不继续执行。
`advance_ticks(n)` 可以单独推进外设，周期 CSR 也随之推进，但退休指令数不增加。
这些 tick **不是 FPGA 时钟**，不对应三级流水线周期或真实波特率。
精确时钟、引脚波形和串口帧采样仍由 [Verilator 整机仿真](../hardware/common/tb/README.md) 验证。

寄存器地址按硬件的 16 位字计数，定义见 [MMIO 表](../hardware/README.md#mmio-寄存器)。

- GPIO 输入立即反映设定的低四位；LED 保存四位逻辑值，引脚值为其反相。
- 显示模型保存完整 16 位显示字，不生成数码管扫描波形。
- UART 默认 RX/TX FIFO 各 16 字节，读 DATA 出队、写 DATA 只发送低八位；空队列读零。
  状态包含 RX 非空、TX 可写、busy 和错误；满队列保留已有字节并置溢出，错误位写一清除。
- UART 默认每帧 10 个软件 tick；TX 完成后才进入输出日志。虚拟 RX 注入立即进入 FIFO，
  相应 IRQ 事件在下一 tick 锁存。一次注入超过 FIFO 容量会产生真实的模型溢出，建议分批发送。
  消费 RX 或清除设备状态不会自动清中断 pending，pending 由 CPU 实际接受中断时确认。
- Timer 周期单位为软件 tick。支持单次、周期模式、32 位周期/计数和 elapsed 写一清除。
  写 period/control 会清计数并跳过本 tick 的计数；同 tick 到期优先于 elapsed 清除。
- Timer 为 IRQ0，UART 有效接收为 IRQ1。事件在屏蔽期间锁存、同源合并；最低有效位优先。
  CPU 先根据提交后的 CSR 和已有 pending 判断 IRQ，再锁存本 tick 的新事件，新事件不会被同拍确认清掉。

保留地址及只读寄存器的写入被忽略。整个 `0xff00..0xffff` 页属于外设，未定义偏移读零。
`data_mem` 只包含 RAM；外设状态独立导出。软件模型默认启用 UART、Timer 和显示，
可在构造 `PeripheralModel` 或 CLI 参数中关闭它们。

## 命令行

从仓库根目录开始：

```bash
cd software
python3 -m opencpu assemble examples/simple/uart_echo.asm -o /tmp/echo.bin
python3 -m opencpu run /tmp/echo.bin --uart-rx-hex "41 00 ff" --trace /tmp/echo.jsonl
```

预期 `uart_tx` 为 `[65, 0, 255]`，HALT 后自动推进至已经排队的 TX 发完。
JSON 同时包含寄存器、RAM、外设快照、停止原因、结构化故障和 TX 文本。
`ticks` 为累计软件时间，`cycle` 为按 32 位回绕的 CSR 计数；跟踪文件每行对应一条实际退休指令。

其他操作：

```bash
python3 -m opencpu run /tmp/echo.bin --uart-rx OK! --buttons 0x3 --switches 0xc
python3 -m opencpu run /tmp/echo.bin --breakpoint 0 --trace /tmp/before.jsonl
python3 -m opencpu run /tmp/echo.bin --uart-rx-hex "41 00 ff" --drain-ticks 20
python3 -m opencpu run /tmp/echo.bin --disable-uart --disable-timer --disable-display --max-steps 100
python3 -m opencpu assemble examples/simple/timer_irq.asm -o /tmp/timer.bin
python3 -m opencpu run /tmp/timer.bin
```

Timer 示例在 ISR 将 RAM 字 0 写为 1、清除 elapsed、通过 MRET 返回，然后 HALT。
`--uart-rx` 按 UTF-8 编码；`--uart-rx-hex` 支持原始二进制字节，二者互斥。
`--uart-frame-ticks N` 调整抽象发送时长。`--drain-ticks N` 显式推进外设，覆盖 HALT 后自动排空策略；
断点、故障和指令上限默认不会自动推进外设。
`--breakpoint` 可重复，地址为 ROM 字地址 `0..1023`。正常 HALT 或断点退出码为 0，fault 为 2，指令上限为 3。

## IDE 调试

1. 打开程序并 Assemble；使用原有 Run、Run step、Run undo、Stop 和 Reset。
2. **Run → PC breakpoints** 设置字地址断点；F9 切换当前 PC。断点在指令执行前停止，
   再点 Run 继续，Step 执行该条指令；循环再次到达断点会再次停止。
3. **Tools → Simulation...** 打开独立窗口，调整按键/开关，观察 LED、显示字、UART 状态和 Timer。
   使用 Text/Hex 注入虚拟 RX，也可模拟坏帧；TX 终端同时显示文本和十六进制。
4. HALT 后使用 **Advance ticks** 排空串口或观察 Timer。运行期间配置控件禁用，Stop 后可操作。

模拟串口不使用真实串口连接。查看状态通过无副作用的 peek/snapshot，不会消费 RX。
主窗口布局保持；TX 终端只显示最近 4096 字节，避免长日志拖慢窗口。

## 撤销、故障和 API

默认保留最近 10000 个可撤销事件；`history_limit=None` 显式无限保留，`0` 完全关闭记录。
CLI 使用 `0`，避免批量执行保留无用快照。撤销恢复寄存器、RAM、CSR、PC、Timer、FIFO、IRQ 和 TX 输出长度；
虚拟输入、显式设备读取与空闲时间推进也可以撤销。达到历史上限后，只能退回仍保留的部分。

非法指令和取指失败本身可以撤销，不会跳过上一条有效指令。
`fault_code=1` 表示非法编码，`2` 表示取指失败；后者的 `fault_inst=None`。
`fault_pc` 和 `fault_reason` 给出位置与原因。故障不计为退休指令，也不产生跟踪记录。

```python
from opencpu.core.simulator import Simulator

model = Simulator(history_limit=10000)
model.inst_mem = build.words
model.set_inputs(buttons=3, switches=12)
model.inject_uart(b"OK")
model.breakpoints = {build.entry_pc}
model.run(10000, trace=lambda record: print(record))
model.run_step()       # 单步忽略断点
model.run_undo()
model.peek_data(0xff40)  # 不弹出 UART RX
model.advance_ticks(20)
```

`last_retire` 包含 PC、机器字、下一 PC、寄存器、可写 CSR 和 IRQ 确认掩码；
`stop_reason` 区分 `halt/fault/breakpoint/limit/stopped`。Reset 保留镜像、断点及外部 GPIO 输入，
清空执行状态、历史、RAM 视图和内部外设状态。GPIO 同步器延迟、UART 引脚采样和数码管扫描不属于本模型。

## 检查

随机指令、撤销重放、外设批量推进和百万步历史内存检查见[压力测试](StressTesting.md)。

从仓库根目录运行，不需要构建 LLVM：

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_peripherals.py -v
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_simulator.py -v
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_simulator_cli.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_simulator_gui.py -v
make -C hardware test
```

外设测试覆盖 FIFO、W1C、IRQ 优先级、Timer 和撤销。整机测试同时比较稳定的寄存器/最终状态，
不要求软件 tick 与 RTL 物理时钟、忙等次数或中断发生的具体 PC 相等。

本轮通过 16 项外设、20 项核心、8 项 CLI、12 项新增 GUI 回归，以及原有 25 项服务、15 项 GUI、
3 项真实 Clang GUI、12 项原生 C/IR 测试方法和 9 项默认 RTL 回归。
完整 C/IR UART/RTL 对照同样通过，包含 14 个 C 示例、195 个整数程序及原有 LLVM 示例。
有界历史在累计执行 60000 条循环指令后仍只保留配置的 1000 条，没有随累计步数线性增长。
