# ==============================================================================
# Cocotb Simulation Makefile for RV32I Processor Modules
# Simulator: Icarus Verilog (iverilog)
# ==============================================================================

# Ensure ~/.local/bin is available in PATH for cocotb-config
export PATH := $(HOME)/.local/bin:$(PATH)

# Simulator configuration
SIM ?= icarus
TOPLEVEL_LANG ?= verilog

# Automatically enable FST waveform dumping by default (1 = enabled, 0 = disabled)
WAVES ?= 1

# Test selection: configurable via CLI (e.g. make MODULE=test_pipeline_hazards TOPLEVEL=riscv_pipeline)
MODULE ?= test_alu
TOPLEVEL ?= alu

# Forward MODULE to COCOTB_TEST_MODULES for Cocotb 2.x compatibility
COCOTB_TEST_MODULES ?= $(MODULE)

# Dynamic build directory per TOPLEVEL
SIM_BUILD = sim_build_$(TOPLEVEL)

# Paths
PWD_DIR = $(shell pwd)
RTL_DIR = $(PWD_DIR)/../rtl

# Ensure programs/ directory is always accessible to simulator regardless of target invoked
_PROGRAMS_LINK := $(shell ln -sfn ../programs $(PWD_DIR)/programs)

# Select Verilog source files
# For top-level integration modules, all RTL files are needed
ifeq ($(TOPLEVEL),riscv_single_cycle)
  VERILOG_SOURCES = $(wildcard $(RTL_DIR)/*.v)
else ifeq ($(TOPLEVEL),riscv_pipeline)
  VERILOG_SOURCES = $(wildcard $(RTL_DIR)/*.v)
else ifeq ($(wildcard $(RTL_DIR)/$(TOPLEVEL).v),)
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
.PHONY: test_alu test_regfile test_single_cycle test_pipeline_basic test_pipeline_hazards test_all waves_alu waves_regfile waves_single_cycle waves_pipeline_basic waves_pipeline_hazards clean_all link_programs

link_programs:
	@ln -sfn ../programs $(PWD_DIR)/programs

test_alu: link_programs
	$(MAKE) MODULE=test_alu TOPLEVEL=alu SIM_BUILD=sim_build_alu WAVES=$(WAVES)
	@ln -sf alu.fst sim_build_alu/dump.fst 2>/dev/null || true

test_regfile: link_programs
	$(MAKE) MODULE=test_regfile TOPLEVEL=regfile SIM_BUILD=sim_build_regfile WAVES=$(WAVES)
	@ln -sf regfile.fst sim_build_regfile/dump.fst 2>/dev/null || true

test_single_cycle: link_programs
	$(MAKE) MODULE=test_single_cycle TOPLEVEL=riscv_single_cycle SIM_BUILD=sim_build_riscv_single_cycle WAVES=$(WAVES)
	@ln -sf riscv_single_cycle.fst sim_build_riscv_single_cycle/dump.fst 2>/dev/null || true

test_pipeline_basic: link_programs
	$(MAKE) MODULE=test_pipeline_basic TOPLEVEL=riscv_pipeline SIM_BUILD=sim_build_riscv_pipeline WAVES=$(WAVES)
	@ln -sf riscv_pipeline.fst sim_build_riscv_pipeline/dump.fst 2>/dev/null || true

test_pipeline_hazards: link_programs
	$(MAKE) MODULE=test_pipeline_hazards TOPLEVEL=riscv_pipeline SIM_BUILD=sim_build_riscv_pipeline WAVES=$(WAVES)
	@ln -sf riscv_pipeline.fst sim_build_riscv_pipeline/dump.fst 2>/dev/null || true

test_all: test_alu test_regfile test_single_cycle test_pipeline_basic test_pipeline_hazards

waves_alu: test_alu
	gtkwave sim_build_alu/alu.fst &

waves_regfile: test_regfile
	gtkwave sim_build_regfile/regfile.fst &

waves_single_cycle: test_single_cycle
	gtkwave sim_build_riscv_single_cycle/riscv_single_cycle.fst &

waves_pipeline_basic: test_pipeline_basic
	gtkwave sim_build_riscv_pipeline/riscv_pipeline.fst &

waves_pipeline_hazards: test_pipeline_hazards
	gtkwave sim_build_riscv_pipeline/riscv_pipeline.fst &

clean_all:
	rm -rf sim_build* __pycache__ *.vcd *.fst results.xml
	@ln -sfn ../programs $(PWD_DIR)/programs
