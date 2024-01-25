**简体中文 | [English](README.md)**
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
    该项目是在 FPGA 上实现的 16 位单周期 CPU 系统，采用 50MHz 时钟频率和哈佛架构。
    <br />
    <a href="https://github.com/MoonGrt/MoonCore"><strong>浏览文档 »</strong></a>
    <br />
    <a href="https://github.com/MoonGrt/MoonCore">查看 Demo</a>
    ·
    <a href="https://github.com/MoonGrt/MoonCore/issues">反馈 Bug</a>
    ·
    <a href="https://github.com/MoonGrt/MoonCore/issues">请求新功能</a>
    </p>
</div>




<!-- CONTENTS -->
<details open>
  <summary>目录</summary>
  <ol>
    <li><a href="#文件树">文件树</a></li>
    <li>
      <a href="#关于本项目">关于本项目</a>
      <ul>
      </ul>
    </li>
    <li><a href="#贡献">贡献</a></li>
    <li><a href="#许可证">许可证</a></li>
    <li><a href="#联系我们">联系我们</a></li>
    <li><a href="#致谢">致谢</a></li>
  </ol>
</details>





<!-- 文件树 -->
## 文件树

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



<!-- 关于本项目 -->
## 关于本项目

<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_1"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">1</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">  specification</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">	16</span>位<span style=" font-family:'Arial','sans-serif';">cpu </span>哈佛结构<span style=" font-family:'Arial','sans-serif';">50MHz</span>主频单周期</p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/block_diagram.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_2"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">2</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">  ISA</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_3"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">1</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">16-bit-inst </span><span style=" font-size:12pt; font-weight:600;">构成</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">第一种指令：适用于<span style=" font-family:'Arial','sans-serif';">add</span>、<span style=" font-family:'Arial','sans-serif';">sub</span>、<span style=" font-family:'Arial','sans-serif';">and</span>、<span style=" font-family:'Arial','sans-serif';">or</span>、<span style=" font-family:'Arial','sans-serif';">xor</span>、<span style=" font-family:'Arial','sans-serif';">sll</span>、<span style=" font-family:'Arial','sans-serif';">srl</span>、<span style=" font-family:'Arial','sans-serif';">addi</span>、<span style=" font-family:'Arial','sans-serif';">subi</span>、<span style=" font-family:'Arial','sans-serif';">andi</span>、<span style=" font-family:'Arial','sans-serif';">ori</span>、<span style=" font-family:'Arial','sans-serif';">xori</span>、<span style=" font-family:'Arial','sans-serif';">slli</span>、<span style=" font-family:'Arial','sans-serif';">srli</span>、<span style=" font-family:'Arial','sans-serif';">beq</span>、<span style=" font-family:'Arial','sans-serif';">blt</span>、<span style=" font-family:'Arial','sans-serif';">lw</span>、<span style=" font-family:'Arial','sans-serif';">sw</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">	命令使用格式为：<span style=" font-family:'Arial','sans-serif';">opcode rd rs  xxx</span>（将<span style=" font-family:'Arial','sans-serif';">rd</span>、<span style=" font-family:'Arial','sans-serif';">rs</span>两个寄存器指向的值，进行<span style=" font-family:'Arial','sans-serif';">opcode</span>对应的计算操作，再将结果存在<span style=" font-family:'Arial','sans-serif';">rd</span>中。这种命令空余两个指令位未使用） </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/isa_type1.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">第二种指令：适用于<span style=" font-family:'Arial','sans-serif';">li</span>、 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">命令使用格式为：<span style=" font-family:'Arial','sans-serif';">li rd xxxxxxxx </span>（将后面八位的立即数，放入<span style=" font-family:'Arial','sans-serif';">rd</span>指向的寄存器中） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">（多这么一条指令主要是为了方便向寄存器填入值。有了这个指令能一次性向某个寄存器填入<span style=" font-family:'Arial','sans-serif';">8</span>位数据） </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/isa_type2.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_4"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">2</span><span style=" font-size:12pt; font-weight:600;">）指令效果解释</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">	参考前面画板中框图内容 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_5"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">3</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. CPU</span><span style=" font-size:14pt; font-weight:600;">架构</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">cpu</span>架构主要参考：<span style=" font-family:'Arial','sans-serif';">https://www.zhihu.com/column/c_1530950608688910336</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_6"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">1</span><span style=" font-size:12pt; font-weight:600;">）整体框架图</span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/overall_rtl.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">整体</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">cpu</span><span style=" font-weight:600;">模块：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n                   </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">irq                              </span>中断信号（） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_data &amp; inst_addr    </span>指令地址以及指令内容 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">mem_rd &amp; mem_wd      cpu</span>的输入输出数据 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">mem_addr                   cpu</span>的输入输出地址 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">mem_crtl                     cpu</span>的输入输出控制 </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><a name="heading_7"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">2</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">ctrl</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ctrl.png" /></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/IF.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">控制模块</span>：（<span style=" font-family:'Arial','sans-serif';">CU</span>） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">将输入的指令截取出相应部分，通过译码<span style=" font-family:'Arial','sans-serif';">opcode</span>，生成各个多路复用器的控制信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入</span>： </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">rst_n               </span>复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst                 </span>指令 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">CMPout            EX</span>模块中<span style=" font-family:'Arial','sans-serif';">CMP</span>的比较结果 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出</span>： </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUop             alu</span>模块执行的操作<span style=" font-family:'Arial','sans-serif';">(</span>加、减、<span style=" font-family:'Arial','sans-serif';">and</span>、<span style=" font-family:'Arial','sans-serif';">or</span>、<span style=" font-family:'Arial','sans-serif';">xor</span>、左移、右移） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMSel            </span>控制<span style=" font-family:'Arial','sans-serif';">ID</span>输出是指令中的<span style=" font-family:'Arial','sans-serif';">5</span>位立即数，还是<span style=" font-family:'Arial','sans-serif';">8</span>位立即数 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMop            </span>控制输入给<span style=" font-family:'Arial','sans-serif';">alu</span>和<span style=" font-family:'Arial','sans-serif';">cmp</span>的数据是立即数，还是寄存器中的数 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">PCSel               </span>控制<span style=" font-family:'Arial','sans-serif';">pc</span>是下一条指令，还是<span style=" font-family:'Arial','sans-serif';">branch_pc</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RWSel             </span>控制将<span style=" font-family:'Arial','sans-serif';">alu</span>输出结果写回到寄存器组，还是写回外部读取的地址 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RegWe            </span>寄存器堆的写写使能信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">mem_ctrl         </span>控制对外部设备是读操作，还是写操作 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_8"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">3</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">IF</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/if.png" /></p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">取指令模块</span>： </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">输出<span style=" font-family:'Arial','sans-serif';">PC</span>（<span style=" font-family:'Arial','sans-serif';">inst_addr</span>）向外部<span style=" font-family:'Arial','sans-serif';">rom</span>读取指令。由输入的<span style=" font-family:'Arial','sans-serif';">PCSel</span>控制，下一条指令是顺位下一条，还是输入的<span style=" font-family:'Arial','sans-serif';">branch_pc</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入</span>： </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n  </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_data    </span>读取外部<span style=" font-family:'Arial','sans-serif';">rom</span>得到的<span style=" font-family:'Arial','sans-serif';">16</span>位指令 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">branch_pc   </span>跳转命令地址 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">PCSel          </span>命令选择信号，控制下一条信号是输入的跳转命令，还是顺序读取。该信号由<span style=" font-family:'Arial','sans-serif';">ctrl</span>块生成 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; text-decoration: line-through;">irq              </span><span style=" text-decoration: line-through;">中断信号（）</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出</span>： </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_addr     </span>程序指针，读取外部<span style=" font-family:'Arial','sans-serif';">rom</span>的地址（实际上就是<span style=" font-family:'Arial','sans-serif';">pc</span>指针） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_9"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">4</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">ID</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/id.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">译码模块：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">主要分为两块，上方多路复用通过<span style=" font-family:'Arial','sans-serif';">IMMsel</span>选择输出指令中的<span style=" font-family:'Arial','sans-serif';">5</span>位立即数还是<span style=" font-family:'Arial','sans-serif';">8</span>位立即数。下方是寄存器堆（通用寄存器），解码指令中的<span style=" font-family:'Arial','sans-serif';">rs rd</span>，输出<span style=" font-family:'Arial','sans-serif';">rs rd</span>指向寄存器的值<span style=" font-family:'Arial','sans-serif';">RD RS</span>；并将<span style=" font-family:'Arial','sans-serif';">WB</span>数据写入到<span style=" font-family:'Arial','sans-serif';">rd</span>指向的寄存器。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n         </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">WB                   WB</span>模块写回寄存器的数据 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMSel             </span>控制输出是指令中的<span style=" font-family:'Arial','sans-serif';">5</span>位立即数，还是<span style=" font-family:'Arial','sans-serif';">8</span>位立即数（会自动将立即数扩展为<span style=" font-family:'Arial','sans-serif';">16</span>位） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst                   </span>传入指令，并从指令中解码出寄存器指针 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RegWe              </span>寄存器写入使能信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMM                  </span>解码得到的立即数 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RD &amp; RS            </span>解码<span style=" font-family:'Arial','sans-serif';">rs</span>，<span style=" font-family:'Arial','sans-serif';">rd</span>得到的寄存器中值 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_10"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">5</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">EX</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ex.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">执行模块：由</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">ALU</span><span style=" font-weight:600;">，</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">CMP</span><span style=" font-weight:600;">，</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">MUX</span><span style=" font-weight:600;">构成</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">经过<span style=" font-family:'Arial','sans-serif';">IMMop</span>选择后，将输入的数据计算或比较出结果。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RD RS IMM             </span>输入执行模块的数据：<span style=" font-family:'Arial','sans-serif';">rs rd</span>指向的数据以及立即数 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUop                    ALU</span>执行的操作<span style=" font-family:'Arial','sans-serif';">(</span>加、减、<span style=" font-family:'Arial','sans-serif';">and</span>、<span style=" font-family:'Arial','sans-serif';">or</span>、<span style=" font-family:'Arial','sans-serif';">xor</span>、左移、右移） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">IMMop                   </span>控制输入给<span style=" font-family:'Arial','sans-serif';">alu</span>和<span style=" font-family:'Arial','sans-serif';">cmp</span>的数据是立即数，还是寄存器中的数 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUout                   ALU</span>计算结果 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">CMPout                  </span>比较结果 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_11"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">6</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">WB</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/wb.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-weight:600;">写回模块：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">一个多路复用模块，用于选择将哪个数据写回到<span style=" font-family:'Arial','sans-serif';">ID</span>模块的寄存器堆中。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ALUout                        </span>计算结果 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">DRAMdata                       lw</span>命令，从<span style=" font-family:'Arial','sans-serif';">cpu</span>外部读取的数据 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">RWSel                          </span>控制多路复用器，选择写回的数据类型 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">WB                              </span>写回寄存器的数据 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">  </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_12"></a><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">4</span><span style=" font-family:'Arial','sans-serif'; font-size:14pt; font-weight:600;">. BUS</span><span style=" font-size:14pt; font-weight:600;">结构</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_13"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">1</span><span style=" font-size:12pt; font-weight:600;">）整体结构</span> </p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/address.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Arial','sans-serif'; font-weight:600;">BUS</span><span style=" font-weight:600;">总体结构</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">cpu</span>为哈佛结构，指令和地址分开读取。<span style=" font-family:'Arial','sans-serif';">cpu</span>与<span style=" font-family:'Arial','sans-serif';">BUS</span>有两组线，数据通路：地址（<span style=" font-family:'Arial','sans-serif';">addr</span>）、数据（<span style=" font-family:'Arial','sans-serif';">data</span>）、控制（<span style=" font-family:'Arial','sans-serif';">ctrl</span>）；指令通路：地址（<span style=" font-family:'Arial','sans-serif';">inst_addr</span>）、数据（<span style=" font-family:'Arial','sans-serif';">inst_data</span>）。指令通路直接与<span style=" font-family:'Arial','sans-serif';">BUS</span>中的<span style=" font-family:'Arial','sans-serif';">rom</span>相连。数据通路与<span style=" font-family:'Arial','sans-serif';">ram</span>和其他外设相连，通过<span style=" font-family:'Arial','sans-serif';">addr</span>的地址与设备基地址比较来使能相应功能。<span style=" font-family:'Arial','sans-serif';">BUS</span>的其他线路直接直接连接外设：<span style=" font-family:'Arial','sans-serif';">led</span>、<span style=" font-family:'Arial','sans-serif';">switch</span>、<span style=" font-family:'Arial','sans-serif';">bt</span>、<span style=" font-family:'Arial','sans-serif';">uart</span>、<span style=" font-family:'Arial','sans-serif';">tube</span>。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n         </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">bt_rx                 </span>蓝牙接收口 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">uart_rx              uart</span>接收口 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl                    BUS</span>读写控制，<span style=" font-family:'Arial','sans-serif';">1</span>为写，<span style=" font-family:'Arial','sans-serif';">0</span>为读 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr                  BUS</span>读写地址 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data                  BUS</span>读写数据<span style=" font-family:'Arial','sans-serif';">(</span>这是一个双端口，既可以输出也可以输入<span style=" font-family:'Arial','sans-serif';">)</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_addr           </span>指令地址 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">switch               </span>外部拨码开关（<span style=" font-family:'Arial','sans-serif';">8</span>个） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">bt_tx                                    </span>蓝牙发送口 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">uart_tx                                 uart</span>发送口 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">inst_data                              inst_addr</span>读取外部<span style=" font-family:'Arial','sans-serif';">rom</span>得到的指令内容 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif'; text-decoration: line-through;">irq_bt irq_timer irq_uart         </span><span style=" text-decoration: line-through;">蓝牙、定时器、</span><span style=" font-family:'Arial','sans-serif'; text-decoration: line-through;">uart</span><span style=" text-decoration: line-through;">中断</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">led                                       led</span>接口（<span style=" font-family:'Arial','sans-serif';">8</span>个） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">tube_en seg_led1 seg_led2     </span>数码管接口（<span style=" font-family:'Arial','sans-serif';">4</span>个数码管为一组，有两组） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_14"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">2</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">ROM </span></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/rom.png" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">指令储存。例化一个<span style=" font-family:'Arial','sans-serif';">rom ip</span>核，写入<span style=" font-family:'Arial','sans-serif';">coe</span>初始化文件。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">a              </span>连接<span style=" font-family:'Arial','sans-serif';">inst_addr</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">spo          </span>输出相应的指令内容。直接连接<span style=" font-family:'Arial','sans-serif';">inst_data</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_15"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">3</span><span style=" font-size:12pt; font-weight:600;">）</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">RAM</span> </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p>
<p align="center" style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><img src="Document/images/ram.png" height="400" /></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">指令储存。例化一个<span style=" font-family:'Arial','sans-serif';">rom ip</span>核，写入<span style=" font-family:'Arial','sans-serif';">coe</span>初始化文件。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n    </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">EN               </span>模块使能信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr             </span>暂时没用，主要是用来读写<span style=" font-family:'Arial','sans-serif';">ram</span>内部寄存器，但目前内部无配置寄存器 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl               </span>控制是读数据还是写数据<span style=" font-family:'Arial','sans-serif';"> </span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">&amp;</span><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data             </span>输入或输出数据 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><a name="heading_16"></a><span style=" font-size:12pt; font-weight:600;">（</span><span style=" font-family:'Arial','sans-serif'; font-size:12pt; font-weight:600;">4</span><span style=" font-size:12pt; font-weight:600;">）外设</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">注意：外设<span style=" font-family:'Arial','sans-serif';">led</span>、<span style=" font-family:'Arial','sans-serif';">tube</span>等设备的控制时钟频率不能太高。需要将<span style=" font-family:'Arial','sans-serif';">100MHz</span>的主频分频后共给外设设备。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">分频模块：</span>将输入时钟分频 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><span style=" font-family:'Arial','sans-serif'; font-weight:600;">LED</span><span style=" font-weight:600;">模块:</span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;">控制<span style=" font-family:'Arial','sans-serif';">8</span>个<span style=" font-family:'Arial','sans-serif';">led</span>灯的亮灭。 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">clk &amp; rst_n    </span>时钟和复位信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">deviceClk      </span>外设时钟 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">EN               </span>模块使能信号 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">addr             </span>暂时没用，主要是用来读写<span style=" font-family:'Arial','sans-serif';">led</span>设备内部寄存器，但目前内部无配置寄存器 </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">ctrl               </span>控制是读数据还是写数据（对于<span style=" font-family:'Arial','sans-serif';">led</span>，不能读数据，只能写） </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">led               </span>直接连接上外部<span style=" font-family:'Arial','sans-serif';">led</span>引脚<span style=" font-family:'Arial','sans-serif';"> </span></p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-weight:600;">输入</span><span style=" font-family:'Arial','sans-serif'; font-weight:600;">&amp;</span><span style=" font-weight:600;">输出：</span> </p>
<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; line-height:120%;"><span style=" font-family:'Arial','sans-serif';">data             </span>输入或输出数据 </p>
<p style="-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;"><br /></p></body></html>
<p align="right">(<a href="#top">top</a>)</p>



<!-- 贡献 -->
## 贡献

贡献让开源社区成为了一个非常适合学习、互相激励和创新的地方。你所做出的任何贡献都是**受人尊敬**的。

如果你有好的建议，请复刻（fork）本仓库并且创建一个拉取请求（pull request）。你也可以简单地创建一个议题（issue），并且添加标签「enhancement」。不要忘记给项目点一个 star！再次感谢！

1. 复刻（Fork）本项目
2. 创建你的 Feature 分支 (`git checkout -b feature/AmazingFeature`)
3. 提交你的变更 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到该分支 (`git push origin feature/AmazingFeature`)
5. 创建一个拉取请求（Pull Request）
<p align="right">(<a href="#top">top</a>)</p>



<!-- 许可证 -->
## 许可证

根据 MIT 许可证分发。打开 [LICENSE](LICENSE) 查看更多内容。
<p align="right">(<a href="#top">top</a>)</p>



<!-- 联系我们 -->
## 联系我们

MoonGrt - 1561145394@qq.com
Project Link: [MoonGrt/MoonCore](https://github.com/MoonGrt/MoonCore)

<p align="right">(<a href="#top">top</a>)</p>



<!-- 致谢 -->
## 致谢

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

