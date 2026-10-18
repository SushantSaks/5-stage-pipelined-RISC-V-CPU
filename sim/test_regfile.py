"""
test_regfile.py - Cocotb Testbench for RV32I 32x32-bit Register File
===================================================================
Verifies:
1. Clock generation using cocotb.clock.Clock started with cocotb.start_soon().
2. Register x0 hardwired zero immutability (write to rd=0 is ignored).
3. Synchronous write to registers x1..x31 on posedge clk.
4. Immediate dual asynchronous read ports (rs1, rs2) without waiting for a clock edge.
5. Write-enable gate verification (no overwrite when we=0).
"""

import random
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_regfile_x0_immutability(dut):
    """Verify that writing to rd=0 is strictly ignored and x0 remains 32'b0."""
    dut._log.info("--- Starting Test: Register x0 Immutability ---")

    # Start 100 MHz clock (10 ns period: 5 ns high, 5 ns low)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Initialize control and address signals
    dut.we.value = 0
    dut.rs1.value = 0
    dut.rs2.value = 0
    dut.rd.value = 0
    dut.wd.value = 0
    await RisingEdge(dut.clk)

    # Initial check: x0 must read 0 asynchronously
    dut.rs1.value = 0
    dut.rs2.value = 0
    await Timer(1, units="ns")
    assert int(dut.rd1.value) == 0, f"Initial rd1 for x0 is non-zero: 0x{int(dut.rd1.value):08X}"
    assert int(dut.rd2.value) == 0, f"Initial rd2 for x0 is non-zero: 0x{int(dut.rd2.value):08X}"

    # Attempt multiple writes to register x0 with various non-zero patterns
    test_values = [
        0xFFFFFFFF,
        0xDEADBEEF,
        0x12345678,
        0x80000000,
        0x7FFFFFFF,
        0xAAAAAAAA,
        0x55555555,
    ]

    for val in test_values:
        dut._log.info(f"Attempting write to x0 (rd=0) with value: 0x{val:08X}")
        dut.we.value = 1
        dut.rd.value = 0
        dut.wd.value = val

        # Write happens synchronously on rising edge of clk
        await RisingEdge(dut.clk)

        # Deassert write enable
        dut.we.value = 0

        # Asynchronously verify x0 on both read ports immediately (without another clock edge)
        dut.rs1.value = 0
        dut.rs2.value = 0
        await Timer(1, units="ns")  # Combinational propagation delay

        assert int(dut.rd1.value) == 0, (
            f"x0 immutability violated on rd1! Wrote 0x{val:08X}, read 0x{int(dut.rd1.value):08X}"
        )
        assert int(dut.rd2.value) == 0, (
            f"x0 immutability violated on rd2! Wrote 0x{val:08X}, read 0x{int(dut.rd2.value):08X}"
        )

    dut._log.info("[PASS] Register x0 successfully verified to be strictly immutable (hardwired 0).")


@cocotb.test()
async def test_regfile_write_and_immediate_async_read(dut):
    """
    Write random values to x1..x31 on posedge clk, and immediately verify
    that dual asynchronous read ports (rs1, rs2) reflect correct data without clock wait.
    """
    dut._log.info("--- Starting Test: Synchronous Write & Immediate Dual Asynchronous Read ---")

    # Start 100 MHz clock
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    random.seed(12345)
    shadow_rf = [0] * 32  # Python reference register file model

    # Initialize signals
    dut.we.value = 0
    dut.rs1.value = 0
    dut.rs2.value = 0
    dut.rd.value = 0
    dut.wd.value = 0
    await RisingEdge(dut.clk)

    # --------------------------------------------------------------------------
    # Step 1: Write random data to x1..x31 and verify immediate asynchronous read
    # --------------------------------------------------------------------------
    for reg_idx in range(1, 32):
        val = random.randint(0, 0xFFFFFFFF)
        shadow_rf[reg_idx] = val

        dut._log.info(f"Writing x{reg_idx} <= 0x{val:08X} on posedge clk...")
        dut.we.value = 1
        dut.rd.value = reg_idx
        dut.wd.value = val

        # Synchronous write takes place at rising edge
        await RisingEdge(dut.clk)

        # Immediately deassert write enable
        dut.we.value = 0

        # IMMEDIATELY verify asynchronous read without waiting for another clock edge
        # Test rs1 with the newly written register, and rs2 with x0
        dut.rs1.value = reg_idx
        dut.rs2.value = 0
        await Timer(1, units="ns")  # 1 ns combinational settling (10% of clock period, no posedge)

        actual_rd1 = int(dut.rd1.value)
        actual_rd2 = int(dut.rd2.value)

        assert actual_rd1 == val, (
            f"Immediate async read failed on rd1 for x{reg_idx}! "
            f"Expected: 0x{val:08X}, Got: 0x{actual_rd1:08X}"
        )
        assert actual_rd2 == 0, (
            f"Immediate async read failed on rd2 for x0! "
            f"Expected: 0x00000000, Got: 0x{actual_rd2:08X}"
        )

        # Also swap ports: rs1 = x0, rs2 = reg_idx
        dut.rs1.value = 0
        dut.rs2.value = reg_idx
        await Timer(1, units="ns")

        actual_rd1 = int(dut.rd1.value)
        actual_rd2 = int(dut.rd2.value)

        assert actual_rd1 == 0, f"Port swap: rd1 expected 0, got 0x{actual_rd1:08X}"
        assert actual_rd2 == val, f"Port swap: rd2 expected 0x{val:08X}, got 0x{actual_rd2:08X}"

    dut._log.info("[PASS] All registers x1..x31 written and immediately verified via async read.")

    # --------------------------------------------------------------------------
    # Step 2: Comprehensive Dual Asynchronous Read Sweep (Combinational Check)
    # --------------------------------------------------------------------------
    dut._log.info("Testing simultaneous dual-port reads across all paired registers...")
    for i in range(32):
        r1 = i
        r2 = (31 - i)

        # Update read addresses purely combinational (NO clock edges)
        dut.rs1.value = r1
        dut.rs2.value = r2
        await Timer(1, units="ns")

        expected_rd1 = shadow_rf[r1]
        expected_rd2 = shadow_rf[r2]
        actual_rd1 = int(dut.rd1.value)
        actual_rd2 = int(dut.rd2.value)

        assert actual_rd1 == expected_rd1, (
            f"Dual read mismatch rd1 (x{r1}): Expected 0x{expected_rd1:08X}, Got 0x{actual_rd1:08X}"
        )
        assert actual_rd2 == expected_rd2, (
            f"Dual read mismatch rd2 (x{r2}): Expected 0x{expected_rd2:08X}, Got 0x{actual_rd2:08X}"
        )

    dut._log.info("[PASS] Dual asynchronous read sweep completed successfully.")

    # --------------------------------------------------------------------------
    # Step 3: Write-Enable Gate Verification (we = 0 should prevent modification)
    # --------------------------------------------------------------------------
    dut._log.info("Verifying write-enable disable gate (we = 0)...")
    target_reg = 10
    original_val = shadow_rf[target_reg]
    bogus_val = 0xBAD0F00D

    dut.we.value = 0
    dut.rd.value = target_reg
    dut.wd.value = bogus_val

    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)

    dut.rs1.value = target_reg
    await Timer(1, units="ns")

    assert int(dut.rd1.value) == original_val, (
        f"Write enable gate failed! Register x{target_reg} was overwritten when we=0. "
        f"Expected: 0x{original_val:08X}, Got: 0x{int(dut.rd1.value):08X}"
    )

    dut._log.info("[PASS] Write enable gating verified. All Register File tests PASSED!")
