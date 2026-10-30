# OpenCPU

**English | [简体中文](README_cn.md)**

OpenCPU is a 16-bit FPGA CPU project with a custom **ISA v2**, a Verilog implementation,
and a shared assembler, compiler, simulator, Qt IDE, and serial downloader.
The [ISA specification](docs/ISA.md) defines instruction encodings, registers,
word addressing, CSRs, and interrupt behavior.

## Project overview

| Component | Current implementation |
|---|---|
| ISA | 16-bit instructions and data, word addresses, eight registers, arithmetic/logic, loads/stores, branches/calls, CSRs, HALT and MRET |
| CPU | Three-stage F/D/X pipeline, separate instruction/data interfaces, asynchronous memory reads, one system clock |
| SoC | UART with RX/TX FIFOs and ROM programming, Timer, GPIO, four-digit hexadecimal display, interrupt pending/acknowledgment |
| Toolchain | Shared tools; simple `.oc` compiler and native Clang C17 / LLVM IR toolchain |
| GUI | IDE and independently launchable downloader sharing one Python package and virtual environment |
| Verification | Verilator board-level testbench, pin-level UART upload, retirement comparison against the software model, MMIO and interrupt checks |

The simple compiler supports integer assignments, arithmetic/bitwise operations, comparisons,
`if`, `while`, `for`, functions with up to four parameters, and `return`.
Floating point, division, modulo, and `print` are not implemented.

## Documentation

| Topic | Guide |
|---|---|
| Instruction set, encoding, memory model, CSRs | [ISA v2](docs/ISA.md) |
| RTL organization, board interface, MMIO, programming | [Hardware guide](hardware/README.md) |
| Verilator commands, waveforms, driver options | [Testbench guide](hardware/common/tb/README.md) |
| Seeded simulator, compiler and UART/RTL stress tests | [Stress tests and results](docs/StressTesting.md) |
| Virtual environment, IDE, standalone downloader | [Software guide](software/README.md) |
| Native LLVM build and supported ABI | [LLVM guide](toolchain/llvm/README.md), [ABI](docs/ABI.md) |
| Rebuildable assembly and compiler examples | [Examples](software/examples/README.md) |
| Historical Logisim reference | [Logisim](docs/ref/logisim/README.md) |

## Quick start

### Assemble, compile, and simulate

Use **Python 3.10+**. The command line and core toolchain require no third-party Python
packages. Starting at the repository root, run the package from `software/`:

```bash
cd software
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/opencpu-isa.bin
python3 -m opencpu run /tmp/opencpu-isa.bin
python3 -m opencpu compile examples/simple/functions.oc -o /tmp/opencpu-functions.bin
python3 -m opencpu run /tmp/opencpu-functions.bin
python3 -m opencpu disassemble /tmp/opencpu-isa.bin -o /tmp/opencpu-isa.asm
python3 -m opencpu --help
```

These commands use `/tmp` for build outputs; choose another output directory as needed.
Machine-code `.bin` files are text, with one 16-bit binary word per line.
The simulator prints a JSON result with registers, RAM, and HALT/fault status.

| Example | Expected result |
|---|---|
| [isa.asm](software/examples/simple/isa.asm) | RAM word 0 = `0xabcc` (43980), then HALT |
| [loops.oc](software/examples/simple/loops.oc) | `X=15`, `Y=11`, `i=3` |
| [functions.oc](software/examples/simple/functions.oc) | `result=120`, using recursive factorial |

The [software simulator](docs/Simulator.md) also models GPIO, display, UART FIFOs, Timer
and interrupts, with virtual inputs, PC breakpoints and trace output. Its ticks are
abstract instruction time; use the RTL simulation below for physical clocks and pin waveforms.

### Native C and LLVM IR compiler (optional)

The `simple` compiler remains the default for `.oc`. The native LLVM chain also
accepts C17 `.c` and `.ll`, using a real OpenCPU Clang target, bitcode linking and
SelectionDAG backend. C supports integer types through 64 bits, RAM pointers,
arrays, globals, strings, direct calls and multiple source files. Structs/unions,
function pointers, floating point and a full libc are deferred. See the
[LLVM build guide](toolchain/llvm/README.md) and [ABI v2](docs/ABI.md).

From the repository root, with the fork's OpenCPU sources present:

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
cd software
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu compile examples/llvm/factorial.ll -o /tmp/factorial.bin
python3 -m opencpu run /tmp/factorial.bin
```

The IR factorial result is `a1=120` followed by HALT. Native tools are pinned to
LLVM 23.1.4 under `build/llvm/bin`; select another build with `--llvm-bin-dir` or
`OPENCPU_LLVM_BIN_DIR`. The SDK is in adjacent `lib/opencpu/`. Simple builds need
no LLVM; `--ir-only` builds omit Clang. All images remain limited to 1024 ROM words,
and C static data and stack share 2048 RAM bytes.

The IDE detects C/IR on open. **File > Open C project...** loads a multi-file
manifest; **Tools > LLVM input language** selects C or IR. Background builds use
unsaved C/header buffers, and **Stop**, edits or dependency changes invalidate
stale results before execution or download. Window layout remains unchanged.

### Run the IDE or downloader

From the repository root on Linux/macOS:

```bash
cd software
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui]'
.venv/bin/python ide.py
# Start the downloader independently:
.venv/bin/python downloader.py
```

The IDE also opens the downloader through **Tools > Downloader**. Both windows use the
same environment. See the [software guide](software/README.md) for Windows PowerShell
commands and Linux Qt dependencies. GUI applications require a desktop/display connection.

### Run the Verilator simulation

From the **repository root**, with Verilator, g++, GNU make, and Python 3.10+ installed:

```bash
make -C hardware lint
make -C hardware test
make -C hardware run TRACE=build/wave.vcd
# Optional waveform viewer:
gtkwave hardware/common/tb/build/wave.vcd
```

`test` builds and runs nine self-checks, including the current examples, arithmetic,
branches, signed memory offsets, GPIO/display/UART, interrupts and MRET, illegal
encodings, out-of-range instruction fetches, and timeout handling. Pure ISA programs
are compared against the software model at each retirement. `make -C hardware all`
runs lint and tests together, without LLVM. After building LLVM,
`make -C hardware test-llvm` checks its programs through the same UART/RTL path.

The testbench wraps the actual board `top`, uploads images through its UART RX pin
while reset is asserted, then releases reset and executes. It uses 1024-word ROM/RAM,
a 1 MHz clock, and 62500 baud (16 clocks per bit) to shorten simulation. These parameters
are separate from the board defaults of 27 MHz and 115200 baud.

Build products and waveforms stay under `hardware/common/tb/build/`.
`make -C hardware clean` removes them. Driver exit codes distinguish HALT, faults,
and execution timeouts; see the [testbench guide](hardware/common/tb/README.md)
for custom images, retirement logs, RX input, and cycle limits.

## Program a board

1. Build a complete image from the repository root:

   ```bash
   cd software
   python3 -m opencpu assemble examples/simple/isa.asm --pad-rom -o /tmp/opencpu-board.bin
   ```

2. Hold the board CPU reset input `rst_n` low. Open the downloader, load the binary
   text image, and send it with **115200 baud, 8 data bits, no parity, one stop bit**
   for the default RTL parameters. Each word is sent high byte first.
3. Wait for the last complete UART frame, then release reset. Execution starts at PC=0.

The downloader does not control the board reset automatically. `--pad-rom` fills the
default 1024-word image with HALTs so an older program tail is overwritten. The current
upload protocol has no device acknowledgment or CRC. See the
[hardware guide](hardware/README.md#复位与串口下载) for programming and MMIO details.

## Repository layout

```text
OpenCPU/
├─ .devcontainer/                 Development container configuration
├─ docs/
│  ├─ ABI.md                      LLVM subset and calling convention
│  ├─ ISA.md                      Current ISA specification
│  ├─ images/block_diagram.png    Historical diagram
│  └─ ref/logisim/                Historical Logisim circuit
├─ hardware/
│  ├─ verilog/
│  │  ├─ core/                   Pipeline, decode, execute, registers, CSRs
│  │  ├─ include/isa.vh          Hardware ISA definitions
│  │  ├─ memory/                 RAM and UART-programmable ROM
│  │  ├─ peripherals/            GPIO, display, Timer, UART
│  │  ├─ soc/                    Reset, interrupts, interconnect
│  │  ├─ files.f                 Production source manifest
│  │  └─ top.v                   Board-facing top module
│  ├─ common/tb/                 Verilator testbench, driver, self-checks
│  ├─ Makefile
│  └─ README.md
├─ software/
│  ├─ opencpu/                   Core toolchain, GUI, serial transport, CLI
│  ├─ examples/
│  │  ├─ simple/                 Assembly and simple .oc examples
│  │  ├─ llvm/                   Native LLVM .ll examples
│  │  └─ c/                      C17 and multi-file projects
│  ├─ runtime/                   Startup assembly, integer runtime and SDK headers
│  ├─ ide.py                     IDE launcher
│  ├─ downloader.py              Standalone downloader launcher
│  ├─ pyproject.toml
│  ├─ README.md
│  └─ README_cn.md
├─ toolchain/llvm/                LLVM build configuration, acceptance tests and instructions
├─ thirdpartys/llvm-project/      Submodule: LLVM fork and unique backend sources
├─ LICENSE
├─ README.md
└─ README_cn.md
```

## Status and compatibility

The current working tree keeps one ISA v2 RTL and two compiler paths with rebuildable source examples.
The native backend is developed in the LLVM fork; its local changes and publication order
are described in the [LLVM guide](toolchain/llvm/README.md).
Older software, binaries, and removed documentation images remain available in Git history.
The remaining early block diagram and Logisim circuit are historical references; use the
current ISA specification and RTL for implementation details. Earlier binary encodings
require rebuilding from source for ISA v2.

This checkout does not contain a target FPGA project, pin assignments, or timing
constraints. RTL simulation checks behavior; board-specific synthesis, place and route,
and hardware testing are still needed for resource and timing results.

## Contributing and license

Report bugs or propose changes through [issues](https://github.com/MoonGrt/OpenCPU/issues)
and pull requests. ISA changes should update the RTL, software, specification, and tests
together. Run `make -C hardware all` before submitting a hardware/toolchain change.

The main project is distributed under the [MIT License](LICENSE). The LLVM submodule
and its backend additions follow their own Apache-2.0 WITH LLVM-exception license. Author: [MoonGrt](https://github.com/MoonGrt),
[1561145394@qq.com](mailto:1561145394@qq.com).
