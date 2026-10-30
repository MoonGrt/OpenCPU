# OpenCPU C 支持验证记录

验证日期：2026-10-30。使用本仓实际构建的 Clang/LLVM 23.1.4，启用 assertions；
使用 Python 3.10、PyQt5 5.15.11 和 Verilator 4.216。所有原生检查都要求工具存在，未跳过用例。

本次源码在主仓 `d3df811`、LLVM fork `f6f1dbc2c07b` 的工作区上实现，尚未提交或发布。
本记录对应工作区的 LLVM ABI v2；原提交本身不包含此次 C 支持。

## 可重复运行的检查

从主仓根目录运行：

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
build/llvm/bin/llvm-lit -v thirdpartys/llvm-project/clang/test/Preprocessor/opencpu.c thirdpartys/llvm-project/clang/test/CodeGen/opencpu.c
cmake --build build/llvm --target TargetParserTests --parallel 2
build/llvm/unittests/TargetParser/TargetParserTests --gtest_filter='TripleTest.*'
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_services.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_gui.py -v
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_native_gui.py -v
make -C hardware all
make -C hardware test-llvm
```

GUI 检查需要安装 `software` 的 `gui` 可选依赖。服务及 GUI 流程测试使用受控工具验证错误、
取消与生命周期；两个 `native` 入口和 UART 验收均使用真实 Clang、llc 和运行库。

## 结果

| 检查 | 结果与覆盖 |
|---|---|
| LLVM CodeGen | 8 项通过，覆盖 ABI、字节/全局数据、ZERO、volatile 与拒绝项 |
| Clang | 2 项通过，验证目标宏、整数/指针宽度、对齐、参数返回及 MMIO builtin |
| Triple | 30 项通过，包含 OpenCPU 解析、16 位指针、小端布局和无异常处理约定 |
| Python 服务 | 25 项通过，覆盖项目清单、VFS、依赖变化、容量、工具错误、超时和取消 |
| GUI 流程 | 15 项通过，覆盖项目快照、语言选择、迟到结果、磁盘变化和运行预算 |
| 原生 C/IR | 12 个测试方法通过，含 14 个 C 示例、195 个整数程序、额外宽 ABI 用例与 16 个原有 IR 示例 |
| 真实 GUI | 3 项通过，真实阶乘返回 120，多文件未保存源码/头文件返回独立预期 26，文本文件显式 C 返回 42 |
| 默认 RTL | lint 和 9 项整机回归通过 |
| C/IR UART/RTL | 5 个测试方法通过，以上 C/IR 程序经 UART 引脚上传并逐退休、完整 RAM 对照 |

原生检查同时验证入口为零、静态数据初始化、HALT、SP=1024、FP=0，及 ROM/RAM 容量错误。
栈耗尽在写坏静态区之前故障，软件与 RTL 中的 `0x5aa5` 哨兵均保持不变。
三个旧极简示例的完整机器码与实现 C 支持前逐字一致。

另做了启用 `-verify-machineinstrs` 的 52 组整数 IR、4 组扩展 ABI 和 102 组 64 位除余边界检查，
全部通过。有符号 64 位除余探针的镜像约 818/811 字，边界探针最大 824 字。
运行库的 4400 组独立算法验算也通过；这些额外检查不替代上述永久原生验收。

安装包已构建为 wheel，并在仓库外通过显式 LLVM 工具目录运行真实 C 程序得到 42；
同一安装包的极简编译器独立可用。

## 验证范围

支持范围及调用约定见 [ABI](../../docs/ABI.md)，构建方式见 [LLVM 指南](README.md)。
本轮验证的是整数型 C17 裸机子集，不包含结构体、联合体、位域、函数指针、浮点、VLA、
可变参数、原子操作、线程、内联汇编、完整 libc 或 C++。

UART/RTL 检查使用真实 Verilog 顶层的 Verilator 仿真，尚未代替实际 FPGA 板上的综合与运行验证。
