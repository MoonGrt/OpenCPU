**简体中文 | [English](README.md)**

# OpenCPU

OpenCPU 是面向 FPGA 的 16 位 CPU 项目，包含 Verilog 硬件、统一的 ISA v2 工具链、
图形 IDE、独立串口下载器和 Verilator 整机仿真。可以从源码编写程序，完成汇编或编译，
在软件模型中运行，再通过 UART 装载到 RTL 仿真或开发板。

## 项目概览

| 部分 | 当前实现 |
|---|---|
| 指令集 | 自定义 ISA v2，16 位定长指令，数据和地址均以 16 位字为单位 |
| 寄存器 | 8 个 16 位寄存器；`zero=r0`、`fp=r5`、`ra=r6`、`sp=r7` |
| CPU | F 取指、D 缓存、X 执行与提交的三级顺序核，独立指令与数据通道 |
| 存储 | 默认 ROM/RAM 各 1024 字，异步读、时钟上升沿写 |
| 中断 | CSR 配置、外设 pending、IRQ 确认与 `MRET` 返回 |
| 外设 | GPIO、UART、Timer 和四位十六进制数码管 |
| 软件 | 汇编、反汇编、极简 `.oc` 与原生 Clang C17/LLVM IR、模拟器、Qt IDE 和独立下载器 |
| 验证 | 真实 UART 引脚上传、逐指令模型对照、MMIO 和中断自检、VCD 波形 |

算术寄存器指令原地更新目的寄存器；算术立即数和访存偏移支持负数，跳转以 `PC+1` 为基准。
汇编器支持标签，自动展开完整 16 位常量及远距离分支、调用。
完整编码和行为以 [ISA 规范](docs/ISA.md) 为准。

## 文档导航

| 内容 | 文档 |
|---|---|
| 指令编码、寄存器、内存与中断约定 | [ISA v2](docs/ISA.md) |
| RTL 结构、板级接口、MMIO 和下载流程 | [硬件说明](hardware/README.md) |
| Verilator 构建、自检、自定义镜像与波形 | [仿真说明](hardware/common/tb/README.md) |
| 仿真器、编译器和 UART/RTL 随机压力测试 | [压力测试与结果](docs/StressTesting.md) |
| 虚拟环境、IDE、独立下载器和命令行 | [软件说明](software/README_cn.md) |
| 原生 Clang/LLVM 构建与 ABI | [LLVM 说明](toolchain/llvm/README.md)、[ABI](docs/ABI.md) |
| 可重新构建的源码示例与预期结果 | [示例程序](software/examples/README.md) |
| 早期 Logisim 电路 | [历史参考](docs/ref/logisim/README.md) |

## 快速开始

以下每组命令均以仓库根目录为起点。软件需要 **Python 3.10 或更新版本**。

### 命令行：汇编、编译和模拟

进入 `software` 后即可运行工具链，无需安装 Qt 或第三方 Python 依赖：

```bash
cd software
python3 -m opencpu --help
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/opencpu-isa.bin
python3 -m opencpu run /tmp/opencpu-isa.bin
python3 -m opencpu compile examples/simple/functions.oc -o /tmp/opencpu-functions.bin
python3 -m opencpu run /tmp/opencpu-functions.bin
python3 -m opencpu disassemble /tmp/opencpu-isa.bin -o /tmp/opencpu-isa.dis.asm
```

以上示例使用 Linux/macOS 临时路径；其他系统可替换为可写路径。
`assemble` 接收汇编，`compile` 接收 `.oc`、C 或 LLVM IR，`run` 执行机器码，`disassemble` 输出汇编。
`.bin` 是文本文件，每个非空行包含一个 16 位二进制字。

| 示例 | 预期结果 |
|---|---|
| [isa.asm](software/examples/simple/isa.asm) | RAM 字地址 0 为 `0xabcc`（43980），随后 HALT |
| [loops.oc](software/examples/simple/loops.oc) | `X=15`、`Y=11`、`i=3` |
| [functions.oc](software/examples/simple/functions.oc) | 递归计算 `factorial(5)`，`result=120` |

极简编译器支持整数赋值、算术与位运算、比较、`if`、`while`、`for`、最多四参数的函数和 `return`。
`print`、浮点数、除法和取模会明确报错。编译器生成的局部变量位于 RAM，
具体存储位置见[示例说明](software/examples/README.md)。

### 原生 C 与 LLVM IR 编译器（可选）

`.oc` 保持极简编译器，原生链路同时接受 C17 `.c` 和 `.ll`，通过真正的 OpenCPU Clang target、
bitcode 合并和 SelectionDAG 后端生成汇编，再复用当前汇编器生成镜像。
C 支持至 64 位的整数、RAM 指针、数组、全局变量、字符串、直接调用和多源文件；结构体、联合体、
函数指针、浮点及完整 libc 留待后续。详见 [构建说明](toolchain/llvm/README.md)和 [ABI v2](docs/ABI.md)。

从仓库根目录、具备 fork 中 OpenCPU 实现的工作区执行：

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
cd software
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu compile examples/llvm/factorial.ll -o /tmp/factorial.bin
python3 -m opencpu run /tmp/factorial.bin
```

IR 阶乘示例返回 `a1=120`，随后 HALT。工具固定为 LLVM 23.1.4，位于 `build/llvm/bin`；
`--llvm-bin-dir` 或 `OPENCPU_LLVM_BIN_DIR` 可选择其他构建，SDK 位于相邻 `lib/opencpu/`。
极简版无需 LLVM；`--ir-only` 构建可省略 Clang。镜像仍限 1024 字 ROM，C 静态数据与栈共用 2048 字节 RAM。

IDE 打开 `.c/.ll` 自动选择 LLVM C/IR；**File > Open C project...** 加载多文件清单，
**Tools > LLVM input language** 切换语言。后台构建使用 C/头文件未保存内容；Stop、编辑和依赖变化
使陈旧结果失效，禁止运行或下载旧镜像。窗口布局保持。

### 图形 IDE 与独立下载器

Linux/macOS 下，从仓库根目录创建共享虚拟环境：

```bash
cd software
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui]'
.venv/bin/python ide.py
```

退出 IDE 后，在同一目录可单独启动下载器：

```bash
.venv/bin/python downloader.py
```

IDE 中的 **Tools > Downloader** 也可打开下载器，两者共用工具链和串口服务。
Windows PowerShell 命令、Qt 系统依赖及容器显示要求见[软件说明](software/README_cn.md)。
安装后还可通过虚拟环境中的 `opencpu`、`opencpu-ide`、`opencpu-downloader` 命令启动。

## 硬件仿真与检查

需要 **Verilator、g++、GNU make 和 Python 3.10+**；GTKWave 用于查看波形，可按需安装。
从仓库根目录执行：

```bash
make -C hardware lint
make -C hardware test
make -C hardware run TRACE=build/wave.vcd
gtkwave hardware/common/tb/build/wave.vcd
```

`lint` 检查默认、显示开启、UART/Timer 禁用和小存储四种配置。
`test` 构建并执行 9 项整机自检，覆盖现有示例、逐指令状态对照、访存与分支、GPIO/显示、
UART 收发、Timer 中断、`MRET`、非法指令、取指越界和超时。
默认 `make -C hardware all` 不依赖 LLVM；构建 LLVM 后可运行 `make -C hardware test-llvm` 验证其产物。
`run` 默认汇编 `software/examples/simple/isa.asm`，从真实 UART RX 引脚上传镜像，再释放复位运行到 HALT。

仿真使用 1 MHz 时钟和 62500 波特率，每位 16 拍，以缩短运行时间；板级默认参数为
27 MHz 和 115200 波特。仿真不会连接实际串口设备，遇到 fault 或超过周期上限会以非零状态退出。
构建与示例波形位于 `hardware/common/tb/build/`，可用 `make -C hardware clean` 清理。
自定义镜像、运行周期限制和退休日志见[仿真说明](hardware/common/tb/README.md)。

[软件模拟器](docs/Simulator.md) 已支持 GPIO、显示、UART FIFO、Timer 和外设中断，
提供虚拟输入、PC 断点与执行跟踪。软件 tick 为抽象时间，精确物理时钟和引脚波形使用整机 RTL 验证。

## 下载到开发板

板级默认串口格式为 **115200、8 数据位、无校验、1 停止位（8N1）**，需与实际 RTL 参数匹配。

1. 构建完整镜像。在仓库根目录执行：

   ```bash
   cd software
   python3 -m opencpu assemble examples/simple/isa.asm --pad-rom -o /tmp/opencpu.bin
   ```

2. 将开发板外部 `rst_n` 保持为低，用独立下载器打开镜像，通过匹配的串口配置发送。
3. 等待最后一个完整 UART 帧发送完毕，再释放复位。CPU 从字地址 0 开始执行。

软件不会自动切换开发板上的 CPU 复位。镜像按每字高字节、低字节顺序发送；
`--pad-rom` 用 HALT 补齐到 1024 字，覆盖旧程序尾部。详细装载规则见[硬件说明](hardware/README.md)。

## 仓库结构

```text
OpenCPU/
├─ .devcontainer/                 开发容器配置
├─ docs/
│  ├─ ABI.md                      LLVM 子集与调用约定
│  ├─ ISA.md                      当前指令集规范
│  ├─ images/block_diagram.png    早期设计框图
│  └─ ref/logisim/                早期电路参考
├─ hardware/
│  ├─ verilog/
│  │  ├─ core/                    CPU、译码、执行、寄存器、CSR
│  │  ├─ include/isa.vh           硬件指令编码
│  │  ├─ memory/                  RAM、ROM 与镜像装载
│  │  ├─ peripherals/             GPIO、UART、Timer、显示
│  │  ├─ soc/                     连接、复位与中断 pending
│  │  ├─ files.f                  生产 RTL 源码清单
│  │  └─ top.v                    板级入口
│  ├─ common/tb/                  Verilator testbench、驱动、自检
│  ├─ Makefile
│  └─ README.md
├─ software/
│  ├─ opencpu/
│  │  ├─ core/                    ISA、工具链、编译器与模拟器
│  │  ├─ gui/                     IDE、下载器与资源
│  │  ├─ transport/               串口服务
│  │  └─ cli.py                   命令行入口
│  ├─ examples/
│  │  ├─ simple/                  汇编和极简 .oc 示例
│  │  ├─ llvm/                    原生 LLVM .ll 示例
│  │  └─ c/                       C17 与多文件项目
│  ├─ runtime/                    启动汇编、整数运行库和 SDK 头文件
│  ├─ ide.py
│  ├─ downloader.py
│  ├─ pyproject.toml
│  ├─ README.md
│  └─ README_cn.md
├─ toolchain/llvm/                 LLVM 构建、验收测试与说明
├─ thirdpartys/llvm-project/       LLVM fork 子模块及后端唯一源码
├─ LICENSE
├─ README.md
└─ README_cn.md
```

## 项目状态与历史资料

当前两套编译器和 RTL 统一采用 ISA v2，工作目录保留当前实现及可重新构建的源码示例。
原生后端在 LLVM fork 中开发；本地改动与子仓发布顺序见 [LLVM 说明](toolchain/llvm/README.md)。
旧版操作码、寄存器别名和分支编码与现行 ISA 不兼容；旧程序应依据当前规范从源码重新汇编或编译。

已移除的图片和旧代码可从 Git 历史查看；剩余框图和 Logisim 电路用于了解早期设计，
当前指令行为与接口以 ISA 规范和现行 RTL 为准。
仓库当前没有板卡工程、管脚或时序约束，仿真通过不代表已完成目标器件的综合、布局布线及实板验证。

## 贡献与许可证

欢迎通过 [Issue](https://github.com/MoonGrt/OpenCPU/issues) 反馈问题或提交 Pull Request。
修改 ISA 时请同步更新 RTL、软件工具链和规范，并执行 `make -C hardware all`。

主项目使用 [MIT 许可证](LICENSE)；LLVM 子模块及其中新增后端遵循其自身的
Apache-2.0 WITH LLVM-exception 许可证。作者：[MoonGrt](https://github.com/MoonGrt)，
联系邮箱：[1561145394@qq.com](mailto:1561145394@qq.com)。
