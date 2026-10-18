`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I 5-Stage Pipelined Processor / Single-Cycle Datapath
// Module Name: control_unit
// Description: Main Decoder and ALU Decoder for RV32I architecture.
//              Generates datapath control signals and next-PC selection.
//////////////////////////////////////////////////////////////////////////////////

module control_unit (
    input  wire [6:0] op,
    input  wire [2:0] funct3,
    input  wire       funct7b5,
    input  wire       Zero,
    output reg        RegWrite,
    output reg        MemWrite,
    output reg        ALUSrc,
    output reg        Branch,
    output reg        Jump,
    output reg  [1:0] ResultSrc,
    output reg  [2:0] ImmSrc,
    output reg  [3:0] ALUControl,
    output wire       PCSrc
);

    reg [1:0] ALUOp;

    // =========================================================================
    // 1. Main Decoder
    // =========================================================================
    always @(*) begin
        case (op)
            // R-type instructions (add, sub, and, or, xor, sll, srl, sra, slt, sltu)
            7'b0110011: begin
                RegWrite  = 1'b1;
                ImmSrc    = 3'b000;
                ALUSrc    = 1'b0;
                MemWrite  = 1'b0;
                ResultSrc = 2'b00;
                Branch    = 1'b0;
                ALUOp     = 2'b10;
                Jump      = 1'b0;
            end

            // I-type ALU instructions (addi, andi, ori, xori, slli, srli, srai, slti, sltiu)
            7'b0010011: begin
                RegWrite  = 1'b1;
                ImmSrc    = 3'b000;
                ALUSrc    = 1'b1;
                MemWrite  = 1'b0;
                ResultSrc = 2'b00;
                Branch    = 1'b0;
                ALUOp     = 2'b10;
                Jump      = 1'b0;
            end

            // I-type Load instructions (lw)
            7'b0000011: begin
                RegWrite  = 1'b1;
                ImmSrc    = 3'b000;
                ALUSrc    = 1'b1;
                MemWrite  = 1'b0;
                ResultSrc = 2'b01;
                Branch    = 1'b0;
                ALUOp     = 2'b00;
                Jump      = 1'b0;
            end

            // S-type Store instructions (sw)
            7'b0100011: begin
                RegWrite  = 1'b0;
                ImmSrc    = 3'b001;
                ALUSrc    = 1'b1;
                MemWrite  = 1'b1;
                ResultSrc = 2'b00;
                Branch    = 1'b0;
                ALUOp     = 2'b00;
                Jump      = 1'b0;
            end

            // B-type Branch instructions (beq, bne, blt, bge)
            7'b1100011: begin
                RegWrite  = 1'b0;
                ImmSrc    = 3'b010;
                ALUSrc    = 1'b0;
                MemWrite  = 1'b0;
                ResultSrc = 2'b00;
                Branch    = 1'b1;
                ALUOp     = 2'b01;
                Jump      = 1'b0;
            end

            // J-type Jump instructions (jal)
            7'b1101111: begin
                RegWrite  = 1'b1;
                ImmSrc    = 3'b011;
                ALUSrc    = 1'b0;
                MemWrite  = 1'b0;
                ResultSrc = 2'b10;
                Branch    = 1'b0;
                ALUOp     = 2'b00;
                Jump      = 1'b1;
            end

            // U-type instructions (lui)
            7'b0110111: begin
                RegWrite  = 1'b1;
                ImmSrc    = 3'b100;
                ALUSrc    = 1'b1;
                MemWrite  = 1'b0;
                ResultSrc = 2'b00;
                Branch    = 1'b0;
                ALUOp     = 2'b00;
                Jump      = 1'b0;
            end

            // Default safe state (NOP behavior)
            default: begin
                RegWrite  = 1'b0;
                ImmSrc    = 3'b000;
                ALUSrc    = 1'b0;
                MemWrite  = 1'b0;
                ResultSrc = 2'b00;
                Branch    = 1'b0;
                ALUOp     = 2'b00;
                Jump      = 1'b0;
            end
        endcase
    end

    // =========================================================================
    // 2. ALU Decoder
    // =========================================================================
    // 4-bit ALUControl encodings matching rtl/alu.v:
    // 0000: ADD, 0001: SUB, 0010: AND, 0011: OR, 0100: XOR
    // 0101: SLT, 0110: SLTU, 0111: SLL, 1000: SRL, 1001: SRA
    always @(*) begin
        case (ALUOp)
            2'b00: ALUControl = 4'b0000; // ADD (for Load, Store, LUI)
            2'b01: ALUControl = 4'b0001; // SUB (for Branch equality test)
            2'b10: begin                 // R-type and I-type ALU operations
                case (funct3)
                    3'b000: begin
                        // For R-type (op[5]==1), funct7b5 differentiates ADD and SUB.
                        // For I-type (op[5]==0, addi), always perform ADD.
                        if (op[5] & funct7b5)
                            ALUControl = 4'b0001; // SUB
                        else
                            ALUControl = 4'b0000; // ADD
                    end
                    3'b001: ALUControl = 4'b0111; // SLL
                    3'b010: ALUControl = 4'b0101; // SLT
                    3'b011: ALUControl = 4'b0110; // SLTU
                    3'b100: ALUControl = 4'b0100; // XOR
                    3'b101: begin
                        if (funct7b5)
                            ALUControl = 4'b1001; // SRA
                        else
                            ALUControl = 4'b1000; // SRL
                    end
                    3'b110: ALUControl = 4'b0011; // OR
                    3'b111: ALUControl = 4'b0010; // AND
                    default: ALUControl = 4'b0000;
                endcase
            end
            default: ALUControl = 4'b0000;
        endcase
    end

    // =========================================================================
    // 3. PCSrc Logic Block
    // =========================================================================
    assign PCSrc = (Branch & Zero) | Jump;

endmodule
