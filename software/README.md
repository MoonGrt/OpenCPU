# OpenCPU software

The simple compiler and native LLVM toolchain share ISA v2, the assembler, image format,
simulator, IDE and downloader:

| Backend | Input | Implementation |
|---|---|---|
| `simple` | `.oc` integer language | Independent Python lexer/parser/codegen under `opencpu/core/compiler/simple` |
| `llvm` | C17 `.c`, or LLVM IR `.ll` | Clang and native OpenCPU target in the LLVM fork; Python adapter under `opencpu/core/compiler/llvm` |

C uses a freestanding integer profile: 8-bit char, 16-bit short/int/pointers, 32-bit long and
64-bit long long. It supports RAM pointers, arrays with dynamic indices, globals, strings,
direct calls, recursion and multiple C files. Structs/unions, bitfields, function pointers,
floating point, VLA, varargs, atomics, C++ and a full libc are deferred.
See the [ABI](../docs/ABI.md) for types, registers, byte addresses and MMIO interfaces.
The CLI has no Qt dependency; simple builds do not import or launch LLVM.

## Install and run

Use Python 3.10+. From this directory on Linux/macOS:

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

Both windows use the same environment. **Tools > Downloader** opens the independent downloader.
Installed entry points are `opencpu`, `opencpu-ide`, and `opencpu-downloader`.
A desktop/display connection is required. Ubuntu/Debian GUI packages are `python3-venv`,
`libgl1`, `libxcb-icccm4`, `libxcb-image0`, `libxcb-keysyms1`, `libxcb-render-util0`,
`libxcb-shape0`, `libxcb-xinerama0`, `libxcb-xkb1`, and `libxkbcommon-x11-0`.
For CLI-only installation, use `python -m pip install -e .`.

## Assemble, compile and simulate

From this directory:

```bash
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/isa.bin
python3 -m opencpu compile examples/simple/functions.oc -o /tmp/functions.bin --assembly /tmp/functions.asm
python3 -m opencpu run /tmp/functions.bin
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
```

The simple language supports 16-bit integer expressions, comparisons, control flow,
up to four function arguments and return values. Variables are function-local and start at
zero. `print`, floating point, division and modulo report errors. `.oc` keeps this compiler.

Build the real tools from the repository root using
`python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test`, then return here:

```bash
python3 -m opencpu compile examples/llvm/factorial.ll -o /tmp/ir.bin
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin --assembly /tmp/c.asm
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu run /tmp/project.bin
```

`.c` and `.ll` select LLVM automatically; `--backend simple|llvm` makes the selection explicit.
`--language c|llvm-ir` overrides LLVM input-language detection. Multiple C files can be
listed directly, with repeatable include directories and preprocessor definitions:

```bash
python3 -m opencpu compile main.c math.c -I include -D FEATURE=1 -o /tmp/app.bin
```

The native chain uses Clang `--target=opencpu-unknown-none`, `llvm-link` and
`llc -march=opencpu -O0`. C17 freestanding mode disables host system headers while retaining
Clang resource headers and the SDK's `opencpu.h`/`string.h`. Use `int main(void)` and return
explicitly. No Python code interprets C or LLVM IR.

Tools must be OpenCPU LLVM 23.1.4. Directory precedence is `--llvm-bin-dir`,
`OPENCPU_LLVM_BIN_DIR`, then repository `build/llvm/bin`. The selected SDK is under the
adjacent `lib/opencpu/`; C requires Clang, resource headers, llvm-link and runtime bitcode.
A `.ll`-only installation can omit Clang. See the [build guide](../toolchain/llvm/README.md).

Images remain text with one 16-bit word per nonblank line. UART sends each word's high
byte first. `--pad-rom` fills the 1024-word ROM image with HALTs. RAM is also 1024 words:
C globals, string literals and stack share its 2048 bytes; runtime code and static data
initialization also consume ROM. Oversized images fail rather than changing hardware limits.
The downloader handles this same format and has no LLVM dependency.

## Multi-file C projects

A `.opencpu.json` manifest uses paths relative to its directory:

```json
{
  "version": 1,
  "sources": ["main.c", "math.c"],
  "include_dirs": ["include"],
  "defines": ["FEATURE=1"]
}
```

`sources` is an ordered, nonempty list of `.c` files. Include directories and definitions
are optional. Definitions use `NAME` or `NAME=value`. The manifest does not mix `.oc`
functions into the C program. All referenced C files are compiled separately and merged
at the bitcode level; missing and duplicate definitions produce diagnostics.

## IDE builds and execution

Opening `.c` or `.ll` selects LLVM C or LLVM IR; `.oc` remains Simple. Use
**Tools > Compiler backend** and **Tools > LLVM input language** to select per-document
settings. **Tools > LLVM tool directory...** selects another compiler installation.
Assembly `.asm`/`.s` and binary `.bin` documents retain their direct build paths.

Use **File > Open C project...** for a manifest and **File > Close C project** to detach it.
Project builds capture unsaved C and header buffers through a Clang VFS overlay; they do
not overwrite source files. Save changes to the manifest itself before building.
An opened project header can build the owning project; a standalone header cannot be run.

LLVM builds run in worker threads. **Stop** cancels the complete tool chain; edits,
tab switches, closure, language/tool changes and dependency changes invalidate the result.
Source/header/configuration files are watched and file hashes are rechecked before
running or downloading. Late completions cannot replace a newer build. Window closure
cancels work and waits asynchronously for workers. Layout, toolbars and icons are retained.

Run executes in event-loop batches; Run step and Run undo operate one instruction at a
time. All LLVM execution starts at `entry_pc=0`, initializes RAM, calls `main`, then HALTs.
Each Run permits 200000 instructions for C or 10000 for other inputs. Reaching the
limit pauses with its value in the message pane; Run continues from that instruction.
Execution still yields every 64 instructions, and Stop remains available.
Save uses full document paths, and Save As updates the save destination.

## Python API

`Toolchain.compile(source)` remains the independent simple path. For native compilation:

```python
from opencpu.core.toolchain import Toolchain
from opencpu.core.compiler.llvm import CProject

build = Toolchain().compile("int main(void) { return 42; }", backend="llvm", language="c")
project = CProject.load("example.opencpu.json")
build = Toolchain().compile_project(project, buffers={})
```

`compile` accepts `source_name`, `language="auto"`, `include_dirs`, `defines`,
`llvm_bin_dir`, `cancel_event` and `timeout` (60 seconds). Auto language selection uses the
source name; LLVM without a name defaults to IR. `compile_project` accepts buffer overrides
keyed by file paths and the same tool-directory/cancellation/timeout options. One deadline
covers the whole build, and cancellation terminates child processes.

`BuildResult` retains its previous constructor fields and adds defaulted `language`,
`abi_version`, `dependencies`, `dependency_hashes` and `data_size_bytes`. Native ABI is
`llvm-v2`; the data size is the static-region end byte address, including the reserved two
bytes. `source_map` still maps words to generated-assembly line numbers. Native
`variable_offsets` is empty; there is no source-variable debug mapping.
`Compiler`, `CompileError` and `LanguageError` imports remain compatible.

## Software simulation

The shared model includes GPIO/display, UART FIFOs, Timer interrupts, bounded reversible
history, PC breakpoints and JSONL traces. Use **Tools > Simulation...** for virtual I/O
and **Run > PC breakpoints** in the IDE. See the [simulator guide](../docs/Simulator.md)
for CLI options, examples and the abstract tick model.

## Verification

From the repository root, service and GUI tests do not require a native LLVM build:

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_services.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_gui.py -v
make -C hardware all
```

After building the actual native tools:

```bash
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_native_gui.py -v
make -C hardware test-llvm
```

Explicit native tests fail when required tools are missing. They check independent results,
startup, integer and pointer semantics, multi-file calls, RAM initialization, HALT and
SP/FP restoration, then compare images against real UART-uploaded RTL execution.
See [examples](examples/README.md), [ISA](../docs/ISA.md) and [hardware](../hardware/README.md).
