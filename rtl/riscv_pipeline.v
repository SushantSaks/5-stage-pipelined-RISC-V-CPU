`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: riscv_pipeline
// Description: Top-level 5-stage pipelined RV32I processor module:
//              - Stage 1: Instruction Fetch (IF)
//              - Stage 2: Instruction Decode & Register Fetch (ID)
//              - Stage 3: Execute / Address Calculation (EX)
//              - Stage 4: Memory Access (MEM)
//              - Stage 5: Writeback (WB)
//              Structural pipeline segmentation without hazard handling.
//////////////////////////////////////////////////////////////////////////////////

module riscv_pipeline (
    input wire clk,
    input wire reset
);

    // =========================================================================
    // Stage 1: Instruction Fetch (IF) Signals
    // =========================================================================
    reg  [31:0] PCF;
    wire [31:0] PCNextF;
    wire [31:0] PCPlus4F;
    wire [31:0] InstrF;

    // =========================================================================
    // Stage 2: Instruction Decode (ID) Signals
    // =========================================================================
    wire [31:0] PCD;
    wire [31:0] InstrD;
    wire [31:0] PCPlus4D;

    wire [6:0]  opD       = InstrD[6:0];
    wire [2:0]  funct3D   = InstrD[14:12];
    wire        funct7b5D = InstrD[30];
    wire [4:0]  Rs1D      = InstrD[19:15];
    wire [4:0]  Rs2D      = InstrD[24:20];
    wire [4:0]  RdD       = InstrD[11:7];

    wire        RegWriteD;
    wire [1:0]  ResultSrcD;
    wire        MemWriteD;
    wire        JumpD;
    wire        BranchD;
    wire [3:0]  ALUControlD;
    wire        ALUSrcD;
    wire [2:0]  ImmSrcD;
    wire        PCSrcD_unused;

    wire [31:0] RD1D;
    wire [31:0] RD2D;
    wire [31:0] ImmExtD;

    // =========================================================================
    // Stage 3: Execute (EX) Signals
    // =========================================================================
    wire        RegWriteE;
    wire [1:0]  ResultSrcE;
    wire        MemWriteE;
    wire        JumpE;
    wire        BranchE;
    wire [3:0]  ALUControlE;
    wire        ALUSrcE;

    wire [31:0] RD1E;
    wire [31:0] RD2E;
    wire [31:0] PCE;
    wire [31:0] ImmExtE;
    wire [31:0] PCPlus4E;
    wire [4:0]  Rs1E;
    wire [4:0]  Rs2E;
    wire [4:0]  RdE;

    wire [31:0] SrcAE;
    wire [31:0] SrcBE;
    wire [31:0] WriteDataE;
    wire [31:0] ALUResultE;
    wire        ZeroE;
    wire [31:0] PCTargetE;
    wire        PCSrcE;

    // =========================================================================
    // Stage 4: Memory Access (MEM) Signals
    // =========================================================================
    wire        RegWriteM;
    wire [1:0]  ResultSrcM;
    wire        MemWriteM;

    wire [31:0] ALUResultM;
    wire [31:0] WriteDataM;
    wire [31:0] PCPlus4M;
    wire [4:0]  RdM;
    wire [31:0] ReadDataM;

    // =========================================================================
    // Stage 5: Writeback (WB) Signals
    // =========================================================================
    wire        RegWriteW;
    wire [1:0]  ResultSrcW;

    wire [31:0] ALUResultW;
    wire [31:0] ReadDataW;
    wire [31:0] PCPlus4W;
    wire [4:0]  RdW;
    wire [31:0] ResultW;

    // =========================================================================
    // 1. FETCH (IF) STAGE
    // =========================================================================
    assign PCPlus4F = PCF + 32'd4;
    assign PCNextF  = PCSrcE ? PCTargetE : PCPlus4F;

    always @(posedge clk or posedge reset) begin
        if (reset) begin
            PCF <= 32'd0;
        end else begin
            PCF <= PCNextF;
        end
    end

    InstructionMemory #(.MEM_DEPTH(1024)) u_imem (
        .Address(PCF),
        .Instruction(InstrF)
    );

    // Pipeline Register: IF -> ID
    IF_ID_reg u_if_id_reg (
        .clk(clk),
        .reset(reset),
        .clr(1'b0),
        .en(1'b1),
        .PCF(PCF),
        .InstrF(InstrF),
        .PCPlus4F(PCPlus4F),
        .PCD(PCD),
        .InstrD(InstrD),
        .PCPlus4D(PCPlus4D)
    );

    // =========================================================================
    // 2. DECODE (ID) STAGE
    // =========================================================================
    control_unit u_cunit (
        .op(opD),
        .funct3(funct3D),
        .funct7b5(funct7b5D),
        .Zero(1'b0), // Evaluated in EX stage
        .RegWrite(RegWriteD),
        .MemWrite(MemWriteD),
        .ALUSrc(ALUSrcD),
        .Branch(BranchD),
        .Jump(JumpD),
        .ResultSrc(ResultSrcD),
        .ImmSrc(ImmSrcD),
        .ALUControl(ALUControlD),
        .PCSrc(PCSrcD_unused)
    );

    regfile u_regfile (
        .clk(clk),
        .we(RegWriteW),
        .rs1(Rs1D),
        .rs2(Rs2D),
        .rd(RdW),
        .wd(ResultW),
        .rd1(RD1D),
        .rd2(RD2D)
    );

    extend u_extend (
        .Instr(InstrD[31:7]),
        .ImmSrc(ImmSrcD),
        .ImmExt(ImmExtD)
    );

    // Pipeline Register: ID -> EX
    ID_EX_reg u_id_ex_reg (
        .clk(clk),
        .reset(reset),
        .clr(1'b0),
        .en(1'b1),
        .RegWriteD(RegWriteD),
        .ResultSrcD(ResultSrcD),
        .MemWriteD(MemWriteD),
        .JumpD(JumpD),
        .BranchD(BranchD),
        .ALUControlD(ALUControlD),
        .ALUSrcD(ALUSrcD),
        .RD1D(RD1D),
        .RD2D(RD2D),
        .PCD(PCD),
        .ImmExtD(ImmExtD),
        .PCPlus4D(PCPlus4D),
        .Rs1D(Rs1D),
        .Rs2D(Rs2D),
        .RdD(RdD),
        .RegWriteE(RegWriteE),
        .ResultSrcE(ResultSrcE),
        .MemWriteE(MemWriteE),
        .JumpE(JumpE),
        .BranchE(BranchE),
        .ALUControlE(ALUControlE),
        .ALUSrcE(ALUSrcE),
        .RD1E(RD1E),
        .RD2E(RD2E),
        .PCE(PCE),
        .ImmExtE(ImmExtE),
        .PCPlus4E(PCPlus4E),
        .Rs1E(Rs1E),
        .Rs2E(Rs2E),
        .RdE(RdE)
    );

    // =========================================================================
    // 3. EXECUTE (EX) STAGE
    // =========================================================================
    assign SrcAE      = RD1E;
    assign WriteDataE = RD2E;
    assign SrcBE      = ALUSrcE ? ImmExtE : WriteDataE;

    alu u_alu (
        .A(SrcAE),
        .B(SrcBE),
        .ALUControl(ALUControlE),
        .Result(ALUResultE),
        .Zero(ZeroE)
    );

    assign PCTargetE = PCE + ImmExtE;
    assign PCSrcE    = (BranchE & ZeroE) | JumpE;

    // Pipeline Register: EX -> MEM
    EX_MEM_reg u_ex_mem_reg (
        .clk(clk),
        .reset(reset),
        .clr(1'b0),
        .en(1'b1),
        .RegWriteE(RegWriteE),
        .ResultSrcE(ResultSrcE),
        .MemWriteE(MemWriteE),
        .ALUResultE(ALUResultE),
        .WriteDataE(WriteDataE),
        .PCPlus4E(PCPlus4E),
        .RdE(RdE),
        .RegWriteM(RegWriteM),
        .ResultSrcM(ResultSrcM),
        .MemWriteM(MemWriteM),
        .ALUResultM(ALUResultM),
        .WriteDataM(WriteDataM),
        .PCPlus4M(PCPlus4M),
        .RdM(RdM)
    );

    // =========================================================================
    // 4. MEMORY (MEM) STAGE
    // =========================================================================
    DataMemory #(.MEM_DEPTH(1024)) u_dmem (
        .clk(clk),
        .we(MemWriteM),
        .Address(ALUResultM),
        .WriteData(WriteDataM),
        .ReadData(ReadDataM)
    );

    // Pipeline Register: MEM -> WB
    MEM_WB_reg u_mem_wb_reg (
        .clk(clk),
        .reset(reset),
        .clr(1'b0),
        .en(1'b1),
        .RegWriteM(RegWriteM),
        .ResultSrcM(ResultSrcM),
        .ALUResultM(ALUResultM),
        .ReadDataM(ReadDataM),
        .PCPlus4M(PCPlus4M),
        .RdM(RdM),
        .RegWriteW(RegWriteW),
        .ResultSrcW(ResultSrcW),
        .ALUResultW(ALUResultW),
        .ReadDataW(ReadDataW),
        .PCPlus4W(PCPlus4W),
        .RdW(RdW)
    );

    // =========================================================================
    // 5. WRITEBACK (WB) STAGE
    // =========================================================================
    assign ResultW = (ResultSrcW == 2'b00) ? ALUResultW :
                     (ResultSrcW == 2'b01) ? ReadDataW  :
                     (ResultSrcW == 2'b10) ? PCPlus4W   : 32'd0;

endmodule
