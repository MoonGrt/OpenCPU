# OpenCPU software

Two compilers share ISA v2, the assembler, image format, simulator, IDE and downloader:

| Backend | Input | Implementation |
|---|---|---|
| `simple` (default) | `.oc` integer language | Python lexer/parser/codegen under `opencpu/core/compiler/simple` |
| `llvm` | Restricted `i16` LLVM IR, `.ll` | Native C++/TableGen/SelectionDAG target in the LLVM fork; Python process adapter under `opencpu/core/compiler/llvm` |

Clang/C, ELF/linking and a general pointer ABI are outside this first LLVM version.
See the [ABI](../docs/ABI.md) for supported operations and stack-address restrictions.
The core toolchain and CLI have no Qt dependency; simple builds do not find or launch LLVM.

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

Both windows use the same environment. **Tools > Downloader** also opens the downloader.
Installed entry points are `opencpu`, `opencpu-ide`, and `opencpu-downloader`.
A desktop/display connection is required. Ubuntu/Debian GUI packages are `python3-venv`,
`libgl1`, `libxcb-icccm4`, `libxcb-image0`, `libxcb-keysyms1`, `libxcb-render-util0`,
`libxcb-shape0`, `libxcb-xinerama0`, `libxcb-xkb1`, and `libxkbcommon-x11-0`.
For CLI-only installation, use `python -m pip install -e .`.

## Build and simulate

From this directory:

```bash
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/isa.bin
python3 -m opencpu compile examples/simple/functions.oc --backend simple -o /tmp/functions.bin --assembly /tmp/functions.asm
python3 -m opencpu run /tmp/functions.bin
python3 -m opencpu disassemble /tmp/isa.bin -o /tmp/isa.dis.asm
```

The simple language supports 16-bit integer expressions, comparisons, control flow,
up to four function arguments and return values. Variables are local to a function;
uninitialized locals start at zero. `print`, floating point, division and modulo report errors.
Omitting `--backend` preserves this compiler and its existing behavior.

Build the LLVM tools from the repository root with
`python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test`, then return here:

```bash
python3 -m opencpu compile examples/llvm/factorial.ll --backend llvm -o /tmp/factorial.bin --assembly /tmp/factorial.asm
python3 -m opencpu run /tmp/factorial.bin
```

This example returns `a1=120` and HALTs. LLVM compilation always uses the real target's
`llc -march=opencpu -O0`; unsupported IR is diagnosed rather than translated by Python.
The executable must be LLVM 23.1.4 with a registered OpenCPU target. Its directory is
selected by `--llvm-bin-dir`, then `OPENCPU_LLVM_BIN_DIR`, then repository `build/llvm/bin`.
Use the [LLVM guide](../toolchain/llvm/README.md) for source initialization, build options
and publication of the local fork changes.

The `.bin` format is text, one 16-bit word per nonblank line; UART sends each word's
high byte first. `--pad-rom` fills the default 1024-word image with trailing HALTs.
Both compilers produce this same format; the downloader needs no LLVM dependency.

## IDE compiler selection

Opening `.ll` selects LLVM; other source documents default to Simple. Use
**Tools > Compiler backend > Simple (.oc) / LLVM IR (.ll)** for the current document.
Assembly `.asm`/`.s` and binary `.bin` documents keep their direct build paths.

LLVM compilation runs in a worker thread. **Stop** cancels the external compiler;
editing, switching tabs, closing documents or changing backend invalidates the request.
Late completions cannot replace a newer build or enable downloading stale code.
Closing the IDE cancels outstanding work and waits asynchronously for workers to exit.
The existing layout, toolbars and icons are retained.

Run executes in event-loop batches, while Run step and Run undo operate one instruction
at a time. All execution starts at the build's `entry_pc` (zero), including LLVM startup
before `main`. Save uses full document paths and Save As rebinds the save destination.

## Python build API

`Toolchain.compile(source)` remains the simple path. Optional keywords are `backend`,
`source_name`, `llvm_bin_dir`, `cancel_event`, and `timeout` (60 seconds by default).
`BuildResult` adds `backend`, `isa_version`, and `entry_pc`; `source_map` still maps each
machine word to a 1-based line in the generated assembly. LLVM leaves `variable_offsets`
empty; it does not claim source-variable debugging or the simple compiler's fixed slots.
The previous `Compiler`, `CompileError`, and `LanguageError` package imports remain valid.

## Verification

From the repository root, host tests including offscreen Qt tests use the GUI environment:

```bash
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s software/tests -v
make -C hardware all
```

The default hardware suite needs no LLVM. After building the native target, run:

```bash
python3 -B -m unittest discover -s software/tests/native -v
make -C hardware test-llvm
```

Explicit native/LLVM targets fail if the real toolchain is missing. They check independent
expected results and software/RTL agreement through actual UART RX programming.
See [examples](examples/README.md), the [ISA specification](../docs/ISA.md),
and the [hardware guide](../hardware/README.md).
