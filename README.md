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
    <a href="https://github.com/MoonGrt/FPGA-CPU">
    <img src="images/logo.png" alt="Logo" width="80" height="80">
    </a>
<h3 align="center">FPGA-CPU</h3>
    <p align="center">
    This project is a 16-bit single-cycle CPU system implemented on FPGA, featuring a 100Hz clock frequency and Harvard architecture. It integrates peripherals such as LED, seven-segment display, UART, and switches, with support for UART debugging. It provides a comprehensive solution for embedded system development.
    <br />
    <a href="https://github.com/MoonGrt/FPGA-CPU"><strong>Explore the docs »</strong></a>
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
  ├─ /code/
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
  ├─ /document/
  ├─ /GUI_v1/
  │ └─ GUI.py
  ├─ /GUI_v2/
  ├─ /images/
  └─ /Tool/
    ├─ B2H.py
    ├─ coe_to_mi.py
    └─ H2B.py

```



<!-- ABOUT THE PROJECT -->
## About The Project

<p style=" margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;">[![Product Name Screen Shot][product-screenshot]](https://example.com) Here's a blank template to get started: To avoid retyping too much info. Do a search and replace with your text editor for the following: `github_username`, `repo_name`, `twitter_handle`, `linkedin_username`, `email_client`, `email`, `project_title`, `project_description`</p></body></html>
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

