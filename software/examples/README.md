# Current examples

The assembly, simple `.oc`, C `.c`, and native LLVM `.ll` source files use the current [ISA v2](../../docs/ISA.md). Build outputs belong in a
temporary or user-selected directory, so the repository has no stale generated binaries.

## Simple compiler and assembly examples

Sources are kept in `simple/`; C inputs are in `c/`, and LLVM IR inputs are in `llvm/`.

| Source | Expected result |
|---|---|
| [isa.asm](simple/isa.asm) | RAM word 0 = 0xabcc (43980), then HALT |
| [loops.oc](simple/loops.oc) | X=15, Y=11, i=3 |
| [functions.oc](simple/functions.oc) | result=120, using recursive calls |
| [uart_echo.asm](simple/uart_echo.asm) | Inject `41 00 ff`; TX returns those three bytes |
| [timer_irq.asm](simple/timer_irq.asm) | One-shot IRQ writes RAM word 0 = 1, clears elapsed, then HALT |

From the repository root:

```bash
cd software
python3 -m opencpu assemble examples/simple/isa.asm -o /tmp/isa.bin
python3 -m opencpu run /tmp/isa.bin
python3 -m opencpu compile examples/simple/loops.oc -o /tmp/loops.bin --assembly /tmp/loops.asm
python3 -m opencpu run /tmp/loops.bin
python3 -m opencpu compile examples/simple/functions.oc -o /tmp/functions.bin
python3 -m opencpu run /tmp/functions.bin
cd ..
```

In the IDE, open an assembly or simple example and choose **Run > Assemble**, followed by **Run**, **Run step**
or **Run undo**. RAM uses word addresses. The simple compiler stores main's variables below fp=1022;
the first declared variable is at word 1021. `.oc` files use the small integer source language,
`.asm` files are assembly, and `.bin` files are binary text with one 16-bit word per line.

Use `--pad-rom` when building a complete 1024-word image to overwrite a previous ROM tail.
Use the [software simulator guide](../../docs/Simulator.md) for virtual RX, Timer IRQs, PC breakpoints and tracing.
The downloader window can open the resulting binary directly. See the [software guide](../README.md).

## Native C17 examples

Build Clang and the OpenCPU SDK using the [LLVM guide](../../toolchain/llvm/README.md).
The `.c` programs use the freestanding [ABI v2](../../docs/ABI.md): 8-bit char,
16-bit int/pointers, 32-bit long and 64-bit long long. Ordinary pointers address RAM
bytes; `<opencpu.h>` provides hardware-word MMIO access. Global data and strings
are initialized in RAM before `main`; code and data must fit the default memories.

| Source | Coverage | Expected a1 |
|---|---|---|
| [constant.c](c/constant.c) | C entry point and constant return | 43981 |
| [integers.c](c/integers.c) | Integer arithmetic and conversions | 65502 |
| [control.c](c/control.c) | Conditions, loops and switch | 125 |
| [pointers.c](c/pointers.c) | Dynamic indices and RAM pointers | 65005 |
| [globals.c](c/globals.c) | Static initializers and zero-initialized storage | 289 |
| [strings.c](c/strings.c) | Byte addressing and string data | 527 |
| [calls.c](c/calls.c) | Register and stack arguments | 4670 |
| [factorial.c](c/factorial.c) | Recursive calls and stack restoration | 120 |
| [narrow.c](c/narrow.c) | Char/bool argument and return conversions | 50 |
| [wide32.c](c/wide32.c) | 32-bit values and runtime operations | 47119 |
| [wide64.c](c/wide64.c) | 64-bit values and runtime operations | 57344 |
| [large_frame.c](c/large_frame.c) | Stack frame beyond short memory offsets | 3432 |
| [mmio.c](c/mmio.c) | Word-address MMIO interface | 4665 |
| [Multi-file project](c/multifile/demo.opencpu.json) | Separate translation units, shared declarations and project macros | 33 |

From the repository root:

```bash
cd software
python3 -m opencpu compile examples/c/integers.c -o /tmp/c.bin --assembly /tmp/c.asm
python3 -m opencpu run /tmp/c.bin
python3 -m opencpu compile --project examples/c/multifile/demo.opencpu.json -o /tmp/project.bin
python3 -m opencpu run /tmp/project.bin
```

The [native test registry](../../toolchain/llvm/tests/cases.py) records independent
expected results. Native acceptance uses actual Clang/llc, then runs the generated
images in the software model and through the real UART-uploaded RTL testbench.
Each program returns explicitly from `int main(void)` and must reach HALT with
SP=1024 and FP=0. Structs/unions, function pointers, floating point, VLA and a full
libc are outside this version's profile.

## Native LLVM IR examples

Build the real OpenCPU target first using the [LLVM guide](../../toolchain/llvm/README.md).
These `.ll` programs exercise the [LLVM ABI v2](../../docs/ABI.md); each starts
through `_start`, returns an `i16` value in `a1`, restores SP=1024/FP=0, then HALTs.
They are LLVM IR inputs, not C programs. Expected register values below are unsigned 16-bit words.

| Source | Coverage | Expected a1 |
|---|---|---|
| [constant.ll](llvm/constant.ll) | Full-width constant | 43981 |
| [arithmetic.ll](llvm/arithmetic.ll) | Arithmetic and bitwise operations | 836 |
| [comparisons.ll](llvm/comparisons.ll) | Signed and unsigned conditions | 3099 |
| [booleans.ll](llvm/booleans.ll) | i1/i16 conversion | 23 |
| [bool_branch.ll](llvm/bool_branch.ll) | Low-bit truncation followed by branching | 13 |
| [bool_phi.ll](llvm/bool_phi.ll) | i1 PHI, branch and select | 17 |
| [phi_loop.ll](llvm/phi_loop.ll) | Loop PHI | 45 |
| [select.ll](llvm/select.ll) | Conditional values | 65521 |
| [minmax_abs.ll](llvm/minmax_abs.ll) | Internal min/max/absolute-value selection patterns | 126 |
| [calls.ll](llvm/calls.ll) | Internal function calls | 133 |
| [factorial.ll](llvm/factorial.ll) | Recursive factorial | 120 |
| [call_live_values.ll](llvm/call_live_values.ll) | Live values across calls and spills | 117 |
| [stack_array.ll](llvm/stack_array.ll) | Fixed array, constant GEP and large frame | 666 |
| [memory_word_ops.ll](llvm/memory_word_ops.ll) | Word memory, high/low byte extraction and recombination | 52651 |
| [far_branch.ll](llvm/far_branch.ll) | Branch relaxation | 32771 |
| [shift_boundaries.ll](llvm/shift_boundaries.ll) | Valid i16 shift boundaries | 32769 |

From the repository root:

```bash
cd software
python3 -m opencpu compile examples/llvm/factorial.ll --backend llvm -o /tmp/llvm-factorial.bin --assembly /tmp/llvm-factorial.asm
python3 -m opencpu run /tmp/llvm-factorial.bin
cd ..
make -C hardware run IMAGE=/tmp/llvm-factorial.bin TRACE=build/llvm-factorial.vcd
```

The IDE chooses LLVM when opening `.ll`; use **Tools > Compiler backend** to change the
current document's selection, then **Run > Assemble**. Compilation is asynchronous and
**Stop** cancels it. The same binary format works with the independent downloader.

Run all independent expected-result/software checks with
`python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v` from the repository root.
`make -C hardware test-llvm` additionally exercises the real UART upload and RTL path.
These explicit native tests require the real OpenCPU LLVM tools and fail if they are absent.
