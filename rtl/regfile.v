`timescale 1ns / 1ps
//////////////////////////////////////////////////////////////////////////////////
// Company: 
// Engineer: 
// 
// Create Date: 
// Design Name: RV32I 5-Stage Pipelined Processor
// Module Name: regfile
// Project Name: RISC-V Pipeline Verilog
// Target Devices: Xilinx Vivado (Synthesizable)
// Tool Versions: Vivado 2026.1+
// Description: 32 x 32-bit RISC-V Register File.
//              - Dual asynchronous read ports (combinational).
//              - Single synchronous write port (posedge clk).
//              - Register x0 is strictly hardwired to 32'b0 and ignores all writes.
//
// Dependencies: None
// 
// Revision:
// Revision 0.01 - File Created
// Additional Comments:
// - Latches are prevented: read ports use continuous assignments; write port
//   uses positive-edge clocked register transfers.
//////////////////////////////////////////////////////////////////////////////////

module regfile (
    input  wire        clk,
    input  wire        we,
    input  wire [4:0]  rs1,
    input  wire [4:0]  rs2,
    input  wire [4:0]  rd,
    input  wire [31:0] wd,
    output wire [31:0] rd1,
    output wire [31:0] rd2
);

    // 32 architectural 32-bit registers
    reg [31:0] rf [31:0];

    // Initialize registers to 0 for simulation predictability
    integer i;
    initial begin
        for (i = 0; i < 32; i = i + 1) begin
            rf[i] = 32'd0;
        end
    end

    // Dual asynchronous (combinational) read ports
    // Register x0 is strictly hardwired to 32'h00000000
    assign rd1 = (rs1 == 5'd0) ? 32'd0 : rf[rs1];
    assign rd2 = (rs2 == 5'd0) ? 32'd0 : rf[rs2];

    // Synchronous write port: triggered on the rising edge of clk
    // Writes to register x0 are strictly ignored
    always @(posedge clk) begin
        if (we && (rd != 5'd0)) begin
            rf[rd] <= wd;
        end
    end

endmodule
