# OpenCPU 软件

两套编译器共用 ISA v2、汇编器、镜像格式、模拟器、IDE 和下载器：

| 后端 | 输入 | 实现 |
|---|---|---|
| `simple`（默认） | `.oc` 极简整数语言 | `opencpu/core/compiler/simple` 中的 Python 词法、语法和代码生成 |
| `llvm` | 受限 `i16` LLVM IR，`.ll` | LLVM fork 中真实的 C++/TableGen/SelectionDAG 后端；`opencpu/core/compiler/llvm` 中的 Python 代码负责进程适配 |

首版不包含 Clang/C、ELF/链接器和通用指针 ABI。支持操作与栈地址限制见 [ABI](../docs/ABI.md)。
核心工具链和 CLI 不依赖 Qt；使用极简版时不查找、不启动 LLVM。

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

两个窗口共用一个环境。IDE 的 **Tools > Downloader** 也能打开独立下载器。
安装后可使用 `opencpu`、`opencpu-ide` 和 `opencpu-downloader` 命令。
GUI 需要桌面显示服务，容器需要显示转发。Ubuntu/Debian 的 GUI 系统依赖：

```bash
sudo apt-get install python3-venv libgl1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
```

只使用命令行时，执行 `python -m pip install -e .` 即可，无需 GUI 可选依赖。

## 构建和模拟

在本目录执行：

```bash
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/isa.bin
python3 -m opencpu compile examples/simple/functions.oc --backend simple -o /tmp/functions.bin --assembly /tmp/functions.asm
python3 -m opencpu run /tmp/functions.bin
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
```

极简语言支持 16 位整数表达式、比较、控制流、最多四参数函数和返回值。
变量属于函数局部作用域，未赋值局部变量初始为零；`print`、浮点、除法和取模会明确报错。
省略 `--backend` 保持原有极简编译行为。

从仓库根目录执行 `python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test`
构建 LLVM 后，回到本目录运行：

```bash
python3 -m opencpu compile examples/llvm/factorial.ll --backend llvm -o /tmp/factorial.bin --assembly /tmp/factorial.asm
python3 -m opencpu run /tmp/factorial.bin
```

预期返回 `a1=120`，随后 HALT。LLVM 路径调用真实的 `llc -march=opencpu -O0`；
不支持的 IR 由原生后端诊断，Python 不解释或翻译 IR。
工具必须是带有 OpenCPU target 的 LLVM 23.1.4。路径依次取 `--llvm-bin-dir`、
`OPENCPU_LLVM_BIN_DIR`、仓库内 `build/llvm/bin`。源码初始化、构建参数和本地 fork
改动的发布顺序见 [LLVM 构建说明](../toolchain/llvm/README.md)。

`.bin` 为每个非空行一个 16 位字的文本；UART 按每字高字节、低字节发送。
`--pad-rom` 用 HALT 补齐默认 1024 字镜像。两条编译链共用该格式，下载器不依赖 LLVM。

## IDE 后端选择

打开 `.ll` 自动选择 LLVM；其他源码默认 Simple。在
**Tools > Compiler backend > Simple (.oc) / LLVM IR (.ll)** 中切换当前文档的后端。
`.asm`/`.s` 汇编和 `.bin` 镜像保留直接构建路径。

LLVM 在工作线程中编译，**Stop** 可以取消外部进程；编辑、切页、关闭文档或切换后端会使请求失效。
迟到的结果不会覆盖新构建或允许下载旧镜像。关闭 IDE 时会取消工作，并在后台结束后完成关闭。
窗口布局、工具栏和图标保持原样。

Run 分批执行，Run step、Run undo 逐指令操作。执行从构建产物的 `entry_pc`（零）开始，
包括 LLVM 的启动汇编，再进入 `main`。Save 使用完整文档路径，Save As 更新后续保存目标。

## Python 构建接口

`Toolchain.compile(source)` 仍走极简版；新增可选关键字 `backend`、`source_name`、
`llvm_bin_dir`、`cancel_event` 和 `timeout`（默认 60 秒）。
`BuildResult` 增加 `backend`、`isa_version`、`entry_pc`；`source_map` 仍表示每个机器字对应的
生成汇编的 1-based 行号。LLVM 的 `variable_offsets` 为空，不伪造变量栈槽或源码级调试能力。
原有 `Compiler`、`CompileError`、`LanguageError` 包导入入口继续可用。

## 验证

从仓库根目录运行宿主测试，包含 offscreen GUI 回归：

```bash
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s software/tests -v
make -C hardware all
```

默认硬件回归不需要 LLVM。实际构建原生后端后，再运行：

```bash
python3 -B -m unittest discover -s software/tests/native -v
make -C hardware test-llvm
```

显式 native/LLVM 验收在工具缺失时失败；通过独立预期结果与真实 UART 上传后的 RTL 进行对照。
示例见 [examples](examples/README.md)，指令行为见 [ISA](../docs/ISA.md)，
硬件命令见 [硬件说明](../hardware/README.md)。
