"""
test_alu.py - Cocotb Testbench for RV32I 32-bit Combinational ALU
================================================================
Verifies all 10 RV32I ALU operations with corner-case boundary values
and randomized 32-bit signed/unsigned inputs, checking Result and Zero flag.
"""

import random
from enum import IntEnum

import cocotb
from cocotb.triggers import Timer


# ------------------------------------------------------------------------------
# 1. 4-bit ALUControl Mapping
# ------------------------------------------------------------------------------
class ALUControl(IntEnum):
    ADD  = 0b0000  # A + B
    SUB  = 0b0001  # A - B
    AND  = 0b0010  # A & B
    OR   = 0b0011  # A | B
    XOR  = 0b0100  # A ^ B
    SLT  = 0b0101  # Signed Less Than
    SLTU = 0b0110  # Unsigned Less Than
    SLL  = 0b0111  # Shift Left Logical (A << B[4:0])
    SRL  = 0b1000  # Shift Right Logical (A >> B[4:0])
    SRA  = 0b1001  # Shift Right Arithmetic ($signed(A) >>> B[4:0])


ALU_OP_NAMES = {
    ALUControl.ADD:  "ADD",
    ALUControl.SUB:  "SUB",
    ALUControl.AND:  "AND",
    ALUControl.OR:   "OR",
    ALUControl.XOR:  "XOR",
    ALUControl.SLT:  "SLT",
    ALUControl.SLTU: "SLTU",
    ALUControl.SLL:  "SLL",
    ALUControl.SRL:  "SRL",
    ALUControl.SRA:  "SRA",
}


# ------------------------------------------------------------------------------
# 2. Golden Reference Model
# ------------------------------------------------------------------------------
def compute_expected_alu(a: int, b: int, op: ALUControl) -> tuple[int, int]:
    """
    Simulate exact 32-bit hardware arithmetic, logic, and comparison.
    Handles signed/unsigned representations and overflow wrapping.
    """
    # Enforce 32-bit unsigned boundaries
    a_u = a & 0xFFFFFFFF
    b_u = b & 0xFFFFFFFF

    # Convert to 32-bit signed two's complement for signed comparison and shift
    a_s = a_u if a_u < 0x80000000 else a_u - 0x100000000
    b_s = b_u if b_u < 0x80000000 else b_u - 0x100000000

    # RISC-V shift amount is strictly the lower 5 bits of B
    shamt = b_u & 0x1F

    if op == ALUControl.ADD:
        res = (a_u + b_u) & 0xFFFFFFFF
    elif op == ALUControl.SUB:
        res = (a_u - b_u) & 0xFFFFFFFF
    elif op == ALUControl.AND:
        res = a_u & b_u
    elif op == ALUControl.OR:
        res = a_u | b_u
    elif op == ALUControl.XOR:
        res = a_u ^ b_u
    elif op == ALUControl.SLT:
        res = 1 if a_s < b_s else 0
    elif op == ALUControl.SLTU:
        res = 1 if a_u < b_u else 0
    elif op == ALUControl.SLL:
        res = (a_u << shamt) & 0xFFFFFFFF
    elif op == ALUControl.SRL:
        res = (a_u >> shamt) & 0xFFFFFFFF
    elif op == ALUControl.SRA:
        # Arithmetic right shift with sign extension
        res = (a_s >> shamt) & 0xFFFFFFFF
    else:
        # Default case returning zero
        res = 0

    zero = 1 if res == 0 else 0
    return res, zero


# ------------------------------------------------------------------------------
# 3. Comprehensive Cocotb Test
# ------------------------------------------------------------------------------
@cocotb.test()
async def test_alu_comprehensive(dut):
    """Verify ALU operations across boundary conditions and randomized 32-bit vectors."""
    dut._log.info("Starting comprehensive Cocotb test for RV32I ALU...")

    # Define critical corner cases (boundary conditions for signed & unsigned 32-bit ints)
    corner_cases = [
        # (A, B, Description)
        (0x00000000, 0x00000000, "Zeroes"),
        (0x00000001, 0x00000001, "Small positive ones"),
        (0x7FFFFFFF, 0x00000001, "Max positive + 1 (Signed Overflow)"),
        (0x7FFFFFFF, 0x7FFFFFFF, "Max positive operands"),
        (0x80000000, 0x00000001, "Min negative (0x80000000) - 1"),
        (0x80000000, 0x80000000, "Min negative equal operands"),
        (0xFFFFFFFF, 0x00000001, "0xFFFFFFFF (-1) + 1 (Unsigned Overflow)"),
        (0xFFFFFFFF, 0xFFFFFFFF, "All ones (-1 and -1)"),
        (0x12345678, 0x12345678, "Arbitrary equal values (SUB Zero flag test)"),
        (0xF0F0F0F0, 0x0F0F0F0F, "Complement bit patterns"),
        (0xAAAAAAAA, 0x55555555, "Alternating bit patterns"),
        # Shift amount edge cases: B[4:0] = 0, 1, 31, and B with high bits set
        (0x80000001, 0x00000000, "Shift by 0"),
        (0x80000001, 0x00000001, "Shift by 1"),
        (0x80000001, 0x0000001F, "Shift by 31 (max 5-bit shift)"),
        (0x80000001, 0x00000020, "Shift by 32 (B[4:0] = 0, tests shift amount masking)"),
        (0x80000001, 0xFFFFFFE5, "Shift with large B (B[4:0] = 5)"),
        # Signed vs Unsigned comparisons
        (0xFFFFFFFB, 0x00000003, "-5 vs 3 (SLT: 1, SLTU: 0)"),
        (0x00000003, 0xFFFFFFFB, "3 vs -5 (SLT: 0, SLTU: 1)"),
    ]

    total_checks = 0

    # 1. Run Corner Cases
    dut._log.info(f"Running {len(corner_cases)} corner-case vector pairs...")
    for a, b, desc in corner_cases:
        for op in ALUControl:
            dut.A.value = a
            dut.B.value = b
            dut.ALUControl.value = int(op)

            await Timer(1, units="ns")

            actual_res = int(dut.Result.value)
            actual_zero = int(dut.Zero.value)
            exp_res, exp_zero = compute_expected_alu(a, b, op)

            assert actual_res == exp_res, (
                f"[{desc}] Operation {ALU_OP_NAMES[op]} failed! "
                f"A=0x{a:08X}, B=0x{b:08X}: Expected Result=0x{exp_res:08X}, Got=0x{actual_res:08X}"
            )
            assert actual_zero == exp_zero, (
                f"[{desc}] Operation {ALU_OP_NAMES[op]} failed Zero flag! "
                f"A=0x{a:08X}, B=0x{b:08X}: Expected Zero={exp_zero}, Got={actual_zero}"
            )
            total_checks += 1

    # 2. Run Randomized Vectors
    random.seed(42)  # Deterministic seed for reproducible verification
    num_random_tests = 100
    dut._log.info(f"Running {num_random_tests} randomized 32-bit vector pairs...")

    for i in range(num_random_tests):
        # Generate random 32-bit unsigned integers
        a = random.randint(0, 0xFFFFFFFF)
        b = random.randint(0, 0xFFFFFFFF)

        for op in ALUControl:
            dut.A.value = a
            dut.B.value = b
            dut.ALUControl.value = int(op)

            await Timer(1, units="ns")

            actual_res = int(dut.Result.value)
            actual_zero = int(dut.Zero.value)
            exp_res, exp_zero = compute_expected_alu(a, b, op)

            assert actual_res == exp_res, (
                f"[Random Test #{i}] Operation {ALU_OP_NAMES[op]} failed! "
                f"A=0x{a:08X}, B=0x{b:08X}: Expected Result=0x{exp_res:08X}, Got=0x{actual_res:08X}"
            )
            assert actual_zero == exp_zero, (
                f"[Random Test #{i}] Operation {ALU_OP_NAMES[op]} failed Zero flag! "
                f"A=0x{a:08X}, B=0x{b:08X}: Expected Zero={exp_zero}, Got={actual_zero}"
            )
            total_checks += 1

    # 3. Test Default / Undefined Control Code Behavior
    dut._log.info("Testing default case for undefined ALUControl codes (10 to 15)...")
    for undefined_op in range(10, 16):
        dut.A.value = 0x12345678
        dut.B.value = 0x87654321
        dut.ALUControl.value = undefined_op

        await Timer(1, units="ns")

        actual_res = int(dut.Result.value)
        actual_zero = int(dut.Zero.value)

        assert actual_res == 0, (
            f"Default case failed for ALUControl=4'b{undefined_op:04b}! "
            f"Expected Result=0x00000000, Got=0x{actual_res:08X}"
        )
        assert actual_zero == 1, (
            f"Default case Zero flag failed for ALUControl=4'b{undefined_op:04b}! "
            f"Expected Zero=1, Got={actual_zero}"
        )
        total_checks += 1

    dut._log.info(f"ALU Verification SUCCESS! Completed {total_checks} assertions with 0 errors.")
