# OpenCPU 原生 Clang/LLVM 工具链

`simple` 极简 `.oc` 编译器与 `llvm` 原生编译链长期并存。LLVM 接受 Clang C17 和 `.ll` 输入，
使用真实的 OpenCPU C++/TableGen/SelectionDAG 后端，最终复用现有汇编器生成完整镜像。
C 类型为 char8、short/int16、long32、long long64、数据指针16，支持范围与调用约定见
[ABI v2](../../docs/ABI.md)。本轮不提供 ELF、目标链接器、操作系统或完整 libc。

## 源码与版本

LLVM/Clang 的目标实现位于 `thirdpartys/llvm-project` 子模块：后端在 `llvm/lib/Target/OpenCPU`，
Clang TargetInfo 和内建函数也在同一 fork。主仓 `software/opencpu/core/compiler/llvm/` 只负责
工具发现、项目清单、进程与结果适配，不解析 C/IR，不复制第二份原生后端。
SDK 源码和启动汇编位于 `software/runtime/`；本目录维护构建脚本、验收测试和说明。
子模块 origin 为 [MoonGrt/llvm-project](https://github.com/MoonGrt/llvm-project)。

固定基线为 `llvmorg-23.1.4`，提交 `7a941dfb2877a0b8cf30323fefa85ad019e0b0f5`，
开发分支为 `opencpu/llvm-23.x`。构建脚本检查当前提交从基线派生。
本地未提交的改动可以构建，但不能假设远端 `main` 已包含这些目标实现。
提交和发布按以下顺序进行：

1. 在 LLVM 子仓提交并验证目标代码。
2. 发布子仓提交到 fork，确认远端可获取。
3. 主仓更新子模块指针并提交。

发布后，新的主仓工作区按 gitlink 初始化固定版本：

```bash
git submodule update --init --recursive thirdpartys/llvm-project
```

如果已有 LLVM 工作区使用 sparse checkout，完整 C 构建还需包含 Clang 源码：

```bash
git -C thirdpartys/llvm-project sparse-checkout add clang
```

极简编译与默认硬件检查不需要初始化或构建 LLVM。

## 构建工具与 SDK

需要 Git、Python 3.10+、CMake、Ninja 和 C++17 编译器。容器配置包含相应系统依赖；
Python/Qt 虚拟环境不提供 LLVM 可执行文件。从主仓根目录执行：

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
build/llvm/bin/clang --version
build/llvm/bin/llc --version
```

默认启用 Clang 和唯一的 OpenCPU experimental target，构建 `clang`、资源头文件、`llc`、
`llvm-link` 和测试工具；不构建其他架构、lld 或通用运行库。
不构建 Clang 静态分析器和 ARC 迁移工具。
默认编译并行度为二、链接并行度为一；宿主 Release C/C++ 使用 `-O1` 降低资源消耗，LLVM assertions 开启。
这些宿主选项与编译用户程序的固定参数分别配置。

构建脚本还用 `llvm-link` 将主仓运行库 IR 合并到 `build/llvm/lib/opencpu/runtime.bc`，
并安装 SDK 头文件到相邻的 `include/`。Python 包通过所选工具目录定位 SDK，不依赖源码仓库的位置。
运行库含宽整数 helper 和 `memcpy/memmove/memset/memcmp`，没有宿主 libc 依赖。

```bash
python3 toolchain/llvm/build.py --ir-only --jobs 2 --test
python3 toolchain/llvm/build.py --configure-only
python3 toolchain/llvm/build.py --build-dir /tmp/opencpu-llvm-build --jobs 1 --link-jobs 1
```

`--ir-only` 省略 Clang 和资源头文件，仍构建 LLVM IR 工具和运行库。`--test` 运行原生后端 lit 测试。
`--source-dir` 可选择另一份包含 OpenCPU 实现、从相同基线派生的源码。
默认产物 `build/llvm/` 被 Git 忽略。源码移动时脚本会刷新 CMake 配置并保留对象与可执行文件；
绝对路径变化后，下一次完整构建可能需要重新编译。

## 编译 C 和 LLVM IR

从主仓根目录进入 `software`：

```bash
cd software
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin --assembly /tmp/c.asm
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu run /tmp/project.bin
python3 -m opencpu compile examples/llvm/factorial.ll -o /tmp/factorial.bin
python3 -m opencpu run /tmp/factorial.bin
```

`.c/.ll` 自动使用 LLVM，其他输入默认 Simple。可使用 `--backend`、`--language` 显式指定。
多文件也可直接列出：

```bash
python3 -m opencpu compile main.c math.c -I include -D FEATURE=1 -o /tmp/app.bin
```

项目清单格式、虚拟环境和 IDE 操作见[软件说明](../../software/README_cn.md)。
工具目录依次取 `--llvm-bin-dir` / Python `llvm_bin_dir`、`OPENCPU_LLVM_BIN_DIR`、本仓 `build/llvm/bin`。
适配层验证 LLVM 23.1.4 和 OpenCPU target；C 还验证前端、bitcode 链接工具与 SDK。
编译错误、工具缺失、超时和取消均返回清晰错误，极简版不作为 LLVM 的静默回退。

实际管线为：

```text
C source files → Clang bitcode → llvm-link → OpenCPUPrepare/llc → assembly
                                                                   ↓
                                                           shared assembler
                                                                   ↓
                                                         16-bit word image
```

Clang 固定使用 `--target=opencpu-unknown-none -std=c17 -ffreestanding -nostdlibinc`
和 `-O0 -Xclang -disable-O0-optnone`；保留资源及 SDK 头文件，关闭宿主系统头文件，禁止跳转表。
后端准备阶段提升局部变量、降低 switch 和运行库操作，按需导入 runtime，再验证和选择指令。
直接调用 `llc`、且程序需要运行库时，传入 `-opencpu-runtime=/path/to/lib/opencpu/runtime.bc`。
`llc -march=opencpu -O0 -filetype=asm` 输出当前汇编器方言，Python 不解释 IR。

入口为显式返回的 `int main(void)`；启动代码初始化 RAM 后调用 main，返回后 HALT。
C 的普通指针使用字节地址，MMIO 使用 `<opencpu.h>` 的硬件字地址接口。
默认 ROM/RAM 各 1024 字，静态初始化与运行库也占 ROM，全局数据与栈共享 RAM；超容量报错。
镜像可以 `--pad-rom` 补齐并交给现有下载器，UART 协议不变。

## IDE 与取消

打开 `.c/.ll` 自动选择 LLVM C/IR；**File > Open C project...** 加载多文件清单。
**Tools > LLVM input language** 和 **Tools > LLVM tool directory...** 修改配置。
工作线程捕获打开的 C/头文件 buffer，使用 VFS overlay 编译未保存内容；清单自身需先保存。
编辑任一相关 buffer、改变文件依赖或配置、切页、关闭和 Stop 均使旧结果失效。
运行和下载前再次核对依赖，禁止使用陈旧镜像；窗口关闭异步等待取消完成。

## 验收

主仓根目录执行宿主测试和默认 RTL 回归：

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_services.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_gui.py -v
make -C hardware all
```

实际构建 Clang/OpenCPU 工具链后执行：

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_native_gui.py -v
make -C hardware test-llvm
```

显式 native 和 `test-llvm` 必须使用真实工具，缺失时失败，不跳过。
用例检查 C/IR 的独立结果、类型宽度、指针与字节写入、全局初始化、多文件符号、宽参数/返回、
递归、大栈帧和 MMIO，验证 HALT、SP/FP 恢复，再逐退休对照软件模型和真实 UART 上传后的 RTL。
进程服务与 GUI 测试覆盖错误、超时、取消和迟到结果；它们的受控服务不代替原生编译验收。
本轮可重复执行的检查和结果见[验证记录](VALIDATION.md)。
固定种子的随机压力测试、百万步内存检查及 UART/RTL 对照见[压力测试](../../docs/StressTesting.md)；
统一入口为 `python3 -B toolchain/llvm/stress.py --profile full`（从主仓根目录运行）。
镜像、波形与仿真参数见[整机仿真说明](../../hardware/common/tb/README.md)。

LLVM 子模块及其后端遵循 Apache-2.0 WITH LLVM-exception；主仓其他部分按主仓许可证分发。
