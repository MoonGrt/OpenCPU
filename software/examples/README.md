# Current examples

These source files use the current [ISA v2](../../docs/ISA.md). Build outputs belong in a
temporary or user-selected directory, so the repository has no stale generated binaries.

| Source | Expected result |
|---|---|
| [isa.asm](isa.asm) | RAM word 0 = 0xabcc (43980), then HALT |
| [loops.oc](loops.oc) | X=15, Y=11, i=3 |
| [functions.oc](functions.oc) | result=120, using recursive calls |

From the repository root:

```bash
cd software
python3 -m opencpu assemble examples/isa.asm -o /tmp/isa.bin
python3 -m opencpu run /tmp/isa.bin
python3 -m opencpu compile examples/loops.oc -o /tmp/loops.bin --assembly /tmp/loops.asm
python3 -m opencpu run /tmp/loops.bin
python3 -m opencpu compile examples/functions.oc -o /tmp/functions.bin
python3 -m opencpu run /tmp/functions.bin
cd ..
```

In the IDE, open any example and choose **Run > Assemble**, followed by **Run**, **Run step**
or **Run undo**. RAM uses word addresses. The compiler stores main's variables below fp=1022;
the first declared variable is at word 1021. `.oc` files use the small integer source language,
`.asm` files are assembly, and `.bin` files are binary text with one 16-bit word per line.

Use `--pad-rom` when building a complete 1024-word image to overwrite a previous ROM tail.
The downloader window can open the resulting binary directly. See the [software guide](../README.md).
