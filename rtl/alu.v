`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: alu
// Project Name: RISC-V Pipeline Verilog
// Target Devices: Xilinx Vivado (Synthesizable)
// Tool Versions: Vivado 2026.1+
// Description: Purely combinational 32-bit Arithmetic Logic Unit (ALU)
//              supporting standard RV32I arithmetic, logic, and comparison operations.
//
// Dependencies: None
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// - All shifts strictly utilize B[4:0] per RV32I specification.
// - SRA utilizes $signed for arithmetic right shift with sign extension.
// - SLT performs signed comparison; SLTU performs unsigned comparison.
// - Zero flag is high when Result is 32'b0.
// - Fully combinational; latches are strictly prevented via complete case coverage.
//////////////////////////////////////////////////////////////////////////////////

module alu (
    input  wire [31:0] A,
    input  wire [31:0] B,
    input  wire [3:0]  ALUControl,
    output reg  [31:0] Result,
    output wire        Zero
);

    // ALU Operation Encodings (4-bit control)
    localparam [3:0] ALU_ADD  = 4'b0000; // Addition: A + B
    localparam [3:0] ALU_SUB  = 4'b0001; // Subtraction: A - B
    localparam [3:0] ALU_AND  = 4'b0010; // Bitwise AND: A & B
    localparam [3:0] ALU_OR   = 4'b0011; // Bitwise OR: A | B
    localparam [3:0] ALU_XOR  = 4'b0100; // Bitwise XOR: A ^ B
    localparam [3:0] ALU_SLT  = 4'b0101; // Set Less Than (Signed)
    localparam [3:0] ALU_SLTU = 4'b0110; // Set Less Than (Unsigned)
    localparam [3:0] ALU_SLL  = 4'b0111; // Shift Left Logical: A << B[4:0]
    localparam [3:0] ALU_SRL  = 4'b1000; // Shift Right Logical: A >> B[4:0]
    localparam [3:0] ALU_SRA  = 4'b1001; // Shift Right Arithmetic: $signed(A) >>> B[4:0]

    // Combinational evaluation of ALU operations
    always @(*) begin
        case (ALUControl)
            ALU_ADD:  Result = A + B;
            ALU_SUB:  Result = A - B;
            ALU_AND:  Result = A & B;
            ALU_OR:   Result = A | B;
            ALU_XOR:  Result = A ^ B;
            ALU_SLT:  Result = ($signed(A) < $signed(B)) ? 32'd1 : 32'd0;
            ALU_SLTU: Result = (A < B) ? 32'd1 : 32'd0;
            ALU_SLL:  Result = A << B[4:0];
            ALU_SRL:  Result = A >> B[4:0];
            ALU_SRA:  Result = $signed(A) >>> B[4:0];
            default:  Result = 32'd0;
        endcase
    end

    // Zero flag output: high when Result is equal to zero
    assign Zero = (Result == 32'd0);

endmodule
