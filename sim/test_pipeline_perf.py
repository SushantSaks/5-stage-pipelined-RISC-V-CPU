"""
test_pipeline_perf.py - Cocotb benchmark for 5-stage RV32I pipeline
===================================================================
Runs a 20-iteration array accumulation workload to exercise:
- RAW hazards with EX/MEM forwarding
- Load-use dependencies with 1-cycle stalls
- Control hazards with branch flushes
Samples hardware counters on each cycle and writes results to results/pipeline_stats.csv.
"""

import csv
import os
import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer


@cocotb.test()
async def test_pipeline_performance(dut):
    """Run pipeline performance benchmark and record throughput metrics."""
    dut._log.info("Starting RV32I pipeline benchmark run...")

    # Start 100 MHz clock (10 ns period)
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # 2. Benchmark Assembly Program (20-iteration compute and memory array accumulation)
    # Exercises:
    # - Consecutive RAW dependencies (EX->EX and MEM->EX forwarding)
    # - Store-Load sequences followed by dependent ALU operations (Load-Use 1-cycle stall)
    # - Loop branch condition tests and branch flushing
    # --------------------------------------------------------------------------
    # 0x00: addi x1, x0, 0       # x1 (sum) = 0
    # 0x04: addi x2, x0, 0       # x2 (i) = 0
    # 0x08: addi x3, x0, 20      # x3 (N) = 20 iterations
    # 0x0C: addi x4, x0, 16      # x4 (data memory base address) = 16
    # loop_start (0x10):
    # 0x10: sw   x2, 0(x4)       # mem[x4] = i (store current index)
    # 0x14: lw   x5, 0(x4)       # x5 = mem[x4] (Load-Use hazard with next instruction!)
    # 0x18: add  x1, x1, x5      # sum = sum + val (RAW hazard on x5: triggers 1-cycle Load-Use stall)
    # 0x1C: addi x6, x1, 10      # RAW hazard on x1: triggers EX-to-EX forwarding
    # 0x20: addi x2, x2, 1       # i = i + 1
    # 0x24: sub  x7, x3, x2      # diff = N - i (triggers EX-to-EX forwarding from addi x2)
    # 0x28: beq  x7, x0, 16      # if diff == 0, branch to exit (0x38)
    # 0x2C: beq  x0, x0, -28     # Unconditional branch to loop_start (0x10). Flushes 2 instructions!
    # exit (0x38):
    # 0x30: sw   x1, 4(x4)       # mem[x4 + 4] = sum
    # 0x34: lw   x8, 4(x4)       # x8 = sum
    # 0x38: addi x9, x8, 100     # x9 = sum + 100
    # 0x3C: beq  x0, x0, 0       # halt loop (beq x0, x0, 0)
    # --------------------------------------------------------------------------
    benchmark_program = [
        0x00000093,  # 0x00: addi x1, x0, 0
        0x00000113,  # 0x04: addi x2, x0, 0
        0x01400193,  # 0x08: addi x3, x0, 20
        0x01000213,  # 0x0C: addi x4, x0, 16
        0x00222023,  # 0x10: sw   x2, 0(x4)
        0x00022283,  # 0x14: lw   x5, 0(x4)
        0x005080B3,  # 0x18: add  x1, x1, x5
        0x00A08313,  # 0x1C: addi x6, x1, 10
        0x00110113,  # 0x20: addi x2, x2, 1
        0x402183B3,  # 0x24: sub  x7, x3, x2
        0x00038863,  # 0x28: beq  x7, x0, 16 (branch to 0x38 on completion)
        0xFE0002E3,  # 0x2C: beq  x0, x0, -28 (branch back to 0x10)
        0x00122223,  # 0x30: sw   x1, 4(x4)
        0x00422403,  # 0x34: lw   x8, 4(x4)
        0x06440493,  # 0x38: addi x9, x8, 100
        0x00000063,  # 0x3C: beq  x0, x0, 0 (self-loop halt)
    ]

    # Preload instruction memory array
    for idx, instr in enumerate(benchmark_program):
        dut.u_imem.memory_array[idx].value = instr

    # 3. Performance metric counters
    total_cycles = 0
    stall_count = 0
    flush_count = 0
    executed_instructions = 0

    # 4. Monitoring Coroutine
    async def monitor_performance():
        nonlocal total_cycles, stall_count, flush_count, executed_instructions
        while True:
            await RisingEdge(dut.clk)
            await Timer(1, units="ps")  # allow combinational hazard and control signals to settle

            if int(dut.reset.value) == 0:
                total_cycles += 1

                # Sample StallD from Hazard Unit (load-use stalls)
                if int(dut.u_hazard.StallD.value) == 1:
                    stall_count += 1

                # Sample FlushE from Hazard Unit (load-use stall bubble OR branch flush)
                if int(dut.u_hazard.FlushE.value) == 1:
                    flush_count += 1

                # Track successfully executed instructions in EX stage
                # A valid instruction in EX has PCPlus4E != 0 (bubbles have PCPlus4E == 0)
                if int(dut.PCPlus4E.value) != 0:
                    executed_instructions += 1

    # Start monitoring in background
    monitor_task = cocotb.start_soon(monitor_performance())

    # 5. Reset Sequence
    dut._log.info("Asserting reset for 2 clock cycles...")
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0
    dut._log.info("Reset deasserted. Running benchmark for 250 clock cycles...")

    # 6. Execute benchmark for 250 cycles (> 200 cycles requirement)
    for _ in range(250):
        await RisingEdge(dut.clk)

    # Stop monitoring
    monitor_task.kill()

    # 7. Compute Performance Metrics
    ipc = (executed_instructions / total_cycles) if total_cycles > 0 else 0.0
    cpi = (total_cycles / executed_instructions) if executed_instructions > 0 else 0.0

    dut._log.info("==================================================================")
    dut._log.info(" Performance Benchmark Completed Successfully!                  ")
    dut._log.info("==================================================================")
    dut._log.info(f" Total Clock Cycles     : {total_cycles}")
    dut._log.info(f" Executed Instructions  : {executed_instructions}")
    dut._log.info(f" Stall Cycles (StallD)  : {stall_count}")
    dut._log.info(f" Flush Cycles (FlushE)  : {flush_count}")
    dut._log.info(f" IPC (Instr Per Cycle)  : {ipc:.4f}")
    dut._log.info(f" CPI (Cycles Per Instr) : {cpi:.4f}")
    dut._log.info("==================================================================")

    # 8. Export metrics to results/pipeline_stats.csv
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    results_dir = os.path.join(repo_root, "results")
    os.makedirs(results_dir, exist_ok=True)
    csv_path = os.path.join(results_dir, "pipeline_stats.csv")

    with open(csv_path, "w", newline="") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["Metric", "Value"])
        writer.writerow(["Total Cycles", total_cycles])
        writer.writerow(["Executed Instructions", executed_instructions])
        writer.writerow(["Stalls", stall_count])
        writer.writerow(["Flushes", flush_count])
        writer.writerow(["IPC", f"{ipc:.4f}"])
        writer.writerow(["CPI", f"{cpi:.4f}"])

    dut._log.info(f"Pipeline statistics saved to: {csv_path}")

    # Assertions ensuring valid benchmark completion
    assert total_cycles >= 200, f"Expected at least 200 cycles, got {total_cycles}"
    assert executed_instructions > 0, "No instructions executed!"
    assert os.path.exists(csv_path), f"CSV statistics file {csv_path} was not created!"
