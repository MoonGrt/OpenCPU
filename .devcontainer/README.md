# OpenCPU Dev Container

This directory provides a Ubuntu 22.04 development environment for OpenCPU.
It installs Git, GTKWave, Verilator `v4.216`, SBT, and Mill `0.11.6`. The
Verilator and Mill versions follow `../OpenCPU/setup.sh`; Ubuntu 22.04's
OpenJDK 17 is used in place of the script's obsolete OpenJDK 8 PPA.

## Use with VS Code

Open the `OpenCPU` repository root in VS Code, then run **Dev Containers:
Reopen in Container**. VS Code uses `.devcontainer/docker-compose.yml` to
build the fixed image `OpenCPU:latest`, start the fixed container
`OpenCPU-dev`, mount the whole repository at `/workspace/OpenCPU`, and
open the terminal in `/workspace/OpenCPU/OpenCPU` as `root@dev`.

The configuration forwards the WSLg X11 socket, so `gtkwave` can open a window
when VS Code is launched from a WSL distribution with Docker Desktop WSL
integration enabled.

## Build

Run this command from the repository root (the directory containing
`OpenCPU`):

```bash
docker compose -f .devcontainer/docker-compose.yml build
```

## Run with WSLg GUI support

In a WSL terminal with Docker Desktop WSL integration enabled, run the
following command from the repository root. It bind-mounts the complete
repository, including the parent `.git/modules/OpenCPU` metadata required by
OpenCPU's Git submodule checkout. The working directory remains
`/workspace/OpenCPU/OpenCPU`. It also forwards the WSLg X11 socket, so
applications such as GTKWave can open windows on the Windows desktop.

```bash
docker run -it \
  --name OpenCPU \
  --hostname dev \
  -v "$PWD:/workspace/OpenCPU" \
  --workdir /workspace/OpenCPU/OpenCPU \
  -e DISPLAY="$DISPLAY" \
  -v /mnt/wslg/.X11-unix:/tmp/.X11-unix \
  OpenCPU:ubuntu22.04
```

Verify the graphical connection inside the container:

```bash
gtkwave
```

If the WSLg X11 socket is unavailable, update WSL and ensure Docker Desktop's
**Settings > Resources > WSL Integration** enables the Linux distribution in
which the command is run.

## Tool check

```bash
git --version
dpkg-query -W -f='${Version}\n' gtkwave
verilator --version
sbt --version
mill --version
```
