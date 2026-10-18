#!/usr/bin/env python3
"""
golden_model.py - RV32I Datapath Golden Architectural Model
===========================================================
This module provides a bit-accurate Python model of the RISC-V RV32I datapath
foundations using NumPy to strictly enforce 32-bit unsigned and signed arithmetic,
overflow wrapping, and register file behavior.

Classes:
    - RegisterFile: 32x32-bit register file with immutable x0.
    - ALU: Purely combinational arithmetic logic unit matching rtl/alu.v.
"""

import numpy as np

# Suppress NumPy runtime overflow warnings since 32-bit wrapping is intended hardware behavior
np.seterr(all='ignore')


class RegisterFile:
    """
    32x32-bit RISC-V Architectural Register File.
    - Dual read ports, single write port.
    - Register x0 is strictly hardwired to 0 (reads return 0, writes are ignored).
    - Enforces 32-bit unsigned integer values via NumPy uint32.
    """

    ABI_NAMES = [
        "zero", "ra",  "sp",  "gp",  "tp",  "t0",  "t1",  "t2",
        "s0",   "s1",  "a0",  "a1",  "a2",  "a3",  "a4",  "a5",
        "a6",   "a7",  "s2",  "s3",  "s4",  "s5",  "s6",  "s7",
        "s8",   "s9",  "s10", "s11", "t3",  "t4",  "t5",  "t6"
    ]

    def __init__(self):
        # 32 registers initialized to 32-bit unsigned zero
        self.regs = np.zeros(32, dtype=np.uint32)

    def read(self, reg_num: int) -> np.uint32:
        """Read data from register reg_num. Register x0 unconditionally returns 0."""
        if not (0 <= reg_num < 32):
            raise IndexError(f"Register index out of range: {reg_num} (must be 0-31)")
        if reg_num == 0:
            return np.uint32(0)
        return self.regs[reg_num]

    def write(self, reg_num: int, value) -> None:
        """Write 32-bit data to register reg_num. Writes to x0 are discarded."""
        if not (0 <= reg_num < 32):
            raise IndexError(f"Register index out of range: {reg_num} (must be 0-31)")
        if reg_num == 0:
            # Register x0 is immutable
            return
        # Mask and enforce 32-bit unsigned integer
        self.regs[reg_num] = np.uint32(int(value) & 0xFFFFFFFF)

    def __getitem__(self, reg_num: int) -> np.uint32:
        return self.read(reg_num)

    def __setitem__(self, reg_num: int, value) -> None:
        self.write(reg_num, value)

    def dump(self) -> str:
        """Return a formatted tabular representation of all 32 registers."""
        lines = []
        lines.append("=" * 78)
        lines.append(f"{'Reg':<6}{'ABI':<8}{'Hex Value':<14}{'Unsigned Dec':<16}{'Signed Dec':<14}")
        lines.append("-" * 78)
        for i in range(32):
            val_u = self.read(i)
            val_s = np.int32(val_u)
            lines.append(f"x{i:<5}{self.ABI_NAMES[i]:<8}0x{val_u:08X}    {val_u:<16}{val_s:<14}")
        lines.append("=" * 78)
        return "\n".join(lines)


class ALU:
    """
    RISC-V 32-bit Arithmetic Logic Unit (ALU) Golden Model.
    Exact 4-bit control code mappings match rtl/alu.v.
    """

    # 4-bit Control Codes matching rtl/alu.v
    ALU_ADD  = 0b0000  # 4'b0000: Addition
    ALU_SUB  = 0b0001  # 4'b0001: Subtraction
    ALU_AND  = 0b0010  # 4'b0010: Bitwise AND
    ALU_OR   = 0b0011  # 4'b0011: Bitwise OR
    ALU_XOR  = 0b0100  # 4'b0100: Bitwise XOR
    ALU_SLT  = 0b0101  # 4'b0101: Set Less Than (Signed)
    ALU_SLTU = 0b0110  # 4'b0110: Set Less Than (Unsigned)
    ALU_SLL  = 0b0111  # 4'b0111: Shift Left Logical
    ALU_SRL  = 0b1000  # 4'b1000: Shift Right Logical
    ALU_SRA  = 0b1001  # 4'b1001: Shift Right Arithmetic

    OP_NAMES = {
        ALU_ADD:  "ADD",
        ALU_SUB:  "SUB",
        ALU_AND:  "AND",
        ALU_OR:   "OR",
        ALU_XOR:  "XOR",
        ALU_SLT:  "SLT",
        ALU_SLTU: "SLTU",
        ALU_SLL:  "SLL",
        ALU_SRL:  "SRL",
        ALU_SRA:  "SRA",
    }

    @classmethod
    def execute(cls, a, b, alu_control: int) -> tuple[np.uint32, int]:
        """
        Execute an ALU operation on 32-bit operands.

        Args:
            a: 32-bit operand A (int or np.uint32)
            b: 32-bit operand B (int or np.uint32)
            alu_control: 4-bit ALU control code

        Returns:
            tuple: (result: np.uint32, zero: int)
        """
        # Strictly enforce 32-bit width and two's complement interpretations
        a_u = np.uint32(int(a) & 0xFFFFFFFF)
        b_u = np.uint32(int(b) & 0xFFFFFFFF)
        a_s = np.int32(a_u)
        b_s = np.int32(b_u)

        # Shift amount is restricted to the lower 5 bits (B[4:0])
        shamt = int(b_u & 0x1F)

        if alu_control == cls.ALU_ADD:
            result = np.uint32(a_u + b_u)
        elif alu_control == cls.ALU_SUB:
            result = np.uint32(a_u - b_u)
        elif alu_control == cls.ALU_AND:
            result = np.uint32(a_u & b_u)
        elif alu_control == cls.ALU_OR:
            result = np.uint32(a_u | b_u)
        elif alu_control == cls.ALU_XOR:
            result = np.uint32(a_u ^ b_u)
        elif alu_control == cls.ALU_SLT:
            result = np.uint32(1) if a_s < b_s else np.uint32(0)
        elif alu_control == cls.ALU_SLTU:
            result = np.uint32(1) if a_u < b_u else np.uint32(0)
        elif alu_control == cls.ALU_SLL:
            result = np.uint32((int(a_u) << shamt) & 0xFFFFFFFF)
        elif alu_control == cls.ALU_SRL:
            result = np.uint32(a_u >> np.uint32(shamt))
        elif alu_control == cls.ALU_SRA:
            result = np.uint32(np.int32(a_s >> shamt))
        else:
            # Default case returns zero
            result = np.uint32(0)

        # Zero flag is asserted (1) when Result is 32'b0
        zero = 1 if result == np.uint32(0) else 0

        return result, zero


def main():
    print("=" * 78)
    print(" RV32I Datapath Phase 1: Golden Model Simulation (NumPy)")
    print("=" * 78)

    rf = RegisterFile()
    alu = ALU()

    # 1. Initialize input registers
    # x1 = 0x7FFFFFFF (maximum positive signed 32-bit int)
    # x2 = 0x00000005
    val_x1 = 0x7FFFFFFF
    val_x2 = 0x00000005
    rf.write(1, val_x1)
    rf.write(2, val_x2)

    print(f"\n[Step 1] Initialized Registers:")
    print(f"  x1 ({rf.ABI_NAMES[1]}): 0x{rf[1]:08X} ({rf[1]} unsigned, {np.int32(rf[1])} signed)")
    print(f"  x2 ({rf.ABI_NAMES[2]}): 0x{rf[2]:08X} ({rf[2]} unsigned, {np.int32(rf[2])} signed)")

    # 2. Perform ADD Operation: x3 = x1 + x2 (demonstrates 32-bit signed overflow wrapping)
    op1_a = rf.read(1)
    op1_b = rf.read(2)
    res_add, zero_add = alu.execute(op1_a, op1_b, ALU.ALU_ADD)
    rf.write(3, res_add)

    print(f"\n[Step 2] ALU ADD Operation: x3 = x1 + x2")
    print(f"  ALUControl : 4'b{ALU.ALU_ADD:04b} ({ALU.OP_NAMES[ALU.ALU_ADD]})")
    print(f"  Operand A  : 0x{op1_a:08X} ({op1_a})")
    print(f"  Operand B  : 0x{op1_b:08X} ({op1_b})")
    print(f"  Result     : 0x{res_add:08X} ({res_add} unsigned, {np.int32(res_add)} signed)")
    print(f"  Zero Flag  : {zero_add}")
    print(f"  Note       : 0x7FFFFFFF + 5 wraps to 0x80000004 ({np.int32(res_add)} signed)")

    # 3. Perform SUB Operation: x4 = x3 - x2 (recovering original x1 value)
    op2_a = rf.read(3)
    op2_b = rf.read(2)
    res_sub, zero_sub = alu.execute(op2_a, op2_b, ALU.ALU_SUB)
    rf.write(4, res_sub)

    print(f"\n[Step 3] ALU SUB Operation: x4 = x3 - x2")
    print(f"  ALUControl : 4'b{ALU.ALU_SUB:04b} ({ALU.OP_NAMES[ALU.ALU_SUB]})")
    print(f"  Operand A  : 0x{op2_a:08X} ({op2_a})")
    print(f"  Operand B  : 0x{op2_b:08X} ({op2_b})")
    print(f"  Result     : 0x{res_sub:08X} ({res_sub})")
    print(f"  Zero Flag  : {zero_sub}")

    # 4. Perform SUB Operation yielding Zero: x5 = x1 - x1
    op3_a = rf.read(1)
    op3_b = rf.read(1)
    res_zero, zero_flag = alu.execute(op3_a, op3_b, ALU.ALU_SUB)
    rf.write(5, res_zero)

    print(f"\n[Step 4] ALU SUB Operation (Zero Flag Test): x5 = x1 - x1")
    print(f"  ALUControl : 4'b{ALU.ALU_SUB:04b} ({ALU.OP_NAMES[ALU.ALU_SUB]})")
    print(f"  Operand A  : 0x{op3_a:08X}")
    print(f"  Operand B  : 0x{op3_b:08X}")
    print(f"  Result     : 0x{res_zero:08X}")
    print(f"  Zero Flag  : {zero_flag} (Correctly Asserted)")

    # 5. Enforce x0 Immutability Test
    print(f"\n[Step 5] Register x0 Hardwired Zero Verification:")
    print(f"  Initial x0 value : 0x{rf.read(0):08X}")
    print(f"  Attempting write : rf.write(0, 0xDEADBEEF)")
    rf.write(0, 0xDEADBEEF)
    print(f"  Resulting x0     : 0x{rf.read(0):08X} (Strictly preserved as 0)")

    # 6. Print full Register File State
    print(f"\n[Step 6] Final Register File State Dump:")
    print(rf.dump())


if __name__ == "__main__":
    main()
