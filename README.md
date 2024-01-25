**English | [简体中文](README_cn.md)**
<div id="top"></div>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
    <a href="https://github.com/MoonGrt/MoonCore">
    <img src="Document/images/logo.png" alt="Logo" width="80" height="80">
    </a>
<h3 align="center">MoonCore</h3>
    <p align="center">
    This project is a 16-bit single-cycle CPU system implemented on FPGA, featuring a 100Hz clock frequency and Harvard architecture. 
    <br />
    <a href="https://github.com/MoonGrt/MoonCore"><strong>Explore the docs »</strong></a>
    <br />
    <a href="https://github.com/MoonGrt/MoonCore">View Demo</a>
    ·
    <a href="https://github.com/MoonGrt/MoonCore/issues">Report Bug</a>
    ·
    <a href="https://github.com/MoonGrt/MoonCore/issues">Request Feature</a>
    </p>
</div>




<!-- CONTENTS -->
<details open>
  <summary>Contents</summary>
  <ol>
    <li><a href="#file-tree">File Tree</a></li>
    <li>
      <a href="#about-the-project">About The Project</a>
      <ul>
      </ul>
    </li>
    <li><a href="#contributing">Contributing</a></li>
    <li><a href="#license">License</a></li>
    <li><a href="#contact">Contact</a></li>
    <li><a href="#acknowledgments">Acknowledgments</a></li>
  </ol>
</details>





<!-- FILE TREE -->
## File Tree

```
└─ Project
  ├─ LICENSE
  ├─ README.md
  ├─ /Code/
  │ └─ whole
  ├─ /CPU/
  │ └─ /src/
  │   ├─ para.v
  │   ├─ top.v
  │   ├─ /bus/
  │   │ ├─ BUS.v
  │   │ ├─ Buttom.v
  │   │ ├─ Buttom_OutCtrl.v
  │   │ ├─ Counter.v
  │   │ ├─ Deviceclk.v
  │   │ ├─ LED.v
  │   │ ├─ LED_InCtrl.v
  │   │ ├─ RAM.v
  │   │ ├─ ROM.v
  │   │ ├─ Switch.v
  │   │ ├─ Switch_OutCtrl.v
  │   │ ├─ Timer.v
  │   │ ├─ Tube.v
  │   │ ├─ Tube_InCtrl.v
  │   │ ├─ UART.v
  │   │ ├─ uart_recv.v
  │   │ ├─ uart_rx.v
  │   │ ├─ uart_send.v
  │   │ └─ uart_tx.v
  │   ├─ /cpu/
  │   │ ├─ ALU.v
  │   │ ├─ CLINT.v
  │   │ ├─ CMP.v
  │   │ ├─ CPU.v
  │   │ ├─ Crtl.v
  │   │ ├─ CSR.v
  │   │ ├─ EX.v
  │   │ ├─ ID.v
  │   │ ├─ ID_EX.v
  │   │ ├─ IF.v
  │   │ ├─ IF_ID.v
  │   │ ├─ REG.v
  │   │ └─ WB.v
  │   └─ /utils/
  │     ├─ Buffer.v
  │     ├─ Buffer_Shift.v
  │     ├─ PPLreg.v
  │     └─ RAM_Gen.v
  ├─ /Document/
  │ ├─ isa.xlsx
  │ └─ Mindmap.md
  ├─ /GUI_v1/
  │ └─ GUI.py
  ├─ /GUI_v2/
  │ └─ GUI.py
  └─ /Tool/
    ├─ B2H.py
    ├─ coe_to_mi.py
    └─ H2B.py

```



<!-- ABOUT THE PROJECT -->
## About The Project

<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_1"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">1</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU  specification</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">	16-bit cpu, harvard architecture, 50MHz main clock, single cycle</span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/block_diagram.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_2"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">2</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU  ISA</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_3"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">1</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">16-bit-inst</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">The first command is applicable to add, sub, and, or, xor, sll, srl, addi, subi, andi, ori, xori, slli, srli, beq, blt, lw, sw. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">The format of the command is: opcode rd rs xxx (the value pointed to by the rd and rs registers will be calculated by opcode, and the result will be stored in rd. This command leaves two unused bits.) </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/isa_type1.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">The second command: applies to li, </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">The format of the command is: li rd xxxxxxxxxx (puts the next eight bits into the register pointed to by rd). </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">(The main reason for this extra instruction is to make it easier to fill the registers with values. With this instruction, you can fill 8 bits of data into a register at one time). </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/isa_type2.png" /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_5"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">3</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU Architecture</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">cpu architecture main reference: https://www.zhihu.com/column/c_1530950608688910336</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(1) </span><span style=" font-size:12pt; font-weight:600;">Overall framework diagram</span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/overall_rtl.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Overall CPU Module:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">clk &amp; rst_n           Clock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">irq                   Interrupt signal</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">inst_data &amp; inst_addr Instruction address and instruction content </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">mem_rd &amp; mem_wd       Cpu input/output data </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">mem_addr              Cpu's input/output address </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">mem_crtl              Cpu input/output control </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(2) ctrl</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ctrl.png" /></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/IF.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Control Unit:</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">Intercepts the corresponding part of the input command and generates the control signals for each multiplexer by decoding the opcode. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">rst_n      Reset signal </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">inst       Instruction </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">CMPout     Comparison result of the CMP in the EX module. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUop           </span>Operations performed by the ALUop alu module (add, subtract, and, or, xor, left shift, right shift)  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMSel          </span>Controls whether the ID output is a 5-bit immediate number from the instruction or an 8-bit immediate number </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMop            </span>Controls whether the input to alu and cmp is an immediate number or a number in a register </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">PCSel            </span>Controls whether pc is the next instruction or branch_pc </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RWSel           </span>Controls whether the alu output is written back to the register set or to an externally read address </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RegWe          </span>Write-write enable signal for the register stack </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">mem_ctrl       </span>Controls whether the external device is read or write. </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(3) IF</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/if.png" /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Fetchh Instruction Module:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">The output PC (inst_addr) reads instructions to the external rom. Controlled by the input PCSel, whether the next instruction is the next in line or the input branch_pc </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n   C</span>lock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_data      </span>Read 16-bit instruction obtained from external rom </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">branch_pc    </span>Jump command address  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">PCSel         </span>Command selection signal that controls whether the next signal is a jump command from the input or a sequential read.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">irq                I</span>nterrupt signal</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_addr     P</span>rogramme pointer to read the address of the external rom</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(4) ID</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/id.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Decode Module:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">It is mainly divided into two blocks, the upper multiplexer selects whether to output the 5-bit immediate number or the 8-bit immediate number in the instruction via IMMsel. The lower part is a register stack (general purpose register) that decodes rs rd in the instruction and outputs the value RD RS of the register pointed by rs rd; and writes the WB data to the register pointed by rd. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n         C</span>lock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">WB                    </span>WB module writes back data to registers </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMSel               </span>Controls whether the output is a 5-bit immediate number from the instruction, or an 8-bit immediate number </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst                     P</span>asses in instruction and decodes register pointer from instruction </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RegWe              </span>Register write enable signal </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMM                     </span>Immediate number obtained by IMM decoding </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RD &amp; RS            </span>Decode rs, rd to get the value in the register. </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(5) EX</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ex.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Execution Module: consists of ALU, CMP, MUX</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">After IMMop selection, the input data will be calculated or compared with the result. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RD RS IMM          </span>Input data to the execution module: data pointed to by rs rd and immediate number </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUop                   </span>Operations performed by ALU (add, subtract, and, or, xor, left shift, right shift) </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMop                    </span>Controls whether the data input to alu and cmp is an immediate number or a number in a register </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUout                   </span>ALU calculation result </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">CMPout                  </span>Comparison result </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(6) WB</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/wb.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">Write Back Module:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">A multiplexing module that selects which data to write back into the ID module's register stack. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUout                    C</span>alculation result. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">DRAMdata               l</span>w command, data read from outside the cpu </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RWSel                    C</span>ontrol multiplexer that selects the type of data to be written back to the cpu </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">WB                         D</span>ata written back to registers </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_12"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">4</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. BUS Architecture</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(1) </span><span style=" font-size:12pt; font-weight:600;">Overall structure</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">The cpu is a Harvard structure, and instructions and addresses are read separately. cpu has two sets of wires to the BUS, the data path: address (addr), data (data), control (ctrl); and the instruction path: address (inst_addr), data (inst_data). The instruction path is directly connected to the rom in the BUS. The data path is connected to ram and other peripherals, and the corresponding function is enabled by comparing the address of the addr with the base address of the device. other lines of the BUS are directly connected to peripherals: led, switch, bt, uart, tube. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n              </span>Clock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">bt_rx                 </span>   Bluetooth receive port </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">uart_rx                    U</span>art receive port </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl                          </span>BUS read/write control, 1 is write, 0 is read </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr                        </span>BUS read/write address </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data                        </span>BUS read/write data (this is a dual port, can be both output and input) </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_addr              </span> Instruction address </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">switch                     </span>External dip switches (8) </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">bt_tx                        </span>Bluetooth transmit port </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">uart_tx                     U</span>art transmit port </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_data           </span>   inst_addr Read command content from external rom. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; text-decoration: line-through;">irq_bt irq_timer irq_uart    </span>bluetooth, timer, uart interrupt </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">led                           </span>led interfaces (8) </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">tube_en seg_led1 seg_led2   </span>digital tube interface (4 digital tubes in a group, there are two groups)</p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(2) ROM </span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/rom.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Instruction storage. Example of a rom ip core written to a coe initialisation file. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">a              C</span>onnect inst_addr </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">spo         </span>Outputs the contents of the corresponding instruction. Direct connection to inst_data </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(3) RAM</span> </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ram.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">Instruction storage. Example of a rom ip core written to a coe initialisation file. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n    </span>clock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">EN                </span>Module enable signal </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr              Address</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl               </span>Controls whether to read or write data.</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input &amp; Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data             </span>Input or output data </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">(4) </span><span style=" font-size:12pt; font-weight:600;">外设</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">Note: The control clock frequency of peripheral led, tube and other devices cannot be too high. It is necessary to divide the main frequency of 100MHz and give it to the peripheral devices. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Arial','sans-serif'; font-weight:600;">LED</span><span style=" font-weight:600;">:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">Controls 8 led lights on and off. </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n    </span>Clock and reset signals </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">deviceClk      </span>Peripheral clock </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">EN                </span>Module enable signal </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr              </span>Address</p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl               </span>control is to read data or write data (for led, can not read data, only write) </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">led               D</span>irectly connected to the external led pin <span style=" font-family:'Arial','sans-serif';"> </span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">Input &amp; Output:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data             </span>Input or output data </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html>
<p align="right">(<a href="#top">top</a>)</p>



<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.
If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again!
1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request
<p align="right">(<a href="#top">top</a>)</p>



<!-- LICENSE -->
## License

Distributed under the MIT License. See `LICENSE` for more information.
<p align="right">(<a href="#top">top</a>)</p>



<!-- CONTACT -->
## Contact

MoonGrt - 1561145394@qq.com
Project Link: [MoonGrt/](https://github.com/MoonGrt/)
<p align="right">(<a href="#top">top</a>)</p>



<!-- ACKNOWLEDGMENTS -->
## Acknowledgments

* [Choose an Open Source License](https://choosealicense.com)
* [GitHub Emoji Cheat Sheet](https://www.webpagefx.com/tools/emoji-cheat-sheet)
* [Malven's Flexbox Cheatsheet](https://flexbox.malven.co/)
* [Malven's Grid Cheatsheet](https://grid.malven.co/)
* [Img Shields](https://shields.io)
* [GitHub Pages](https://pages.github.com)
* [Font Awesome](https://fontawesome.com)
* [React Icons](https://react-icons.github.io/react-icons/search)
<p align="right">(<a href="#top">top</a>)</p>




<!-- MARKDOWN LINKS & IMAGES -->
<!-- https://www.markdownguide.org/basic-syntax/#reference-style-links -->
[contributors-shield]: https://img.shields.io/github/contributors/MoonGrt/MoonCore.svg?style=for-the-badge
[contributors-url]: https://github.com/MoonGrt/MoonCore/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/MoonGrt/MoonCore.svg?style=for-the-badge
[forks-url]: https://github.com/MoonGrt/MoonCore/network/members
[stars-shield]: https://img.shields.io/github/stars/MoonGrt/MoonCore.svg?style=for-the-badge
[stars-url]: https://github.com/MoonGrt/MoonCore/stargazers
[issues-shield]: https://img.shields.io/github/issues/MoonGrt/MoonCore.svg?style=for-the-badge
[issues-url]: https://github.com/MoonGrt/MoonCore/issues
[license-shield]: https://img.shields.io/github/license/MoonGrt/MoonCore.svg?style=for-the-badge
[license-url]: https://github.com/MoonGrt/MoonCore/blob/master/LICENSE

