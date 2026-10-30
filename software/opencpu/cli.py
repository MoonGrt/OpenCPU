"""The shared command-line application; no GUI dependencies."""
import argparse
import json
from pathlib import Path
import sys

from .core.disassembler import Disassembler
from .core.image import ROM_WORDS, format_binary, parse_binary
from .core.isa import OPCODES, REGISTER_NAMES
from .core.simulator import Simulator
from .core.toolchain import Toolchain


def _output(text, path):
    if path:
        path.write_text(text, encoding="utf-8")
    else:
        print(text, end="" if text.endswith("\n") else "\n")


def main(argv=None):
    arguments = argparse.ArgumentParser(description="Assemble, disassemble, compile and run OpenCPU ISA v2.")
    commands = arguments.add_subparsers(dest="command", required=True)
    for name in ("assemble", "disassemble", "compile", "run"):
        command = commands.add_parser(name)
        command.add_argument("input", type=Path)
        if name != "run":
            command.add_argument("-o", "--output", type=Path)
        if name in ("assemble", "compile"):
            command.add_argument("--pad-rom", action="store_true", help="fill the 1024-word ROM image with trailing HALTs")
        if name == "compile":
            command.add_argument("--assembly", type=Path, help="also save generated assembly")
        if name == "run":
            command.add_argument("--entry", type=lambda value: int(value, 0), default=0)
            command.add_argument("--max-steps", type=int, default=Simulator.DEFAULT_MAX_STEPS)
    args = arguments.parse_args(argv)
    try:
        source = args.input.read_text(encoding="utf-8")
        if args.command == "disassemble":
            parse_binary(source)
            text = Disassembler().disassemble(source)
            _output(text + ("\n" if text else ""), args.output)
        elif args.command in ("assemble", "compile"):
            toolchain = Toolchain()
            result = toolchain.compile(source) if args.command == "compile" else toolchain.assemble(source)
            words = list(result.words)
            if args.pad_rom:
                words += [OPCODES["halt"]] * (ROM_WORDS - len(words))
            if args.command == "compile" and args.assembly:
                _output(result.assembly, args.assembly)
            _output(format_binary(words), args.output)
        else:
            if not 0 <= args.entry < 1024:
                raise ValueError("entry must be a word address in 0..1023")
            model = Simulator(args.entry)
            model.inst_mem = parse_binary(source)
            model.run(args.max_steps)
            print(json.dumps({
                "isa": "OpenCPU v2", "pc": model.pc,
                "halted": model.halted, "faulted": model.faulted,
                "fault_reason": model.fault_reason,
                "limit_reached": model.limit_reached,
                "instructions_retired": model.instructions_retired,
                "registers": dict(zip(REGISTER_NAMES, model.registers)),
                "memory": {str(address): value for address, value in sorted(model.data_mem.items())},
            }, indent=2))
            return 2 if model.faulted else 3 if model.limit_reached else 0
    except (OSError, ValueError, TypeError) as error:
        print(f"opencpu: {error}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
