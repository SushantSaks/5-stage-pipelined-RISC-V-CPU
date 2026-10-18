`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: hazard_unit
// Description: Pipeline Hazard Unit providing:
//              - Data forwarding (EX-to-EX and MEM-to-EX forwarding)
//              - Load-Use hazard detection and stalling
//              - Control hazard (branch/jump) pipeline flushing
//////////////////////////////////////////////////////////////////////////////////

module hazard_unit (
    input  wire [4:0] Rs1D,
    input  wire [4:0] Rs2D,
    input  wire [4:0] Rs1E,
    input  wire [4:0] Rs2E,
    input  wire [4:0] RdE,
    input  wire [4:0] RdM,
    input  wire [4:0] RdW,
    input  wire       RegWriteM,
    input  wire       RegWriteW,
    input  wire [1:0] ResultSrcE, // bit 0 high indicates a Load instruction
    input  wire       PCSrcE,     // high if branch or jump is taken in EX
    output reg  [1:0] ForwardAE,
    output reg  [1:0] ForwardBE,
    output wire       StallF,
    output wire       StallD,
    output wire       FlushD,
    output wire       FlushE
);

    // =========================================================================
    // 1. Data Forwarding Logic (EX Stage Operands)
    // =========================================================================
    // Forwarding to Operand A (Rs1E)
    // Priority: MEM stage (more recent) > WB stage (older)
    always @(*) begin
        if ((Rs1E == RdM) && RegWriteM && (Rs1E != 5'd0)) begin
            ForwardAE = 2'b10; // Forward from MEM stage (ALUResultM)
        end else if ((Rs1E == RdW) && RegWriteW && (Rs1E != 5'd0)) begin
            ForwardAE = 2'b01; // Forward from WB stage (ResultW)
        end else begin
            ForwardAE = 2'b00; // No forwarding (use RD1E from ID/EX register)
        end
    end

    // Forwarding to Operand B (Rs2E)
    always @(*) begin
        if ((Rs2E == RdM) && RegWriteM && (Rs2E != 5'd0)) begin
            ForwardBE = 2'b10; // Forward from MEM stage (ALUResultM)
        end else if ((Rs2E == RdW) && RegWriteW && (Rs2E != 5'd0)) begin
            ForwardBE = 2'b01; // Forward from WB stage (ResultW)
        end else begin
            ForwardBE = 2'b00; // No forwarding (use RD2E from ID/EX register)
        end
    end

    // =========================================================================
    // 2. Load-Use Hazard Detection & Stall Logic
    // =========================================================================
    // When a Load instruction is in EX (ResultSrcE[0] == 1) and its destination RdE
    // matches either source register of the instruction currently in ID (Rs1D/Rs2D),
    // stall the pipeline for 1 clock cycle to let the load read from memory.
    wire lwStall = ResultSrcE[0] && ((Rs1D == RdE) || (Rs2D == RdE)) && (RdE != 5'd0);

    // =========================================================================
    // 3. Pipeline Stall and Flush Generation
    // =========================================================================
    assign StallF = lwStall;
    assign StallD = lwStall;
    assign FlushD = PCSrcE;
    assign FlushE = lwStall | PCSrcE;

endmodule
