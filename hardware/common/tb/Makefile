.DEFAULT_GOAL := test
.PHONY: all build lint test run clean

TB_DIR := $(abspath $(dir $(lastword $(MAKEFILE_LIST))))
ROOT := $(abspath $(TB_DIR)/../../..)
RTL_DIR := $(ROOT)/hardware/verilog
BUILD_DIR ?= $(TB_DIR)/build
SIM := $(BUILD_DIR)/obj_dir/Vtb_soc
PYTHON ?= python3
VERILATOR ?= verilator
JOBS ?= 2
IMAGE ?= $(BUILD_DIR)/isa.bin
TRACE ?=
MAX_CYCLES ?= 10000
ARGS ?=

RTL_SOURCES := $(addprefix $(RTL_DIR)/,$(shell sed -e 's/\#.*//' -e '/^[[:space:]]*$$/d' $(RTL_DIR)/files.f))
HEADERS := $(wildcard $(RTL_DIR)/include/*.vh)
TOOLCHAIN := $(wildcard $(ROOT)/software/opencpu/core/*.py $(ROOT)/software/opencpu/core/compiler/*.py)
# uart.v deliberately holds uart_rx and uart_tx as well as uart.
FLAGS := --language 1364-2005 --timescale 1ns/1ns -Wall \
         -Wno-UNUSED -Wno-PINCONNECTEMPTY -Wno-SYMRSVDWORD -Wno-DECLFILENAME \
         -I$(RTL_DIR)/include

all: lint test

build: $(SIM)

$(SIM): $(RTL_SOURCES) $(HEADERS) $(RTL_DIR)/files.f $(TB_DIR)/tb_soc.v $(TB_DIR)/sim_main.cpp $(TB_DIR)/Makefile
	mkdir -p "$(BUILD_DIR)"
	$(VERILATOR) $(FLAGS) --cc --exe --build -j $(JOBS) --trace -DTUBE \
		--top-module tb_soc --Mdir "$(BUILD_DIR)/obj_dir" \
		-CFLAGS "-std=c++14 -Wall -Wextra" \
		$(RTL_SOURCES) "$(TB_DIR)/tb_soc.v" "$(TB_DIR)/sim_main.cpp"

lint:
	$(VERILATOR) $(FLAGS) --lint-only --top-module top $(RTL_SOURCES)
	$(VERILATOR) $(FLAGS) --lint-only --top-module top -DTUBE $(RTL_SOURCES)
	$(VERILATOR) $(FLAGS) --lint-only --top-module top -GENABLE_UART=0 -GENABLE_TIMER=0 $(RTL_SOURCES)
	$(VERILATOR) $(FLAGS) --lint-only --top-module top -DTUBE -GROM_DEPTH=16 -GRAM_DEPTH=16 $(RTL_SOURCES)

test: $(SIM)
	OPENCPU_SIM="$(SIM)" $(PYTHON) -B "$(TB_DIR)/test_soc.py"

$(BUILD_DIR)/isa.bin: $(ROOT)/software/examples/isa.asm $(TOOLCHAIN)
	mkdir -p "$(BUILD_DIR)"
	cd "$(ROOT)/software" && $(PYTHON) -B -m opencpu assemble "$<" -o "$@"

run: $(SIM) $(IMAGE)
	$(if $(TRACE),mkdir -p "$(dir $(TRACE))")
	"$(SIM)" --image "$(IMAGE)" --max-cycles "$(MAX_CYCLES)" $(if $(TRACE),--trace "$(TRACE)") $(ARGS)

clean:
	$(RM) -r "$(BUILD_DIR)"
