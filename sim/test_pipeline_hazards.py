"""
test_pipeline_hazards.py - Cocotb Testbench for 5-Stage RV32I Processor with Hazard Unit
========================================================================================
Phase 4 Verification: Hazard Resolution
Verifies:
1. RAW data hazards resolved via EX-to-EX and MEM-to-EX data forwarding.
2. Load-Use data hazard resolved via 1-cycle pipeline stall (StallF, StallD, FlushE).
3. Control hazard (branch taken) resolved via pipeline flush (FlushD, FlushE).
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_pipeline_hazard_resolution(dut):
    """Verify execution of program with RAW hazards, Load-Use stalls, and branch flushes."""
    dut._log.info("==================================================================")
    dut._log.info(" Starting Phase 4: 5-Stage Pipeline Hazard Resolution Verification")
    dut._log.info("==================================================================")

    # 1. Start 100 MHz clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 2. Comprehensive Hazard Verification Program
    # --------------------------------------------------------------------------
    # 0x00: addi x1, x0, 10    # x1 = 10
    # 0x04: addi x2, x1, 5     # RAW on x1 (EX->EX forwarding): x2 = 15
    # 0x08: add  x3, x1, x2    # RAW on x1 (MEM->EX) & x2 (EX->EX): x3 = 25
    # 0x0C: sw   x3, 4(x0)     # Store 25 at byte address 4 (word 1)
    # 0x10: lw   x4, 4(x0)     # Load 25 into x4
    # 0x14: addi x5, x4, 10    # Load-Use hazard on x4! Stalls 1 cycle, forwards x4: x5 = 35
    # 0x18: beq  x3, x4, 8     # Branch taken (25 == 25)! Flushes 0x1C, jumps to 0x20
    # 0x1C: addi x6, x0, 99    # Target to be FLUSHED! Must not commit
    # 0x20: addi x6, x0, 42    # Branch target committed: x6 = 42
    # 0x24: nop
    # --------------------------------------------------------------------------
    hazard_program = [
        0x00A00093,  # 0x00: addi x1, x0, 10
        0x00508113,  # 0x04: addi x2, x1, 5
        0x002081B3,  # 0x08: add  x3, x1, x2
        0x00302223,  # 0x0C: sw   x3, 4(x0)
        0x00402203,  # 0x10: lw   x4, 4(x0)
        0x00A20293,  # 0x14: addi x5, x4, 10
        0x00418463,  # 0x18: beq  x3, x4, 8
        0x06300313,  # 0x1C: addi x6, x0, 99 (flushed)
        0x02A00313,  # 0x20: addi x6, x0, 42 (branch target)
        0x00000013,  # 0x24: nop
        0x00000013,  # 0x28: nop
        0x00000013,  # 0x2C: nop
    ]

    # Preload instruction memory
    for idx, instr in enumerate(hazard_program):
        dut.u_imem.memory_array[idx].value = instr

    # 3. Asynchronous reset sequence
    dut._log.info("Asserting reset for 2 clock cycles...")
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Deassert reset
    dut.reset.value = 0
    dut._log.info("Reset deasserted. Running hazard resolution program for 30 cycles...")

    # 4. Clock the CPU for 30 cycles
    for cycle in range(1, 31):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        pcf_val = int(dut.PCF.value)
        fwd_a = int(dut.ForwardAE.value)
        fwd_b = int(dut.ForwardBE.value)
        stall_f = int(dut.StallF.value)
        flush_e = int(dut.FlushE.value)

        dut._log.info(
            f"[Cycle {cycle:02d}] PC: 0x{pcf_val:08X} | "
            f"FwdA: {fwd_a:02b} | FwdB: {fwd_b:02b} | "
            f"StallF: {stall_f} | FlushE: {flush_e} | "
            f"x1: {int(dut.u_regfile.rf[1].value)} | "
            f"x2: {int(dut.u_regfile.rf[2].value)} | "
            f"x3: {int(dut.u_regfile.rf[3].value)} | "
            f"x4: {int(dut.u_regfile.rf[4].value)} | "
            f"x5: {int(dut.u_regfile.rf[5].value)} | "
            f"x6: {int(dut.u_regfile.rf[6].value)}"
        )

    # 5. Assert final register state
    val_x1 = int(dut.u_regfile.rf[1].value)
    val_x2 = int(dut.u_regfile.rf[2].value)
    val_x3 = int(dut.u_regfile.rf[3].value)
    val_x4 = int(dut.u_regfile.rf[4].value)
    val_x5 = int(dut.u_regfile.rf[5].value)
    val_x6 = int(dut.u_regfile.rf[6].value)

    dut._log.info("--- Verification Results ---")
    dut._log.info(f"x1 (addi x1, x0, 10)       : {val_x1} (Expected: 10)")
    dut._log.info(f"x2 (addi x2, x1, 5  [RAW]) : {val_x2} (Expected: 15)")
    dut._log.info(f"x3 (add  x3, x1, x2 [RAW]) : {val_x3} (Expected: 25)")
    dut._log.info(f"x4 (lw   x4, 4(x0))        : {val_x4} (Expected: 25)")
    dut._log.info(f"x5 (addi x5, x4, 10 [LwUse]): {val_x5} (Expected: 35)")
    dut._log.info(f"x6 (beq branch target jump): {val_x6} (Expected: 42, flushed 99)")

    assert val_x1 == 10, f"RAW failure x1: expected 10, got {val_x1}"
    assert val_x2 == 15, f"EX-to-EX Forwarding failure x2: expected 15, got {val_x2}"
    assert val_x3 == 25, f"MEM-to-EX Forwarding failure x3: expected 25, got {val_x3}"
    assert val_x4 == 25, f"Load Word failure x4: expected 25, got {val_x4}"
    assert val_x5 == 35, (
        f"Load-Use Stall failure x5: expected 35, got {val_x5}. "
        "Pipeline stall for load-use hazard did not execute correctly."
    )
    assert val_x6 == 42, (
        f"Branch Flush failure x6: expected 42, got {val_x6}. "
        "Instruction 0x1C (addi x6, x0, 99) was not flushed when branch was taken."
    )

    # 6. Verify Memory value
    dmem_word1 = int(dut.u_dmem.ram[1].value)
    dut._log.info(f"DataMemory[4] : {dmem_word1} (Expected: 25)")
    assert dmem_word1 == 25, f"DataMemory[4] store mismatch: expected 25, got {dmem_word1}"

    dut._log.info("==================================================================")
    dut._log.info(" [SUCCESS] All Hazard Unit Verifications PASSED!                 ")
    dut._log.info("==================================================================")
