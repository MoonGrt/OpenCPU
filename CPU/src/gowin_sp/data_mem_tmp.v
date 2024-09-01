//Copyright (C)2014-2024 Gowin Semiconductor Corporation.
//All rights reserved.
//File Title: Template file for instantiation
//Tool Version: V1.9.10.02
//Part Number: GW2A-LV18PG256C8/I7
//Device: GW2A-18
//Device Version: C
//Created Time: Mon Aug 26 14:07:39 2024

//Change the instance name and port connections to the signal names
//--------Copy here to design--------

    data_mem your_instance_name(
        .dout(dout), //output [15:0] dout
        .clk(clk), //input clk
        .oce(oce), //input oce
        .ce(ce), //input ce
        .reset(reset), //input reset
        .wre(wre), //input wre
        .ad(ad), //input [9:0] ad
        .din(din) //input [15:0] din
    );

//--------Copy end-------------------
