#!/usr/bin/env python3
"""Build the pinned, native OpenCPU LLVM backend without GUI dependencies."""
import argparse
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
BASE = "7a941dfb2877a0b8cf30323fefa85ad019e0b0f5"


def positive(value):
    number = int(value)
    if number <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return number


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-dir", type=Path, default=ROOT / "thirdpartys/llvm-project")
    parser.add_argument("--build-dir", type=Path, default=ROOT / "build/llvm")
    parser.add_argument("--jobs", type=positive, default=2)
    parser.add_argument("--link-jobs", type=positive, default=1)
    parser.add_argument("--configure-only", action="store_true")
    parser.add_argument("--test", action="store_true", help="also run native backend lit tests")
    args = parser.parse_args(argv)
    source = args.source_dir.expanduser().resolve()
    build = args.build_dir.expanduser().resolve()
    try:
        for tool in ("git", "cmake", "ninja", "c++"):
            if shutil.which(tool) is None:
                raise ValueError(f"required build tool not found: {tool}")
        target = source / "llvm/lib/Target/OpenCPU/CMakeLists.txt"
        if not target.is_file():
            raise ValueError(
                "OpenCPU target sources are missing. Initialize thirdpartys/llvm-project "
                "and check out the OpenCPU development branch before building."
            )
        ancestor = subprocess.run(["git", "-C", str(source), "merge-base", "--is-ancestor", BASE, "HEAD"])
        if ancestor.returncode:
            raise ValueError("LLVM checkout must descend from the pinned llvmorg-23.1.4 commit")
        cache = build / "CMakeCache.txt"
        if cache.is_file():
            prefix = "CMAKE_HOME_DIRECTORY:INTERNAL="
            previous = next((line[len(prefix):] for line in cache.read_text().splitlines()
                             if line.startswith(prefix)), None)
            if previous and Path(previous).resolve() != source / "llvm":
                print("LLVM source directory moved; refreshing CMake configuration. "
                      "Existing object files and executables are retained.", flush=True)
                cache.unlink()
                shutil.rmtree(build / "CMakeFiles", ignore_errors=True)
        command = [
            "cmake", "-G", "Ninja", "-S", str(source / "llvm"), "-B", str(build),
            "-DCMAKE_BUILD_TYPE=Release", "-DCMAKE_CXX_FLAGS_RELEASE=-O1 -DNDEBUG",
            "-DCMAKE_C_FLAGS_RELEASE=-O1 -DNDEBUG",
            "-DLLVM_TARGETS_TO_BUILD=", "-DLLVM_EXPERIMENTAL_TARGETS_TO_BUILD=OpenCPU",
            "-DLLVM_ENABLE_PROJECTS=", "-DLLVM_ENABLE_RUNTIMES=",
            "-DLLVM_INCLUDE_TESTS=ON", "-DLLVM_INCLUDE_BENCHMARKS=OFF",
            "-DLLVM_ENABLE_ASSERTIONS=ON", "-DLLVM_ENABLE_ZLIB=OFF",
            "-DLLVM_ENABLE_ZSTD=OFF", "-DLLVM_ENABLE_LIBXML2=OFF",
            "-DLLVM_ENABLE_LIBEDIT=OFF",
            f"-DLLVM_PARALLEL_COMPILE_JOBS={args.jobs}",
            f"-DLLVM_PARALLEL_LINK_JOBS={args.link_jobs}",
        ]
        subprocess.run(command, check=True)
        if args.configure_only:
            return 0
        targets = ["llc", "FileCheck"]
        if args.test:
            # LLVM's parent lit configuration probes llvm-config; its standard
            # shell substitutions also require the tiny not/count utilities.
            targets += ["llvm-config", "not", "count"]
        subprocess.run(["cmake", "--build", str(build), "--target", *targets,
                        "--parallel", str(args.jobs)], check=True)
        subprocess.run([str(build / "bin/llc"), "--version"], check=True)
        if args.test:
            subprocess.run([sys.executable, str(build / "bin/llvm-lit"), "-v",
                            str(source / "llvm/test/CodeGen/OpenCPU")], check=True)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print(f"OpenCPU LLVM build: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
