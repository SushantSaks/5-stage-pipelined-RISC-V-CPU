`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I Single-Cycle Processor
// Module Name: riscv_single_cycle
// Description: Top-level single-cycle integration module connecting:
//              - Program Counter (PC)
//              - InstructionMemory (ROM)
//              - ControlUnit (Main & ALU decoders + PCSrc)
//              - RegisterFile (32x32-bit registers with x0=0)
//              - Extender (Sign-extension unit)
//              - ALU (32-bit RV32I execution engine)
//              - DataMemory (RAM)
//////////////////////////////////////////////////////////////////////////////////

module riscv_single_cycle (
    input wire clk,
    input wire reset
);

    // =========================================================================
    // Internal Wires & Buses
    // =========================================================================
    // Program Counter signals
    reg  [31:0] PC;
    wire [31:0] PCNext;
    wire [31:0] PCPlus4;
    wire [31:0] PCTarget;

    // Instruction bus
    wire [31:0] Instr;

    // Control signals
    wire       RegWrite;
    wire       MemWrite;
    wire       ALUSrc;
    wire       Branch;
    wire       Jump;
    wire [1:0] ResultSrc;
    wire [2:0] ImmSrc;
    wire [3:0] ALUControl;
    wire       PCSrc;

    // Register File buses
    wire [31:0] SrcA;
    wire [31:0] WriteData;

    // Extender output
    wire [31:0] ImmExt;

    // ALU buses
    wire [31:0] SrcB;
    wire [31:0] ALUResult;
    wire        Zero;

    // Memory output bus
    wire [31:0] ReadData;

    // Writeback result bus
    wire [31:0] Result;

    // =========================================================================
    // 1. Program Counter & Next PC Logic
    // =========================================================================
    assign PCPlus4  = PC + 32'd4;
    assign PCTarget = PC + ImmExt;
    assign PCNext   = PCSrc ? PCTarget : PCPlus4;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            PC <= 32'd0;
        end else begin
            PC <= PCNext;
        end
    end

    // =========================================================================
    // 2. Instruction Memory (ROM)
    // =========================================================================
    InstructionMemory #(.MEM_DEPTH(1024)) u_imem (
        .Address(PC),
        .Instruction(Instr)
    );

    // =========================================================================
    // 3. Control Unit
    // =========================================================================
    control_unit u_cunit (
        .op(Instr[6:0]),
        .funct3(Instr[14:12]),
        .funct7b5(Instr[30]),
        .Zero(Zero),
        .RegWrite(RegWrite),
        .MemWrite(MemWrite),
        .ALUSrc(ALUSrc),
        .Branch(Branch),
        .Jump(Jump),
        .ResultSrc(ResultSrc),
        .ImmSrc(ImmSrc),
        .ALUControl(ALUControl),
        .PCSrc(PCSrc)
    );

    // =========================================================================
    // 4. Register File
    // =========================================================================
    regfile u_regfile (
        .clk(clk),
        .we(RegWrite),
        .rs1(Instr[19:15]),
        .rs2(Instr[24:20]),
        .rd(Instr[11:7]),
        .wd(Result),
        .rd1(SrcA),
        .rd2(WriteData)
    );

    // =========================================================================
    // 5. Immediate Extender
    // =========================================================================
    extend u_extend (
        .Instr(Instr[31:7]),
        .ImmSrc(ImmSrc),
        .ImmExt(ImmExt)
    );

    // =========================================================================
    // 6. Arithmetic Logic Unit (ALU) & Operand Mux
    // =========================================================================
    assign SrcB = ALUSrc ? ImmExt : WriteData;

    alu u_alu (
        .A(SrcA),
        .B(SrcB),
        .ALUControl(ALUControl),
        .Result(ALUResult),
        .Zero(Zero)
    );

    // =========================================================================
    // 7. Data Memory (RAM)
    // =========================================================================
    DataMemory #(.MEM_DEPTH(1024)) u_dmem (
        .clk(clk),
        .we(MemWrite),
        .Address(ALUResult),
        .WriteData(WriteData),
        .ReadData(ReadData)
    );

    // =========================================================================
    // 8. Result Writeback Multiplexer
    // =========================================================================
    assign Result = (ResultSrc == 2'b00) ? ALUResult :
                    (ResultSrc == 2'b01) ? ReadData  :
                    (ResultSrc == 2'b10) ? PCPlus4   : 32'd0;

endmodule
