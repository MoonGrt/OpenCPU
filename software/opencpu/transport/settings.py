"""Validated settings shared by both graphical serial clients."""
from dataclasses import dataclass


@dataclass(frozen=True)
class SerialSettings:
    port: str = ""
    baud_rate: int = 115200
    data_bits: int = 8
    parity: str = "None"
    stop_bits: str = "1"

    def validate(self):
        if not self.port.strip():
            raise ValueError("Select a serial port")
        if type(self.baud_rate) is not int or self.baud_rate <= 0:
            raise ValueError("Baud rate must be a positive integer")
        if self.data_bits not in (5, 6, 7, 8):
            raise ValueError("The serial driver supports 5, 6, 7 or 8 data bits")
        if self.parity not in ("None", "Odd", "Even", "Mark", "Space"):
            raise ValueError("Unsupported parity")
        if str(self.stop_bits) not in ("1", "1.5", "2"):
            raise ValueError("Stop bits must be 1, 1.5 or 2")
        return self
