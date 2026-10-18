"""
test_run.py - Trace ALUControlE and pipeline execution cycle by cycle
"""

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, Timer

ALU_OPS = {
    0b0000: "ADD",
    0b0001: "SUB",
    0b0010: "AND",
    0b0011: "OR",
    0b0100: "XOR",
    0b0101: "SLT",
    0b0110: "SLTU",
    0b0111: "SLL",
    0b1000: "SRL",
    0b1001: "SRA",
}

@cocotb.test()
async def trace_alucontrol(dut):
    """Run pipeline and log ALUControlE for each instruction in EX stage."""
    cocotb.start_soon(Clock(dut.clk, 10, units="ns").start())

    # Assert reset
    dut.reset.value = 1
    await RisingEdge(dut.clk)
    await RisingEdge(dut.clk)
    dut.reset.value = 0

    print("=" * 85)
    print(f"{'Cycle':<7}{'PCF':<8}{'PCE':<8}{'ALUControlE':<15}{'Op':<6}{'SrcAE':<8}{'SrcBE':<8}{'ALURes':<10}{'ZeroE':<7}{'PCSrcE':<8}")
    print("=" * 85)

    for cycle in range(1, 15):
        await RisingEdge(dut.clk)
        await Timer(1, units="ns")

        pcf = int(dut.PCF.value)
        pce = int(dut.PCE.value)
        alu_ctrl = int(dut.ALUControlE.value)
        src_a = int(dut.SrcAE.value)
        src_b = int(dut.SrcBE.value)
        alu_res = int(dut.ALUResultE.value)
        zero = int(dut.ZeroE.value)
        pc_src = int(dut.PCSrcE.value)
        op_name = ALU_OPS.get(alu_ctrl, "UNKNOWN")

        print(
            f"{cycle:<7}0x{pcf:02X}    0x{pce:02X}    {alu_ctrl:04b} ({alu_ctrl})     {op_name:<6}{src_a:<8}{src_b:<8}{alu_res:<10}{zero:<7}{pc_src:<8}"
        )

    print("=" * 85)
    print(
        f"Final Regs: x1={int(dut.u_regfile.rf[1].value)}, "
        f"x2={int(dut.u_regfile.rf[2].value)}, "
        f"x3={int(dut.u_regfile.rf[3].value)}, "
        f"x4={int(dut.u_regfile.rf[4].value)}, "
        f"x5={int(dut.u_regfile.rf[5].value)}"
    )
    print("=" * 85)
