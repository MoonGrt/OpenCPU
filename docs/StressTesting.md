# 仿真器、RTL 与编译器压力测试

压力测试使用固定随机种子和独立预期值，并保存生成源码、镜像、诊断和 RTL 退休记录。
软件模型之间的一致性检查之外，还分别检查 Python 计算的 ISA 或语言结果，避免把同一个错误当成预期。
这些测试位于 `toolchain/llvm/tests/stress_*.py`，不依赖已删除的 `software/tests`。

## 运行

从仓库根目录执行。完整批次需要实际构建的 OpenCPU Clang、llc、llvm-link、SDK 和 Verilator；
工具缺失会失败，不会通过跳过验收。已有构建可以直接运行压力入口。

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1
make -C hardware build
python3 -B toolchain/llvm/stress.py --profile quick
python3 -B toolchain/llvm/stress.py --profile full --seed 20261030
```

默认输出目录为 `build/stress/<UTC时间>/`，终端打印位置。可用 `--output build/stress/my-run` 指定；
每个组件有 `summary.json` 和 `runner.log`，根目录报告汇总组件状态、命令、种子及两仓 Git 状态。
生成文件受 Git 忽略；完整通过退出码为 0，功能失败、非预期资源限制或报告缺失返回非零。
相同输出目录会覆盖同名报告，需保留旧批次时使用新目录。

| 配置 | 模拟器 | RTL | 编译器 |
|---|---|---|---|
| quick | 每类 25 个随机案例，两个各 20000 条指令的长循环 | 8 个随机程序及 15 个外设案例 | Simple/C 各 8 个程序，各抽 3 个 UART/RTL 对照 |
| full | 每类 1000 个随机案例，两个各 100 万条指令的长循环 | 250 个随机程序及 15 个外设案例 | Simple 300 个、C 250 个，各抽 50 个 UART/RTL 对照 |

两个配置都额外检查编译器的六项预期资源拒绝；它们单独列出，不计入正常程序通过数。
可以通过 `--component simulator`、`rtl` 或 `compilers` 单独运行一个组件。
只运行软件模拟器无需 LLVM、Verilator 或 Qt。

提高规模时直接使用组件入口：

```bash
python3 -B toolchain/llvm/tests/stress_simulator.py --seed 20261031 --cases 2000 --steps 2000000 --output build/stress/custom/simulator
python3 -B toolchain/llvm/tests/stress_rtl.py --seed 20261031 --cases 1000 --output build/stress/custom/rtl
python3 -B toolchain/llvm/tests/stress_compilers.py --seed 20261031 --simple-cases 300 --c-cases 250 --rtl-cases 50 --output build/stress/custom/compilers
python3 -B toolchain/llvm/stress.py --collect-only --seed 20261031 --output build/stress/custom
```

`--collect-only` 只收集已有报告，检查种子和失败状态，不表示重新执行了测试。
编译器的 `--rtl-cases` 为**每套编译器**的抽样数；显式设为 0 仅用于软件检查。
如需选择另一个原生工具目录，设置 `OPENCPU_LLVM_BIN_DIR`；RTL 可用 `OPENCPU_SIM` 指定实际可执行文件。

## 覆盖与边界

- 模拟器：随机 ISA 逐退休预期；混合 CPU、IRQ、FIFO、Timer、MMIO 的撤销及重放；
  外设批量推进对逐 tick 推进；HALT、fault、Stop、断点与继续；关闭历史及保留 1000 项历史的长运行。
- RTL：镜像通过 UART 引脚上传到真实 Verilator SoC；随机程序逐退休比较 PC、寄存器、可写 CSR、IRQ 确认及最终完整 RAM，
  再检查独立预期。覆盖寄存器依赖、访存、移位边界、有符号与无符号比较、远近分支和调用、非法指令、取指越界与预期超时。
- 外设：TX burst/溢出与 W1C、RX FIFO 溢出和 IRQ 合并、Timer 单次/周期/合并及中断返回。
  软件 tick 与 RTL 时钟不同，外设案例检查稳定的结果和协议约束；不要求忙等次数或 IRQ 发生的具体 PC 相同。
- 编译器：真实 Simple 与 Clang/LLVM 链分别生成机器码，独立计算结果；覆盖嵌套表达式、循环、递归、远分支、大栈帧、
  调用期间活跃值、8/16/32/64 位整数、宽参数跨寄存器与栈、动态数组、奇偶字节写入、全局初始化、四种内存函数与多源文件。
  C 用例避免有符号溢出、除零、非法移位等未定义行为；C 返回后检查 SP=1024、FP=0。
- 资源：ROM/RAM 容量和 Simple 解析深度单独报告。随机有效程序被容量拒绝时不会算作通过，
  必须另生成有效程序达到请求数量，且各被拒绝类别仍须存在成功覆盖。

内存长跑使用 `tracemalloc`，比较预热后和结束时的 Python 保留分配，检查历史项数和内存阈值。
它不测操作系统 RSS；吞吐包含分配追踪与采样开销，只是本机观测值。
UART 完整输出日志有意保留，长跑使用无输出循环，内存结论针对执行历史。

## 复现

编译器每个案例保存 `case.json`、源码、独立预期、生成汇编和镜像；抽样案例还保存 RTL 状态及退休日志。
模拟器失败保存可重放的完整案例；RTL 的 `case.json` 记录预期和选项。

```bash
python3 -B toolchain/llvm/tests/stress_compilers.py --replay build/stress/latest/compilers/simple/00000-nested-expression --rtl-cases 1 --output build/stress/replay/compilers
python3 -B toolchain/llvm/tests/stress_rtl.py --seed 20261030 --cases 250 --case random-00022 --output build/stress/replay/rtl
```

模拟器出现失败时，将其报告中的 `replay` 路径传给 `stress_simulator.py --replay <路径>`。
RTL 重放需保留原始 `--seed` 和足以生成该编号的 `--cases`。

## 2026-10-30 验证记录

当前工作区使用实际 LLVM 23.1.4 OpenCPU 工具和 Verilator 4.216；两仓含未提交实现。
固定种子 `20261030` 的完整批次结果保存在本机 `build/stress/latest/summary.json`：

| 项目 | 实际结果 |
|---|---|
| 模拟器随机测试 | 4000 个案例，全部通过；ISA 对照 54554 条指令，撤销 20977 个事件，外设逐 tick 对照 262817 次 |
| 模拟器长跑 | 历史关闭/上限 1000，各执行 100 万条指令；各在预热后仅增加 608 字节保留分配 |
| 随机 RTL 与外设 | 265 个验证完成，零失败、零非预期资源限制；255 个通过含 20 个预期 fault，另 10 个预期 timeout |
| RTL 对照规模 | 上传 31134 个机器字，逐退休对照 35036 条，71 个远调用案例 |
| 编译器 | Simple 300/300、C 250/250 通过；各 50 个真实 UART/RTL 对照全部通过 |
| 编译器资源诊断 | 六项预期拒绝全部正确，随机有效程序无资源拒绝 |

发现并修复了 Simple 编译器对 1000/2000 项长表达式直接抛出 `RecursionError` 的问题：
现在返回 `CompileError`，CLI 给出明确深度限制诊断且不留下部分输出。
新增回归还覆盖 1100 层语句嵌套及失败后复用编译器；原有三个示例的机器码 SHA-256 保持一致。

为扩大数值组合，又运行了不同种子的批次，结果均为零失败：

| 种子 / 本机报告目录 | 模拟器随机案例 | RTL 验证 | 编译器程序 / UART 抽样 |
|---|---|---|---|
| `20261031` / `build/stress/secondary` | 每类 200 个，共 800 个，另两个短循环 | 1000 个随机 + 15 个外设 | Simple 140、C 170；各 10 个 UART |
| `20261032` / `build/stress/tertiary` | 本批未执行 | 本批未执行独立 RTL 组 | Simple 70、C 170；各 10 个 UART |

三轮合计 1100 个编译器程序、140 个编译器 UART/RTL 抽样全部通过；资源预期拒绝每轮六项。
两轮独立 RTL 组合计 1280 个验证完成，其中 50 个预期 timeout、100 个预期 fault；
无非预期资源限制。共上传 150965 个机器字，逐退休对照 174890 条。

统一 quick 入口通过。另执行全部 114 项软件测试方法（含实际 C/IR 和 Qt）、默认九项 RTL 回归和 lint、
五项原生 C/IR UART/RTL 测试方法，均通过。可重复执行这些回归：

```bash
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p 'test_*.py' -v
make -C hardware all
make -C hardware test-llvm
```

Qt 回归使用已安装软件 GUI 依赖的虚拟环境；压力入口本身不需要 Qt。
软件 tick、RTL 周期和上板运行属于不同验证层级；本记录中的 UART 验证发生在 Verilator 引脚模型，不表示物理 FPGA 上板测试。
