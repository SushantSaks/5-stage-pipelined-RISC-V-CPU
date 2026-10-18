# ==============================================================================
# Cocotb Simulation Makefile for RV32I Processor Modules
# Simulator: Icarus Verilog (iverilog)
# ==============================================================================

# Ensure ~/.local/bin is available in PATH for cocotb-config
export PATH := $(HOME)/.local/bin:$(PATH)

# Simulator configuration
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Test selection: configurable via CLI (e.g. make MODULE=test_regfile TOPLEVEL=regfile)
MODULE ?= test_alu
TOPLEVEL ?= alu

# Forward MODULE to COCOTB_TEST_MODULES for Cocotb 2.x compatibility
COCOTB_TEST_MODULES ?= $(MODULE)

# Dynamic build directory per TOPLEVEL
SIM_BUILD = sim_build_$(TOPLEVEL)

# Paths
PWD_DIR = $(shell pwd)
RTL_DIR = $(PWD_DIR)/../rtl

# Select Verilog source files based on the specified TOPLEVEL
ifeq ($(wildcard $(RTL_DIR)/$(TOPLEVEL).v),)
  VERILOG_SOURCES = $(wildcard $(RTL_DIR)/*.v)
else
  VERILOG_SOURCES = $(RTL_DIR)/$(TOPLEVEL).v
endif

# Compiler arguments for Icarus Verilog (enable modern Verilog/SystemVerilog constructs)
ifeq ($(SIM),icarus)
  COMPILE_ARGS += -g2012
endif

# Locate Cocotb makefiles directory dynamically
COCOTB_MAKEFILES ?= $(shell cocotb-config --makefiles 2>/dev/null || python3 -c "import cocotb_tools.config; print(cocotb_tools.config.share_dir + '/makefiles')")
include $(COCOTB_MAKEFILES)/Makefile.sim

# Convenience shorthand targets
.PHONY: test_alu test_regfile test_all clean_all

test_alu:
	$(MAKE) MODULE=test_alu TOPLEVEL=alu SIM_BUILD=sim_build_alu

test_regfile:
	$(MAKE) MODULE=test_regfile TOPLEVEL=regfile SIM_BUILD=sim_build_regfile

test_all: test_alu test_regfile

clean_all:
	rm -rf sim_build* __pycache__ *.vcd results.xml
