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
    // 4-bit ALUControl encodings strictly matching rtl/alu.v:
    localparam [3:0] ALU_ADD  = 4'b0000; // Addition: A + B
    localparam [3:0] ALU_SUB  = 4'b0001; // Subtraction: A - B (for Branch equality test)
    localparam [3:0] ALU_AND  = 4'b0010; // Bitwise AND: A & B
    localparam [3:0] ALU_OR   = 4'b0011; // Bitwise OR: A | B
    localparam [3:0] ALU_XOR  = 4'b0100; // Bitwise XOR: A ^ B
    localparam [3:0] ALU_SLT  = 4'b0101; // Set Less Than (Signed)
    localparam [3:0] ALU_SLTU = 4'b0110; // Set Less Than (Unsigned)
    localparam [3:0] ALU_SLL  = 4'b0111; // Shift Left Logical
    localparam [3:0] ALU_SRL  = 4'b1000; // Shift Right Logical
    localparam [3:0] ALU_SRA  = 4'b1001; // Shift Right Arithmetic

    always @(*) begin
        case (ALUOp)
            2'b00: ALUControl = ALU_ADD; // ADD (for Load, Store, LUI)
            2'b01: ALUControl = ALU_SUB; // SUB (for Branch equality test)
            2'b10: begin                 // R-type and I-type ALU operations
                case (funct3)
                    3'b000: begin
                        // For R-type (op[5]==1), funct7b5 differentiates ADD and SUB.
                        // For I-type (op[5]==0, addi), always perform ADD.
                        if (op[5] & funct7b5)
                            ALUControl = ALU_SUB;
                        else
                            ALUControl = ALU_ADD;
                    end
                    3'b001: ALUControl = ALU_SLL;
                    3'b010: ALUControl = ALU_SLT;
                    3'b011: ALUControl = ALU_SLTU;
                    3'b100: ALUControl = ALU_XOR;
                    3'b101: begin
                        if (funct7b5)
                            ALUControl = ALU_SRA;
                        else
                            ALUControl = ALU_SRL;
                    end
                    3'b110: ALUControl = ALU_OR;
                    3'b111: ALUControl = ALU_AND;
                    default: ALUControl = ALU_ADD;
                endcase
            end
            default: ALUControl = ALU_ADD;
        endcase
    end

    // =========================================================================
    // 3. PCSrc Logic Block
    // =========================================================================
    assign PCSrc = (Branch & Zero) | Jump;

endmodule
