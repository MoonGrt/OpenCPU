.DEFAULT_GOAL := all
.PHONY: all build lint test test-llvm run clean

TB_DIR := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))common/tb

all build lint test test-llvm run clean:
	$(MAKE) -C "$(TB_DIR)" $@
