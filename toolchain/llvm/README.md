# OpenCPU 原生 LLVM 工具链

`simple` 极简编译器与 `llvm` 原生后端长期并存。LLVM 首版接受受限 `i16` LLVM IR，
通过 C++、TableGen 和 SelectionDAG 生成当前 Python 汇编器可接受的汇编。
输入不是 C；Clang、ELF、链接器和通用运行库属于后续工作。支持范围见 [ABI](../../docs/ABI.md)。

## 源码与版本

后端唯一源码位于 `thirdpartys/llvm-project` 子模块中的 `llvm/lib/Target/OpenCPU`，
CodeGen 测试位于该子模块的 `llvm/test/CodeGen/OpenCPU`。主仓本目录只维护构建配置与说明，
不复制第二份后端。Python 调用适配层位于主仓 `software/opencpu/core/compiler/llvm/`，
负责工具发现、启动汇编、超时和取消；它通过真实 `llc` 生成汇编。子模块 origin 指向 [MoonGrt/llvm-project](https://github.com/MoonGrt/llvm-project)。

固定基线为 `llvmorg-23.1.4`，提交
`7a941dfb2877a0b8cf30323fefa85ad019e0b0f5`，开发分支为 `opencpu/llvm-23.x`。
构建脚本检查当前提交是否从该基线派生；子模块中尚未提交的目标源码也可用于本地开发构建。

本次实现先保留在本地分支/工作区，不能假定 fork 的远端 `main` 已有 OpenCPU target。
源码交付与审阅需包含子模块里的改动。发布顺序为：

1. 在 LLVM 子仓提交并测试 OpenCPU 后端。
2. 将该提交发布到 fork 的开发分支，确认远端可获取。
3. 在主仓更新子模块指针，再保存主仓变更。

发布并更新主仓之后，新工作区可从主仓初始化对应版本：

```bash
git submodule update --init --recursive thirdpartys/llvm-project
```

正常初始化会按 gitlink 检出固定提交。需要继续开发时，在子仓切到对应的开发分支。
极简工具链及默认硬件检查不需要初始化或构建 LLVM。

## 构建

宿主工具为 Git、Python 3.10+、CMake、Ninja 和支持 C++17 的编译器。
Ubuntu 开发容器已列出对应系统依赖；Python/Qt 虚拟环境不提供 LLVM 可执行文件。
从主仓根目录执行：

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
build/llvm/bin/llc --version
```

默认只启用 OpenCPU experimental target，不构建 Clang 或其他架构。
宿主 C/C++ 源码采用 `-O1` 来降低构建资源消耗，LLVM assertions 开启；
这与生成用户程序固定使用的 `llc -O0` 是两个不同选项。
默认两个并行编译任务、一个链接任务，可用 `--jobs`、`--link-jobs` 调整。
`--test` 构建后运行原生 CodeGen lit 测试，工具或测试失败会使脚本返回非零状态。

其他构建参数：

```bash
python3 toolchain/llvm/build.py --configure-only
python3 toolchain/llvm/build.py --build-dir /tmp/opencpu-llvm-build --jobs 1 --link-jobs 1
```

`--source-dir` 可选择另一份基于相同固定版本、包含 OpenCPU target 的源码工作区。
默认产物为被 Git 忽略的 `build/llvm/`；它不属于 LLVM 子模块的源码提交。
源码目录移动时，构建脚本会刷新 CMake 配置，保留已有可执行文件和对象文件。
源码绝对路径变化后，下一次完整构建可能需要重新编译相关文件。

## 调用与配置

从主仓根目录进入 `software`：

```bash
cd software
python3 -m opencpu compile examples/llvm/constant.ll --backend llvm -o /tmp/constant.bin --assembly /tmp/constant.asm
python3 -m opencpu run /tmp/constant.bin
```

预期 `a1=43981`，随后 HALT。`factorial.ll` 返回 120，`phi_loop.ll` 返回 45。
与极简版一样，可用 `--pad-rom` 用 HALT 补齐默认 1024 字镜像，再由下载器发送。

工具目录优先级为：显式 `--llvm-bin-dir` / Python `llvm_bin_dir` 参数，
然后环境变量 `OPENCPU_LLVM_BIN_DIR`，最后主仓的 `build/llvm/bin`。

```bash
python3 -m opencpu compile examples/llvm/factorial.ll --backend llvm \
  --llvm-bin-dir /tmp/opencpu-llvm-build/bin -o /tmp/factorial.bin
```

适配层验证 `llc --version` 中的 23.1.4 和 OpenCPU 注册项。
实际命令为 `llc -march=opencpu -O0 -filetype=asm`，通过参数数组调用，不使用 shell；
编译失败、工具缺失、版本错误、超时和取消均报告构建错误。
极简后端不会导入或启动 LLVM，也不会在 LLVM 失败时被当作回退路径。

IDE 打开 `.ll` 自动使用 LLVM；**Tools > Compiler backend** 选择当前文档的后端。
LLVM 构建在后台执行，**Stop** 取消；编辑、切页、关闭文档或切换后端会使旧请求失效。

## 验收

主仓根目录执行：

```bash
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s software/tests -v
python3 -B -m unittest discover -s software/tests/native -v
make -C hardware all
make -C hardware test-llvm
```

宿主测试包含工具进程管理及 GUI 生命周期；GUI 需要安装可选 PyQt5。
显式 native 与 `test-llvm` 入口必须使用真实编译后的后端，缺少工具时失败。
用例验证独立预期结果、调用/递归、PHI、比较/布尔、大栈帧、远分支和寄存器溢出，
随后通过真实 UART RX 上传同样的镜像并逐退休对照软件模型。
详细镜像、波形和驱动参数见 [整机仿真说明](../../hardware/common/tb/README.md)。

LLVM 子模块及其中的后端源码遵循 LLVM 的 Apache-2.0 WITH LLVM-exception 许可证；主仓其他部分按主仓许可证分发。
