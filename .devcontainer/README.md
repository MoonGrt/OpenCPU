# OpenCPU Dev Container

The Dockerfile provides Ubuntu 22.04 with Git, Python/venv/pip, g++, make, CMake,
Ninja, Verilator, Icarus Verilog, GTKWave, and the Linux libraries needed by the Qt GUI.
The simple compiler works without LLVM. Native OpenCPU Clang/LLVM tools are built from the
separate source submodule, rather than installed by pip or baked into the image.

## Use with VS Code

Open the OpenCPU checkout and run **Dev Containers: Reopen in Container**.
The compose service is `OpenCPU`, image `opencpu:latest`, container `opencpu-dev`,
with working directory `/workspace/OpenCPU`. The compose configuration mounts this
checkout there and forwards the WSLg X11 socket at `/mnt/wslg/.X11-unix`.
For other desktop environments, adapt that display socket mount before starting it.

From the repository root:

```bash
docker compose -f .devcontainer/docker-compose.yml build
docker compose -f .devcontainer/docker-compose.yml run --rm OpenCPU bash
```

If this checkout is itself an OpenChips submodule, its `.git` file points to metadata
outside the mounted checkout. Make that outer Git directory available inside the
container as well, or use a standalone OpenCPU clone. The current compose mount does
not automatically mount the outer repository's `.git` metadata.

## Build the optional Clang/LLVM tools

With the OpenCPU target sources present, inside the container at the repository root:

```bash
python3 toolchain/llvm/build.py --jobs 2 --link-jobs 1 --test
python3 -B -m unittest discover -s toolchain/llvm/tests -p test_native.py -v
QT_QPA_PLATFORM=offscreen software/.venv/bin/python -B -m unittest discover -s toolchain/llvm/tests -p test_native_gui.py -v
make -C hardware all
make -C hardware test-llvm
```

The full build includes Clang, bitcode linking, resource headers and the target SDK;
use `--ir-only` for LLVM IR tools without Clang. LLVM compilation is optional for the simple backend. Initialize the appropriate fork
revision as described in the [LLVM guide](../toolchain/llvm/README.md); local backend
changes must be published before a new clone can fetch the corresponding submodule version.
GUI setup and source examples are documented in the [software guide](../software/README.md).

## Tool and display checks

```bash
git --version
python3 --version
g++ --version
cmake --version
ninja --version
verilator --version
gtkwave
```

Launching GUI applications requires a valid `DISPLAY` and accessible display socket.
The forwarded WSLg socket works when VS Code/Docker are started from a WSL distribution
with Docker Desktop WSL integration enabled.
