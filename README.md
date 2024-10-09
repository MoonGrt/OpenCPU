<div id="top"></div>

[![Contributors][contributors-shield]][contributors-url]
[![Forks][forks-shield]][forks-url]
[![Stargazers][stars-shield]][stars-url]
[![Issues][issues-shield]][issues-url]
[![MIT License][license-shield]][license-url]


<!-- PROJECT LOGO -->
<br />
<div align="center">
    <a href="https://github.com/MoonGrt/FPGA-CPU">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
    </a>
<h3 align="center">FPGA-CPU</h3>
    <p align="center">
    This project is a 16-bit single-cycle CPU system implemented on FPGA, featuring a 100Hz clock frequency and Harvard architecture. It integrates peripherals such as LED, seven-segment display, UART, and switches, with support for UART debugging. It provides a comprehensive solution for embedded system development. 
    <br />
    <a href="https://github.com/MoonGrt/FPGA-CPU"><strong>Explore the docs »</strong></a>
    <br />
    <br />
    <a href="https://github.com/MoonGrt/FPGA-CPU">View Demo</a>
    ·
    <a href="https://github.com/MoonGrt/FPGA-CPU/issues">Report Bug</a>
    ·
    <a href="https://github.com/MoonGrt/FPGA-CPU/issues">Request Feature</a>
    </p>
</div>


<!-- CONTENTS -->
<details open>
  <summary>Contents</summary>
  <ol>
    <li><a href="#file-tree">File Tree</a></li>
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
  ├─ /code/
  ├─ /CPU/
  ├─ /CPU_PPL/
  ├─ /CPU_PPL_INT/
  │ └─ /src/
  │   ├─ para.v
  │   ├─ top.cst
  │   ├─ top.sdc
  │   ├─ top.v
  │   ├─ /bus/
  │   │ ├─ Buffer.v
  │   │ ├─ BUS.v
  │   │ ├─ Buttom.v
  │   │ ├─ Buttom_OutCtrl.v
  │   │ ├─ Counter.v
  │   │ ├─ Deviceclk.v
  │   │ ├─ LED.v
  │   │ ├─ LED_InCtrl.v
  │   │ ├─ RAM.v
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
  │   │ ├─ CMP.v
  │   │ ├─ CPU.v
  │   │ ├─ Crtl.v
  │   │ ├─ CSR.v
  │   │ ├─ CSR.v.bak
  │   │ ├─ EX.v
  │   │ ├─ ID.v
  │   │ ├─ ID_EX.v
  │   │ ├─ IF.v
  │   │ ├─ IF_ID.v
  │   │ ├─ INT.v
  │   │ ├─ INT.v.bak
  │   │ ├─ REG.v
  │   │ └─ WB.v
  │   ├─ /gowin_rom16/
  │   │ ├─ inst_mem.ipc
  │   │ ├─ inst_mem.mod
  │   │ ├─ inst_mem.v
  │   │ └─ inst_mem_tmp.v
  │   ├─ /gowin_sp/
  │   │ ├─ data_mem.ipc
  │   │ ├─ data_mem.mod
  │   │ ├─ data_mem.v
  │   │ └─ data_mem_tmp.v
  │   └─ /gowin_workfile/
  │     ├─ CPU.cr.mti
  │     ├─ CPU.mpf
  │     ├─ prim_sim.v
  │     ├─ tb_top.v
  │     ├─ tcl_stacktrace.txt
  │     └─ vsim.wlf
  ├─ /document/
  ├─ /images/
  └─ /tool/

```
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
[contributors-shield]: https://img.shields.io/github/contributors/MoonGrt/FPGA-CPU.svg?style=for-the-badge
[contributors-url]: https://github.com/MoonGrt/FPGA-CPU/graphs/contributors
[forks-shield]: https://img.shields.io/github/forks/MoonGrt/FPGA-CPU.svg?style=for-the-badge
[forks-url]: https://github.com/MoonGrt/FPGA-CPU/network/members
[stars-shield]: https://img.shields.io/github/stars/MoonGrt/FPGA-CPU.svg?style=for-the-badge
[stars-url]: https://github.com/MoonGrt/FPGA-CPU/stargazers
[issues-shield]: https://img.shields.io/github/issues/MoonGrt/FPGA-CPU.svg?style=for-the-badge
[issues-url]: https://github.com/MoonGrt/FPGA-CPU/issues
[license-shield]: https://img.shields.io/github/license/MoonGrt/FPGA-CPU.svg?style=for-the-badge
[license-url]: https://github.com/MoonGrt/FPGA-CPU/blob/master/LICENSE

