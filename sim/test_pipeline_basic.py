"""
test_pipeline_basic.py - Cocotb Testbench for 5-Stage Pipelined RV32I Processor
================================================================================
Phase 3 Verification: Structural Pipeline Segmentation
- Verifies that independent, non-hazardous instructions propagate sequentially
  through the 5 stages: IF -> ID -> EX -> MEM -> WB.
- Confirms that the first instruction writes back to the Register File on the
  5th clock cycle (and NOT prematurely in earlier cycles).
- Tracks subsequent instruction writebacks on cycles 6, 7, 8, etc.
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_pipeline_basic_propagation(dut):
    """Verify 5-stage pipeline propagation of independent instructions without hazards."""
    dut._log.info("==================================================================")
    dut._log.info(" Starting Phase 3: 5-Stage Pipeline Structural Verification       ")
    dut._log.info("==================================================================")

    # 1. Start 100 MHz clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 2. Define stream of independent, non-hazardous instructions
    # Each instruction writes to a distinct register using x0 as source
    instructions = [
        0x00A00093,  # 0x00: addi x1, x0, 10
        0x01400113,  # 0x04: addi x2, x0, 20
        0x01E00193,  # 0x08: addi x3, x0, 30
        0x02800213,  # 0x0C: addi x4, x0, 40
        0x03200293,  # 0x10: addi x5, x0, 50
        0x00000013,  # 0x14: nop (addi x0, x0, 0)
        0x00000013,  # 0x18: nop
        0x00000013,  # 0x1C: nop
        0x00000013,  # 0x20: nop
        0x00000013,  # 0x24: nop
    ]

    # Preload instruction memory array
    for idx, instr in enumerate(instructions):
        dut.u_imem.memory_array[idx].value = instr

    # 3. Asynchronous reset sequence (assert reset for 2 full clock cycles)
    dut._log.info("Asserting reset for 2 clock cycles...")
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    # Deassert reset
    dut.reset.value = 0
    dut._log.info("Reset deasserted. Commencing pipeline execution...")

    # 4. Step cycle-by-cycle and verify pipeline latency
    # In a 5-stage pipeline:
    # Cycle 1: IF (Fetch instr 0: addi x1)
    # Cycle 2: ID (Decode instr 0), IF (Fetch instr 1: addi x2)
    # Cycle 3: EX (Execute instr 0), ID (Decode instr 1), IF (Fetch instr 2: addi x3)
    # Cycle 4: MEM (Memory instr 0), EX (Execute instr 1), ID (Decode instr 2), IF (Fetch instr 3)
    # Cycle 5: WB (Writeback instr 0 -> x1 receives 10!)

    for cycle in range(1, 6):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")  # Settling delay

        val_x1 = int(dut.u_regfile.rf[1].value)
        pcf_val = int(dut.PCF.value)
        dut._log.info(f"[Cycle {cycle}] PCF: 0x{pcf_val:08X} | Reg x1: {val_x1}")

        if cycle < 5:
            assert val_x1 == 0, (
                f"Premature writeback on cycle {cycle}! "
                f"x1 is {val_x1}, expected 0 before cycle 5."
            )
        else:
            # On cycle 5, the first instruction (addi x1, x0, 10) completes writeback!
            assert val_x1 == 10, (
                f"Pipeline 5th cycle writeback failed! "
                f"Expected x1=10 on cycle 5, got {val_x1}"
            )
            dut._log.info("[PASS] Verified: x1 written on the 5th clock cycle as expected!")

    # 5. Continue clocking for cycles 6 through 16 to observe subsequent writebacks
    for cycle in range(6, 17):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        val_x2 = int(dut.u_regfile.rf[2].value)
        val_x3 = int(dut.u_regfile.rf[3].value)
        val_x4 = int(dut.u_regfile.rf[4].value)
        val_x5 = int(dut.u_regfile.rf[5].value)

        dut._log.info(
            f"[Cycle {cycle:02d}] x1={int(dut.u_regfile.rf[1].value)} | "
            f"x2={val_x2} | x3={val_x3} | x4={val_x4} | x5={val_x5}"
        )

    # 6. Final verification of all registers after stream execution
    final_x1 = int(dut.u_regfile.rf[1].value)
    final_x2 = int(dut.u_regfile.rf[2].value)
    final_x3 = int(dut.u_regfile.rf[3].value)
    final_x4 = int(dut.u_regfile.rf[4].value)
    final_x5 = int(dut.u_regfile.rf[5].value)

    dut._log.info("--- Final Register State ---")
    dut._log.info(f"x1 = {final_x1} (Expected: 10)")
    dut._log.info(f"x2 = {final_x2} (Expected: 20)")
    dut._log.info(f"x3 = {final_x3} (Expected: 30)")
    dut._log.info(f"x4 = {final_x4} (Expected: 40)")
    dut._log.info(f"x5 = {final_x5} (Expected: 50)")

    assert final_x1 == 10, f"Mismatch in x1: expected 10, got {final_x1}"
    assert final_x2 == 20, f"Mismatch in x2: expected 20, got {final_x2}"
    assert final_x3 == 30, f"Mismatch in x3: expected 30, got {final_x3}"
    assert final_x4 == 40, f"Mismatch in x4: expected 40, got {final_x4}"
    assert final_x5 == 50, f"Mismatch in x5: expected 50, got {final_x5}"

    dut._log.info("==================================================================")
    dut._log.info(" [SUCCESS] 5-Stage Pipeline Structural Segmentation Test PASSED!  ")
    dut._log.info("==================================================================")
