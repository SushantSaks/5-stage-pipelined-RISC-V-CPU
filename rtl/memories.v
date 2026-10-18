`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: InstructionMemory, DataMemory
// Project Name: RISC-V Pipeline Verilog
// Target Devices: Xilinx Vivado (Synthesizable)
// Tool Versions: Vivado 2026.1+
// Description: Memory modules for RV32I processor:
//              1. InstructionMemory: ROM initialized via $readmemh with word-aligned addressing.
//              2. DataMemory: RAM with asynchronous read and synchronous write (posedge clk).
//
// Dependencies: programs/inst_mem.mem (for InstructionMemory initialization)
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// - Word alignment: 32-bit byte address divided by 4 using Address[31:2].
// - Asynchronous reads are implemented via continuous assign to eliminate latches.
// - Synchronous writes are strictly sensitive to posedge clk.
//////////////////////////////////////////////////////////////////////////////////

// ==============================================================================
// Module 1: InstructionMemory (ROM)
// ==============================================================================
module InstructionMemory #(
    parameter MEM_DEPTH = 1024  // Number of 32-bit words (4 KB default)
)(
    input  wire [31:0] Address,
    output wire [31:0] Instruction
);

    // Memory array storing 32-bit instructions
    reg [31:0] memory_array [0:MEM_DEPTH-1];

    integer i;
    initial begin
        // Initialize memory with default NOPs (addi x0, x0, 0 = 32'h00000013)
        for (i = 0; i < MEM_DEPTH; i = i + 1) begin
            memory_array[i] = 32'h00000013;
        end
        // Load machine code from hex file into memory_array
        $readmemh("programs/inst_mem.mem", memory_array);
    end

    // Word-aligned asynchronous read (Address / 4 => Address[31:2])
    // Out-of-bounds accesses safely return NOP
    assign Instruction = (Address[31:2] < MEM_DEPTH) ? memory_array[Address[31:2]] : 32'h00000013;

endmodule

// ==============================================================================
// Module 2: DataMemory (RAM)
// ==============================================================================
module DataMemory #(
    parameter MEM_DEPTH = 1024  // Number of 32-bit words (4 KB default)
)(
    input  wire        clk,
    input  wire        we,
    input  wire [31:0] Address,
    input  wire [31:0] WriteData,
    output wire [31:0] ReadData
);

    // RAM array storing 32-bit data words
    reg [31:0] ram [0:MEM_DEPTH-1];

    integer i;
    initial begin
        // Initialize data memory cells to 0
        for (i = 0; i < MEM_DEPTH; i = i + 1) begin
            ram[i] = 32'd0;
        end
    end

    // Word-aligned asynchronous read (Address / 4 => Address[31:2])
    // Purely combinational logic to prevent memory latches
    assign ReadData = (Address[31:2] < MEM_DEPTH) ? ram[Address[31:2]] : 32'd0;

    // Synchronous write on positive clock edge
    always @(posedge clk) begin
        if (we && (Address[31:2] < MEM_DEPTH)) begin
            ram[Address[31:2]] <= WriteData;
        end
    end

endmodule
