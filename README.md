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
| Toolchain | Assembler with label relaxation, disassembler, integer compiler, instruction-level simulator |
| GUI | IDE and independently launchable downloader sharing one Python package and virtual environment |
| Verification | Verilator board-level testbench, pin-level UART upload, retirement comparison against the software model, MMIO and interrupt checks |

The compiler supports integer assignments, arithmetic/bitwise operations, comparisons,
`if`, `while`, `for`, functions with up to four parameters, and `return`.
Floating point, division, modulo, and `print` are not implemented.

## Documentation

| Topic | Guide |
|---|---|
| Instruction set, encoding, memory model, CSRs | [ISA v2](docs/ISA.md) |
| RTL organization, board interface, MMIO, programming | [Hardware guide](hardware/README.md) |
| Verilator commands, waveforms, driver options | [Testbench guide](hardware/common/tb/README.md) |
| Virtual environment, IDE, standalone downloader | [Software guide](software/README.md) |
| Rebuildable assembly and compiler examples | [Examples](software/examples/README.md) |
| Historical Logisim reference | [Logisim](docs/ref/logisim/README.md) |

## Quick start

### Assemble, compile, and simulate

Use **Python 3.10+**. The command line and core toolchain require no third-party Python
packages. Starting at the repository root, run the package from `software/`:

```bash
cd software
python3 -m opencpu assemble examples/isa.asm -o /tmp/opencpu-isa.bin
python3 -m opencpu run /tmp/opencpu-isa.bin
python3 -m opencpu compile examples/functions.oc -o /tmp/opencpu-functions.bin
python3 -m opencpu run /tmp/opencpu-functions.bin
python3 -m opencpu disassemble /tmp/opencpu-isa.bin -o /tmp/opencpu-isa.asm
python3 -m opencpu --help
```

These commands use `/tmp` for build outputs; choose another output directory as needed.
Machine-code `.bin` files are text, with one 16-bit binary word per line.
The simulator prints a JSON result with registers, RAM, and HALT/fault status.

| Example | Expected result |
|---|---|
| [isa.asm](software/examples/isa.asm) | RAM word 0 = `0xabcc` (43980), then HALT |
| [loops.oc](software/examples/loops.oc) | `X=15`, `Y=11`, `i=3` |
| [functions.oc](software/examples/functions.oc) | `result=120`, using recursive factorial |

The software simulator models instructions, registers, CSRs, and RAM. Use the RTL
simulation below for UART/Timer clocks, FIFOs, and SoC peripheral behavior.

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
runs lint and tests together.

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
   python3 -m opencpu assemble examples/isa.asm --pad-rom -o /tmp/opencpu-board.bin
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
│  ├─ examples/                  Current source examples
│  ├─ ide.py                     IDE launcher
│  ├─ downloader.py              Standalone downloader launcher
│  ├─ pyproject.toml
│  ├─ README.md
│  └─ README_cn.md
├─ LICENSE
├─ README.md
└─ README_cn.md
```

## Status and compatibility

The current working tree keeps one ISA v2 implementation and rebuildable source examples.
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

Distributed under the [MIT License](LICENSE). Author: [MoonGrt](https://github.com/MoonGrt),
[1561145394@qq.com](mailto:1561145394@qq.com).
