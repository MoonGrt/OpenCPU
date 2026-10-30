FROM ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive

ENV LANG=C.UTF-8 \
    LC_ALL=C.UTF-8

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        ca-certificates git make g++ cmake ninja-build python3 python3-venv python3-pip \
        libgl1 libxcb-icccm4 libxcb-image0 libxcb-keysyms1 \
        libxcb-render-util0 libxcb-shape0 libxcb-xinerama0 libxcb-xkb1 \
        libxkbcommon-x11-0 \
        verilator iverilog gtkwave \
    && rm -rf /var/lib/apt/lists/*

RUN git config --global core.autocrlf input \
    && git config --global --add safe.directory '*' \
    && git config --global user.name "MoonGrt" \
    && git config --global user.email "1561145394@qq.com"

WORKDIR /workspace/OpenCPU
CMD ["bash"]
