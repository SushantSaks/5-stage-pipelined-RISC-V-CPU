"""
test_single_cycle.py - Cocotb Testbench for RV32I Single-Cycle Processor
========================================================================
Verifies the end-to-end execution of a preloaded assembly program from inst_mem.mem.
- Tests R-type, I-type (ALU and Load), S-type Store, and B-type Branch instructions.
- Verifies PC incrementation, branch branching, register file writebacks, and memory stores.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_single_cycle_execution(dut):
    """Verify single-cycle CPU execution of program instructions over 25 clock cycles."""
    dut._log.info("==================================================================")
    dut._log.info(" Starting RV32I Single-Cycle Processor Cocotb Testbench           ")
    dut._log.info("==================================================================")

    # 1. Start 100 MHz clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 2. Asynchronous reset sequence: assert reset for 2 clock cycles
    dut._log.info("Asserting reset for 2 cycles...")
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Deassert reset
    dut.reset.value = 0
    dut._log.info("Reset deasserted. CPU executing instructions from 0x00000000...")

    # 3. Clock the CPU for 25 cycles to allow the program in inst_mem.mem to execute
    for cycle in range(1, 26):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Let combinational signals settle

        pc_val = int(dut.PC.value)
        instr_val = int(dut.Instr.value)
        dut._log.info(f"[Cycle {cycle:02d}] PC: 0x{pc_val:08X} | Instr: 0x{instr_val:08X}")

    dut._log.info("Execution complete. Inspecting architectural state...")

    # 4. Assert register values from Register File
    # x1 = 5 (from addi x1, x0, 5)
    # x2 = 10 (from addi x2, x0, 10)
    # x3 = 15 (from add x3, x1, x2)
    # x4 = 15 (from lw x4, 4(x0) after sw x3, 4(x0))
    # x5 = 42 (from addi x5, x0, 42; confirms beq skipped addi x5, x0, 1)
    val_x1 = int(dut.u_regfile.rf[1].value)
    val_x2 = int(dut.u_regfile.rf[2].value)
    val_x3 = int(dut.u_regfile.rf[3].value)
    val_x4 = int(dut.u_regfile.rf[4].value)
    val_x5 = int(dut.u_regfile.rf[5].value)

    dut._log.info(f"Register x1: {val_x1} (Expected: 5)")
    dut._log.info(f"Register x2: {val_x2} (Expected: 10)")
    dut._log.info(f"Register x3: {val_x3} (Expected: 15)")
    dut._log.info(f"Register x4: {val_x4} (Expected: 15)")
    dut._log.info(f"Register x5: {val_x5} (Expected: 42)")

    assert val_x1 == 5, f"Mismatch in x1: expected 5, got {val_x1}"
    assert val_x2 == 10, f"Mismatch in x2: expected 10, got {val_x2}"
    assert val_x3 == 15, f"Mismatch in x3: expected 15, got {val_x3}"
    assert val_x4 == 15, f"Mismatch in x4 (Load Word): expected 15, got {val_x4}"
    assert val_x5 == 42, (
        f"Mismatch in x5 (Branch logic test): expected 42, got {val_x5}. "
        "Branch may not have been taken or instruction was not skipped."
    )

    # 5. Assert DataMemory values (stored via sw instructions)
    # Address 4 (Word index 1): 15 (stored from x3)
    # Address 8 (Word index 2): 42 (stored from x5)
    dmem_word1 = int(dut.u_dmem.ram[1].value)
    dmem_word2 = int(dut.u_dmem.ram[2].value)

    dut._log.info(f"DataMemory[Address 4] (Word 1): {dmem_word1} (Expected: 15)")
    dut._log.info(f"DataMemory[Address 8] (Word 2): {dmem_word2} (Expected: 42)")

    assert dmem_word1 == 15, f"DataMemory[4] mismatch: expected 15, got {dmem_word1}"
    assert dmem_word2 == 42, f"DataMemory[8] mismatch: expected 42, got {dmem_word2}"

    dut._log.info("==================================================================")
    dut._log.info(" [SUCCESS] RV32I Single-Cycle Processor Verification PASSED!     ")
    dut._log.info("==================================================================")
