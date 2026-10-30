# OpenCPU 软件

极简编译器与原生 LLVM 工具链共用 ISA v2、汇编器、镜像格式、模拟器、IDE 和下载器：

| 后端 | 输入 | 实现 |
|---|---|---|
| `simple` | `.oc` 极简整数语言 | `opencpu/core/compiler/simple` 中独立的 Python 词法、语法和代码生成 |
| `llvm` | C17 `.c` 或 LLVM IR `.ll` | fork 中的 Clang 和 OpenCPU 后端；`opencpu/core/compiler/llvm` 中的 Python 进程适配层 |

C 使用裸机整数模型：char 为 8 位，short/int/数据指针为 16 位，long 为 32 位，long long 为 64 位。
支持 RAM 指针、数组动态下标、全局变量、字符串、直接调用、递归及多 C 文件。
结构体、联合体、位域、函数指针、浮点、VLA、可变参数、原子操作、C++ 和完整 libc 留待后续。
类型、寄存器、字节地址和 MMIO 接口见 [ABI](../docs/ABI.md)。CLI 不依赖 Qt；极简编译不导入或启动 LLVM。

## 创建环境和运行

使用 Python 3.10 或更新版本。在本目录执行，Linux/macOS：

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui]'
.venv/bin/python ide.py
.venv/bin/python downloader.py
```

Windows PowerShell：

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[gui]'
.\.venv\Scripts\python.exe ide.py
.\.venv\Scripts\python.exe downloader.py
```

两个窗口共用一个环境，IDE 的 **Tools > Downloader** 可打开独立下载器。
安装后可使用 `opencpu`、`opencpu-ide`、`opencpu-downloader` 命令。GUI 需要桌面或容器显示转发。
Ubuntu/Debian 的系统依赖：

```bash
sudo apt-get install python3-venv libgl1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
```

仅使用命令行时，执行 `python -m pip install -e .`，无需 GUI 可选依赖。

## 汇编、编译和模拟

在本目录执行：

```bash
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/isa.bin
python3 -m opencpu compile examples/simple/functions.oc -o /tmp/functions.bin --assembly /tmp/functions.asm
python3 -m opencpu run /tmp/functions.bin
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
```

极简语言支持 16 位整数、比较、控制流、最多四参数函数和返回值，局部变量初始为零。
`print`、浮点、除法和取模会报错；`.oc` 保持该编译器。

从仓库根目录执行 `python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test`
构建真实工具后，在本目录执行：

```bash
python3 -m opencpu compile examples/llvm/factorial.ll -o /tmp/ir.bin
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin --assembly /tmp/c.asm
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu run /tmp/project.bin
```

`.c`、`.ll` 自动选择 LLVM；也可显式指定 `--backend simple|llvm`。
`--language c|llvm-ir` 覆盖 LLVM 的输入语言识别。多个 C 文件可直接列出，`-I/-D` 可以重复：

```bash
python3 -m opencpu compile main.c math.c -I include -D FEATURE=1 -o /tmp/app.bin
```

原生链路调用 Clang `--target=opencpu-unknown-none`、`llvm-link` 和 `llc -march=opencpu -O0`。
C17 freestanding 模式关闭宿主系统头文件，保留 Clang 资源头文件和 SDK 的 `opencpu.h/string.h`。
入口使用 `int main(void)` 并显式返回结果。Python 不解析或翻译 C、LLVM IR。

工具必须为 OpenCPU LLVM 23.1.4，路径优先级为 `--llvm-bin-dir`、`OPENCPU_LLVM_BIN_DIR`、
本仓 `build/llvm/bin`。SDK 位于相邻的 `lib/opencpu/`；C 需要 Clang、资源头文件、llvm-link 和
运行库 bitcode，只有 `.ll` 的环境可省略 Clang。详见 [构建说明](../toolchain/llvm/README.md)。

镜像仍为每非空行一个 16 位字的文本，UART 每字高字节先发送；`--pad-rom` 用 HALT 补齐 1024 字 ROM。
RAM 同为 1024 字，C 的全局变量、字符串和栈共享其 2048 字节；运行库和静态初始化代码也占 ROM。
超容量镜像会报错。下载器处理统一镜像，不依赖 LLVM。

## 多文件 C 项目

`.opencpu.json` 中的路径相对清单文件所在目录解析：

```json
{
  "version": 1,
  "sources": ["main.c", "math.c"],
  "include_dirs": ["include"],
  "defines": ["FEATURE=1"]
}
```

`sources` 是有序且非空的 `.c` 文件列表；头文件目录和宏可省略。宏使用 `NAME` 或 `NAME=value`。
各 C 文件独立编译后在 bitcode 层合并，缺失符号和重复定义会报错。本轮不混合链接 `.oc` 函数。

## IDE 构建和执行

打开 `.c/.ll` 自动选择 LLVM C/IR，`.oc` 保持 Simple。
使用 **Tools > Compiler backend**、**Tools > LLVM input language** 切换当前文档设置；
**Tools > LLVM tool directory...** 选择其他工具目录。
`.asm/.s` 汇编与 `.bin` 镜像保留直接构建路径。

通过 **File > Open C project...** 打开清单，**File > Close C project** 解除项目关联。
构建以 Clang VFS overlay 捕获已打开 C 文件和头文件的未保存内容，不覆盖磁盘文件。
清单自身的修改需要先保存。已打开的项目头文件可以构建所属项目，独立头文件不能直接运行。

LLVM 在工作线程中编译，**Stop** 取消整条工具链；编辑、切页、关闭、语言或工具切换，以及依赖变化
都会使结果失效。IDE 监视源码、头文件和配置，并在运行、下载前复核文件指纹。
迟到结果不能覆盖新构建。关闭窗口时取消编译，并异步等待线程结束；窗口布局、工具栏和图标保持。

Run 分批执行，Run step、Run undo 逐指令操作。LLVM 从 `entry_pc=0` 初始化 RAM，调用 `main`，返回后 HALT。
每次 Run 对 C 提供 200000 条指令预算，其他输入保留 10000 条；达到上限时暂停并显示具体步数，
再次 Run 从当前指令继续。执行每 64 条指令让出事件循环，Stop 始终可用。
Save 使用完整文档路径，Save As 更新后续保存目标。

## Python 接口

`Toolchain.compile(source)` 仍使用独立极简版。原生编译示例：

```python
from opencpu.core.toolchain import Toolchain
from opencpu.core.compiler.llvm import CProject

build = Toolchain().compile("int main(void) { return 42; }", backend="llvm", language="c")
project = CProject.load("example.opencpu.json")
build = Toolchain().compile_project(project, buffers={})
```

`compile` 接受 `source_name`、`language="auto"`、`include_dirs`、`defines`、`llvm_bin_dir`、
`cancel_event` 和 `timeout`（默认 60 秒）。auto 根据名称选择 C/IR，LLVM 无名称时仍按 IR 处理。
`compile_project` 接受以文件路径为键的 buffer 覆盖，以及同样的工具目录、取消和超时选项。
整次构建共用一个超时预算，取消时终止子进程。

`BuildResult` 保留旧构造字段，增加有默认值的 `language`、`abi_version`、`dependencies`、
`dependency_hashes`、`data_size_bytes`。原生 ABI 为 `llvm-v2`；data size 为含保留两字节的静态区结束地址。
`source_map` 仍对应生成汇编行；原生 `variable_offsets` 为空，不伪造 C/IR 源码调试映射。
原有 `Compiler`、`CompileError`、`LanguageError` 导入保持兼容。

## 软件仿真

共用模型已包含 GPIO/显示、UART FIFO、Timer 中断、有界撤销、PC 断点和 JSONL 跟踪。
IDE 使用 **Tools > Simulation...** 操作虚拟外设，**Run > PC breakpoints** 管理断点。
命令行选项、示例及抽象 tick 约定见[模拟器说明](../docs/Simulator.md)。

## 验证

从仓库根目录执行；宿主与 GUI 测试不需要构建原生 LLVM：

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_services.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_gui.py -v
make -C hardware all
```

实际构建工具后，再执行：

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_native_gui.py -v
make -C hardware test-llvm
```

显式原生测试缺少工具时失败，不以跳过作为通过。用例核对整数和指针、多文件调用、数据初始化、
HALT、SP/FP 恢复及独立预期结果，再与真实 UART 上传后的 RTL 对照。
参见 [示例](examples/README.md)、[ISA](../docs/ISA.md)和[硬件说明](../hardware/README.md)。
