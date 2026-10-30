# OpenCPU 软件

IDE、独立下载器和命令行工具共用一套 ISA v2 实现。界面的菜单、工具栏、分隔窗格和图标保持原有样式；
核心代码不依赖 Qt。当前软件只保留最新代码，旧版本可从 Git 历史查看。

```text
software/
  ide.py / downloader.py       GUI 启动入口
  pyproject.toml               安装配置与 GUI 可选依赖
  opencpu/
    core/                      ISA、汇编、编译、模拟、镜像和统一工具链
    gui/                       窗口布局、控制器、文档和资源
    transport/                 串口配置与 Qt 传输服务
    cli.py                     命令行入口
  examples/                    当前可重新构建的源码示例
```

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
安装后可在任意目录使用 `opencpu-ide`、`opencpu-downloader` 和 `opencpu` 命令。
GUI 需要桌面显示服务，容器需要显示转发。

Ubuntu/Debian 的系统依赖：

```bash
sudo apt-get install python3-venv libgl1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
  libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 libxkbcommon-x11-0
```

只使用命令行时，用 `python -m pip install -e .` 安装即可，无需 `.[gui]`。
核心工具链和命令行都不会导入 GUI 库。

## 构建和模拟

在仓库根目录执行：

```bash
cd software
python3 -m opencpu assemble examples/isa.asm -o /tmp/isa.bin
python3 -m opencpu run /tmp/isa.bin
python3 -m opencpu compile examples/loops.oc -o /tmp/loops.bin --assembly /tmp/loops.asm
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
cd ..
```

`python3 -m opencpu` 在 `software` 目录中运行；末尾的 `cd ..` 返回仓库根目录。
`assemble`、`compile` 的 `--pad-rom` 参数会将镜像用 HALT 补齐到 1024 字，覆盖旧程序尾部。
`.bin` 是每行一个 16 位字的文本文件，下载按每字高字节、低字节顺序发送。

IDE 可编译整数源文件、汇编 `.asm`/`.s` 文件或加载二进制文本 `.bin` 文件。
Run 分批执行，Stop 可以在运行过程中响应；编辑源码后会使旧编译产物失效，防止误运行或误下载。
Save 使用每个文档的完整路径，Save As 更新后续保存目标；二进制文档保持二进制格式。

编译器支持 16 位整数表达式、控制流、最多四参数的函数和返回值。
变量属于各自函数的局部作用域，未赋值的局部变量初始为零；没有隐式全局变量。
`print`、浮点数、除法和取模会明确报错。详见[示例](examples/README.md)和[ISA 规范](../docs/ISA.md)。

## 软硬件对照验证

Verilator testbench 和回归位于 [hardware/common/tb](../hardware/common/tb/README.md)，
与生产代码分开保存。测试将真实 RTL 与本包的 ISA 模型逐提交比较，并通过 UART RX 引脚
装载、执行当前示例；同时检查 MMIO、UART 和 Timer 中断、fault 与超时处理。

在仓库根目录运行 `make -C hardware test`，需要 Python 3.10+、Verilator、g++ 和 make，无需 Qt。
`make -C hardware run` 可运行默认 ISA 示例，lint 和波形命令见[硬件说明](../hardware/README.md)。
