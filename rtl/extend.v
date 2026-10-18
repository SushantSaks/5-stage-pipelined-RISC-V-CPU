`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Design Name: RV32I 5-Stage Pipelined Processor / Single-Cycle Datapath
// Module Name: extend
// Description: Immediate sign-extension unit for RV32I architecture.
//              Supports I-type, S-type, B-type, J-type, and U-type formats.
//////////////////////////////////////////////////////////////////////////////////

module extend (
    input  wire [31:7] Instr,
    input  wire [2:0]  ImmSrc,
    output reg  [31:0] ImmExt
);

    always @(*) begin
        case (ImmSrc)
            // 3'b000: I-type (imm[11:0] at Instr[31:20])
            3'b000: ImmExt = {{20{Instr[31]}}, Instr[31:20]};

            // 3'b001: S-type (imm[11:5] at Instr[31:25], imm[4:0] at Instr[11:7])
            3'b001: ImmExt = {{20{Instr[31]}}, Instr[31:25], Instr[11:7]};

            // 3'b010: B-type (imm[12|10:5|4:1|11])
            3'b010: ImmExt = {{20{Instr[31]}}, Instr[7], Instr[30:25], Instr[11:8], 1'b0};

            // 3'b011: J-type (imm[20|10:1|11|19:12])
            3'b011: ImmExt = {{12{Instr[31]}}, Instr[19:12], Instr[20], Instr[30:21], 1'b0};

            // 3'b100: U-type (imm[31:12] at Instr[31:12])
            3'b100: ImmExt = {Instr[31:12], 12'b0};

            default: ImmExt = 32'd0;
        endcase
    end

endmodule
