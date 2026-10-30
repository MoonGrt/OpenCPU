# OpenCPU software

One current ISA v2 implementation serves the IDE, standalone downloader and command line.
The UI retains its menus, toolbars, split panes and icons. Core code has no Qt dependency.

```text
software/
  ide.py / downloader.py       graphical launchers
  pyproject.toml               installation and optional GUI dependency
  opencpu/
    core/                      ISA, assembler, compiler, simulator, images, toolchain
    gui/                       window layouts, controllers, documents, resources
    transport/                 validated settings and Qt serial transport
    cli.py                     command-line application
  examples/                    current, rebuildable source examples
```

## Install and run

Use Python 3.10 or newer. From this directory on Linux/macOS:

```bash
python3 -m venv .venv
.venv/bin/python -m pip install -e '.[gui]'
.venv/bin/python ide.py
.venv/bin/python downloader.py
```

Windows PowerShell:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[gui]'
.\.venv\Scripts\python.exe ide.py
.\.venv\Scripts\python.exe downloader.py
```

The same environment runs both windows. **Tools > Downloader** also opens the independent
downloader from the IDE. Installed entry points are `opencpu-ide`, `opencpu-downloader`
and `opencpu`; they work from any directory. A desktop/display connection is required.
Ubuntu/Debian needs `python3-venv`, `libgl1`, `libxcb-icccm4`, `libxcb-image0`,
`libxcb-keysyms1`, `libxcb-render-util0`, `libxcb-shape0`, `libxcb-xinerama0`,
`libxcb-xkb1` and `libxkbcommon-x11-0` for the Qt GUI.

For command-line use only, install with `python -m pip install -e .` instead of `.[gui]`.
No GUI libraries are imported by the toolchain or CLI.

## Build and simulate

From the repository root:

```bash
cd software
python3 -m opencpu assemble examples/isa.asm -o /tmp/isa.bin
python3 -m opencpu run /tmp/isa.bin
python3 -m opencpu compile examples/loops.oc -o /tmp/loops.bin --assembly /tmp/loops.asm
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
cd ..
```

Run `python3 -m opencpu` inside `software/`; the final `cd ..` returns to the repository root. `--pad-rom` on
assemble/compile fills a 1024-word image with trailing HALTs to replace an old ROM tail.
The binary format is text: one 16-bit word per line. Downloads send each word high byte first.

The IDE compiles the integer source language and can assemble `.asm`/`.s` files or load
binary text `.bin` files. Run executes in event-loop batches; Stop remains responsive.
Editing the source invalidates its build and prevents execution or download of stale code.
Save uses each document's complete path; Save As rebinds it. Binary documents retain their format.

The compiler supports 16-bit integer expressions, control flow, up to four function arguments
and return values. Variables are local to each function; uninitialized locals start at zero.
There are no implicit globals. `print`, floating point, division and modulo produce explicit errors.
See [examples](examples/README.md) and the [ISA specification](../docs/ISA.md).
Only current source examples are retained; historical software versions are available in Git history.

## Hardware/software verification

The Verilator testbench and regression live in
[hardware/common/tb](../hardware/common/tb/README.md), separated from production code.
They compare real RTL against this package's ISA model at each retirement and load the
current examples through the UART RX pin before execution. The suite also checks MMIO,
UART and Timer interrupts, faults, and timeout handling.

From the repository root, run `make -C hardware test`. This requires Python 3.10+,
Verilator, g++, and make; Qt is not required. Run `make -C hardware run` for the default
ISA example, or see the [hardware guide](../hardware/README.md) for lint and waveform commands.
