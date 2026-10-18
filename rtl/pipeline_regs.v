`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: pipeline_regs (IF_ID_reg, ID_EX_reg, EX_MEM_reg, MEM_WB_reg)
// Description: Pipeline segmentation registers separating the 5 stages:
//              IF -> ID -> EX -> MEM -> WB.
//              - Triggered on posedge clk.
//              - Synchronous reset and clear (clr) to flush pipeline bubbles.
//              - Clock enable (en) to stall/freeze stage state.
//////////////////////////////////////////////////////////////////////////////////

// ==============================================================================
// 1. IF_ID_reg: Fetch to Decode Pipeline Register
// ==============================================================================
module IF_ID_reg (
    input  wire        clk,
    input  wire        reset,
    input  wire        clr,
    input  wire        en,
    input  wire [31:0] PCF,
    input  wire [31:0] InstrF,
    input  wire [31:0] PCPlus4F,
    output reg  [31:0] PCD,
    output reg  [31:0] InstrD,
    output reg  [31:0] PCPlus4D
);

    always @(posedge clk) begin
        if (reset || clr) begin
            PCD      <= 32'd0;
            InstrD   <= 32'h00000013; // NOP (addi x0, x0, 0)
            PCPlus4D <= 32'd0;
        end else if (en) begin
            PCD      <= PCF;
            InstrD   <= InstrF;
            PCPlus4D <= PCPlus4F;
        end
    end

endmodule

// ==============================================================================
// 2. ID_EX_reg: Decode to Execute Pipeline Register
// ==============================================================================
module ID_EX_reg (
    input  wire        clk,
    input  wire        reset,
    input  wire        clr,
    input  wire        en,
    // Control signals in
    input  wire        RegWriteD,
    input  wire [1:0]  ResultSrcD,
    input  wire        MemWriteD,
    input  wire        JumpD,
    input  wire        BranchD,
    input  wire [3:0]  ALUControlD,
    input  wire        ALUSrcD,
    // Data signals in
    input  wire [31:0] RD1D,
    input  wire [31:0] RD2D,
    input  wire [31:0] PCD,
    input  wire [31:0] ImmExtD,
    input  wire [31:0] PCPlus4D,
    // Register address signals in
    input  wire [4:0]  Rs1D,
    input  wire [4:0]  Rs2D,
    input  wire [4:0]  RdD,
    // Control signals out
    output reg         RegWriteE,
    output reg  [1:0]  ResultSrcE,
    output reg         MemWriteE,
    output reg         JumpE,
    output reg         BranchE,
    output reg  [3:0]  ALUControlE,
    output reg         ALUSrcE,
    // Data signals out
    output reg  [31:0] RD1E,
    output reg  [31:0] RD2E,
    output reg  [31:0] PCE,
    output reg  [31:0] ImmExtE,
    output reg  [31:0] PCPlus4E,
    // Register address signals out
    output reg  [4:0]  Rs1E,
    output reg  [4:0]  Rs2E,
    output reg  [4:0]  RdE
);

    always @(posedge clk) begin
        if (reset || clr) begin
            RegWriteE   <= 1'b0;
            ResultSrcE  <= 2'b00;
            MemWriteE   <= 1'b0;
            JumpE       <= 1'b0;
            BranchE     <= 1'b0;
            ALUControlE <= 4'b0000;
            ALUSrcE     <= 1'b0;
            RD1E        <= 32'd0;
            RD2E        <= 32'd0;
            PCE         <= 32'd0;
            ImmExtE     <= 32'd0;
            PCPlus4E    <= 32'd0;
            Rs1E        <= 5'd0;
            Rs2E        <= 5'd0;
            RdE         <= 5'd0;
        end else if (en) begin
            RegWriteE   <= RegWriteD;
            ResultSrcE  <= ResultSrcD;
            MemWriteE   <= MemWriteD;
            JumpE       <= JumpD;
            BranchE     <= BranchD;
            ALUControlE <= ALUControlD;
            ALUSrcE     <= ALUSrcD;
            RD1E        <= RD1D;
            RD2E        <= RD2D;
            PCE         <= PCD;
            ImmExtE     <= ImmExtD;
            PCPlus4E    <= PCPlus4D;
            Rs1E        <= Rs1D;
            Rs2E        <= Rs2D;
            RdE         <= RdD;
        end
    end

endmodule

// ==============================================================================
// 3. EX_MEM_reg: Execute to Memory Pipeline Register
// ==============================================================================
module EX_MEM_reg (
    input  wire        clk,
    input  wire        reset,
    input  wire        clr,
    input  wire        en,
    // Control signals in
    input  wire        RegWriteE,
    input  wire [1:0]  ResultSrcE,
    input  wire        MemWriteE,
    // Data signals in
    input  wire [31:0] ALUResultE,
    input  wire [31:0] WriteDataE,
    input  wire [31:0] PCPlus4E,
    // Register address in
    input  wire [4:0]  RdE,
    // Control signals out
    output reg         RegWriteM,
    output reg  [1:0]  ResultSrcM,
    output reg         MemWriteM,
    // Data signals out
    output reg  [31:0] ALUResultM,
    output reg  [31:0] WriteDataM,
    output reg  [31:0] PCPlus4M,
    // Register address out
    output reg  [4:0]  RdM
);

    always @(posedge clk) begin
        if (reset || clr) begin
            RegWriteM  <= 1'b0;
            ResultSrcM <= 2'b00;
            MemWriteM  <= 1'b0;
            ALUResultM <= 32'd0;
            WriteDataM <= 32'd0;
            PCPlus4M   <= 32'd0;
            RdM        <= 5'd0;
        end else if (en) begin
            RegWriteM  <= RegWriteE;
            ResultSrcM <= ResultSrcE;
            MemWriteM  <= MemWriteE;
            ALUResultM <= ALUResultE;
            WriteDataM <= WriteDataE;
            PCPlus4M   <= PCPlus4E;
            RdM        <= RdE;
        end
    end

endmodule

// ==============================================================================
// 4. MEM_WB_reg: Memory to Writeback Pipeline Register
// ==============================================================================
module MEM_WB_reg (
    input  wire        clk,
    input  wire        reset,
    input  wire        clr,
    input  wire        en,
    // Control signals in
    input  wire        RegWriteM,
    input  wire [1:0]  ResultSrcM,
    // Data signals in
    input  wire [31:0] ALUResultM,
    input  wire [31:0] ReadDataM,
    input  wire [31:0] PCPlus4M,
    // Register address in
    input  wire [4:0]  RdM,
    // Control signals out
    output reg         RegWriteW,
    output reg  [1:0]  ResultSrcW,
    // Data signals out
    output reg  [31:0] ALUResultW,
    output reg  [31:0] ReadDataW,
    output reg  [31:0] PCPlus4W,
    // Register address out
    output reg  [4:0]  RdW
);

    always @(posedge clk) begin
        if (reset || clr) begin
            RegWriteW  <= 1'b0;
            ResultSrcW <= 2'b00;
            ALUResultW <= 32'd0;
            ReadDataW  <= 32'd0;
            PCPlus4W   <= 32'd0;
            RdW        <= 5'd0;
        end else if (en) begin
            RegWriteW  <= RegWriteM;
            ResultSrcW <= ResultSrcM;
            ALUResultW <= ALUResultM;
            ReadDataW  <= ReadDataM;
            PCPlus4W   <= PCPlus4M;
            RdW        <= RdM;
        end
    end

endmodule
