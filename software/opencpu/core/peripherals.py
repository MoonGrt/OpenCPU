"""Register-level SoC peripherals using deterministic instruction-model ticks.

One tick is a software time quantum, not an FPGA clock or a UART bit interval.
The CPU model decides when ticks advance and latches the returned IRQ events.
"""
from collections import deque
from dataclasses import dataclass


def _integer(value, name, minimum, maximum=None):
    if type(value) is not int or value < minimum or (maximum is not None and value > maximum):
        limit = f"{minimum}..{maximum}" if maximum is not None else f">= {minimum}"
        raise ValueError(f"{name} must be an integer in {limit}")
    return value


def _boolean(value, name):
    if type(value) is not bool:
        raise ValueError(f"{name} must be a boolean")
    return value


@dataclass(frozen=True, slots=True)
class _Checkpoint:
    ticks: int
    buttons: int
    switches: int
    led: int
    display: int
    rx: tuple[int, ...]
    tx: tuple[int, ...]
    active: int | None
    remaining: int
    errors: int
    new_errors: int
    events: int
    period: int
    counter: int
    enabled: bool
    periodic: bool
    elapsed: bool
    reconfigured: bool
    output_length: int


class PeripheralModel:
    """GPIO, display, UART FIFOs and Timer for the current SoC register map.

    RX injection makes bytes immediately available. Its IRQ and new error
    events are delivered at the next tick. This lets an error arriving in the
    same quantum as a W1C retain priority, as it does in RTL.
    """

    def __init__(self, fifo_depth=16, uart_frame_ticks=10, enable_uart=True,
                 enable_timer=True, enable_display=True, buttons=0, switches=0):
        self.fifo_depth = _integer(fifo_depth, "fifo_depth", 1, 65536)
        self.uart_frame_ticks = _integer(uart_frame_ticks, "uart_frame_ticks", 1)
        self.enable_uart = _boolean(enable_uart, "enable_uart")
        self.enable_timer = _boolean(enable_timer, "enable_timer")
        self.enable_display = _boolean(enable_display, "enable_display")
        self.buttons = _integer(buttons, "buttons", 0, 15)
        self.switches = _integer(switches, "switches", 0, 15)
        self.uart_output = bytearray()
        self.reset()

    def reset(self):
        """Reset internal devices while retaining configured external inputs."""
        self.ticks = 0
        self.led_value = 0
        self.display_value = 0
        self._rx = deque()
        self._tx = deque()
        self._active = None
        self._remaining = 0
        self._errors = 0
        self._new_errors = 0
        self._events = 0
        self._period = 0
        self._counter = 0
        self._enabled = False
        self._periodic = False
        self._elapsed = False
        self._reconfigured = False
        self.uart_output.clear()

    @property
    def uart_busy(self):
        return self.enable_uart and (self._active is not None or bool(self._tx))

    def _status(self):
        if not self.enable_uart:
            return 0
        can_write = len(self._tx) < self.fifo_depth or (self._active is None and bool(self._tx))
        return (int(bool(self._rx)) | (int(can_write) << 1)
                | (int(self.uart_busy) << 2) | self._errors)

    def read(self, address, side_effects=True):
        address = _integer(address, "address", 0, 65535)
        _boolean(side_effects, "side_effects")
        if address == 0xFF00:
            return self.led_value
        if address == 0xFF10:
            return self.buttons
        if address == 0xFF20:
            return self.switches
        if address == 0xFF30:
            return self.display_value if self.enable_display else 0
        if self.enable_uart:
            if address == 0xFF40:
                if not self._rx:
                    return 0
                return self._rx.popleft() if side_effects else self._rx[0]
            if address == 0xFF41:
                return self._status()
            if address == 0xFF42:
                return self._errors
        if self.enable_timer:
            if address == 0xFF50:
                return self._period & 0xFFFF
            if address == 0xFF51:
                return self._period >> 16
            if address == 0xFF52:
                return int(self._enabled) | (int(self._periodic) << 1)
            if address == 0xFF53:
                return self._counter & 0xFFFF
            if address == 0xFF54:
                return self._counter >> 16
            if address == 0xFF55:
                return int(self._elapsed)
        return 0

    def peek(self, address):
        return self.read(address, side_effects=False)

    def _error(self, mask):
        self._errors |= mask
        self._new_errors |= mask

    def write(self, address, value):
        address = _integer(address, "address", 0, 65535)
        value = _integer(value, "value", 0, 65535)
        if address == 0xFF00:
            self.led_value = value & 15
        elif address == 0xFF30 and self.enable_display:
            self.display_value = value
        elif address == 0xFF40 and self.enable_uart:
            # A ready transmitter can pop a full FIFO in the same quantum as
            # this CPU write. The active byte is separate from FIFO capacity.
            if len(self._tx) == self.fifo_depth and self._active is None:
                self._active = self._tx.popleft()
                self._remaining = self.uart_frame_ticks
            if len(self._tx) < self.fifo_depth:
                self._tx.append(value & 255)
            else:
                self._error(1 << 4)
        elif address == 0xFF42 and self.enable_uart:
            self._errors &= ~(value & 0x38)
        elif self.enable_timer:
            if address in (0xFF50, 0xFF51, 0xFF52):
                self._counter = 0
                self._reconfigured = True
                if address == 0xFF50:
                    self._period = (self._period & 0xFFFF0000) | value
                elif address == 0xFF51:
                    self._period = (self._period & 0xFFFF) | (value << 16)
                else:
                    self._enabled = bool(value & 1)
                    self._periodic = bool(value & 2)
            elif address == 0xFF55 and value & 1:
                self._elapsed = False

    def set_inputs(self, buttons=None, switches=None):
        # Validate both before mutating so invalid input cannot partly apply.
        new_buttons = self.buttons if buttons is None else _integer(buttons, "buttons", 0, 15)
        new_switches = self.switches if switches is None else _integer(switches, "switches", 0, 15)
        self.buttons, self.switches = new_buttons, new_switches

    def inject_uart(self, data, framing_error=False):
        _boolean(framing_error, "framing_error")
        if isinstance(data, str) or isinstance(data, int):
            raise ValueError("UART data must be a bytes-like object or an iterable of byte integers")
        try:
            values = tuple(data)
        except TypeError as error:
            raise ValueError("UART data must be an iterable of byte integers") from error
        for value in values:
            _integer(value, "UART byte", 0, 255)
        if not self.enable_uart:
            return
        if framing_error:
            self._error(1 << 5)
            return
        for value in values:
            self._events |= 1 << 1
            if len(self._rx) < self.fifo_depth:
                self._rx.append(value)
            else:
                self._error(1 << 3)

    def tick(self, ticks=1):
        """Advance device time and return coalesced newly generated IRQ bits."""
        ticks = _integer(ticks, "ticks", 0)
        if not ticks:
            return 0
        self.ticks += ticks
        events = self._events
        self._events = 0
        self._errors |= self._new_errors
        self._new_errors = 0
        # Work is bounded by FIFO capacity, not an arbitrarily large idle
        # advance. Starting a byte consumes its first frame quantum here.
        budget = ticks
        if self.enable_uart:
            while budget:
                if self._active is None:
                    if not self._tx:
                        break
                    self._active = self._tx.popleft()
                    self._remaining = self.uart_frame_ticks
                used = min(budget, self._remaining)
                budget -= used
                self._remaining -= used
                if self._remaining == 0:
                    self.uart_output.append(self._active)
                    self._active = None
        if self._reconfigured:
            self._reconfigured = False
            ticks -= 1
        if ticks:
            if self.enable_timer and self._enabled and self._period:
                until_expiry = self._period - self._counter
                if ticks < until_expiry:
                    self._counter += ticks
                else:
                    events |= 1
                    self._elapsed = True
                    self._counter = (ticks - until_expiry) % self._period if self._periodic else 0
                    if not self._periodic:
                        self._enabled = False
            else:
                self._counter = 0
        return events

    def checkpoint(self):
        """Capture bounded device state and only the completed-output length."""
        return _Checkpoint(
            self.ticks, self.buttons, self.switches, self.led_value, self.display_value,
            tuple(self._rx), tuple(self._tx), self._active, self._remaining,
            self._errors, self._new_errors, self._events, self._period, self._counter,
            self._enabled, self._periodic, self._elapsed, self._reconfigured,
            len(self.uart_output),
        )

    def restore(self, checkpoint):
        """Restore an earlier checkpoint on this timeline, as used by Undo."""
        if not isinstance(checkpoint, _Checkpoint) or checkpoint.output_length > len(self.uart_output):
            raise ValueError("Invalid peripheral checkpoint or output from a discarded future")
        self.ticks = checkpoint.ticks
        self.buttons, self.switches = checkpoint.buttons, checkpoint.switches
        self.led_value, self.display_value = checkpoint.led, checkpoint.display
        self._rx, self._tx = deque(checkpoint.rx), deque(checkpoint.tx)
        self._active, self._remaining = checkpoint.active, checkpoint.remaining
        self._errors, self._new_errors = checkpoint.errors, checkpoint.new_errors
        self._events = checkpoint.events
        self._period, self._counter = checkpoint.period, checkpoint.counter
        self._enabled, self._periodic = checkpoint.enabled, checkpoint.periodic
        self._elapsed, self._reconfigured = checkpoint.elapsed, checkpoint.reconfigured
        del self.uart_output[checkpoint.output_length:]

    def snapshot(self, *, include_output=True):
        """Return a detached view; omit TX history for frequent GUI refreshes."""
        _boolean(include_output, "include_output")
        state = {
            "ticks": self.ticks,
            "gpio": {"buttons": self.buttons, "switches": self.switches,
                     "led": self.led_value, "led_pins": (~self.led_value) & 15},
            "display": {"enabled": self.enable_display, "value": self.display_value},
            "uart": {"enabled": self.enable_uart, "fifo_depth": self.fifo_depth,
                     "frame_ticks": self.uart_frame_ticks, "status": self._status(),
                     "errors": self._errors, "rx_count": len(self._rx), "tx_count": len(self._tx),
                     "rx": list(self._rx), "tx": list(self._tx), "busy": self.uart_busy,
                     "active": self._active, "remaining_ticks": self._remaining,
                     "output_length": len(self.uart_output)},
            "timer": {"available": self.enable_timer, "period": self._period,
                      "counter": self._counter, "enabled": self._enabled,
                      "periodic": self._periodic, "elapsed": self._elapsed},
        }
        if include_output:
            state["uart"]["output"] = list(self.uart_output)
        return state
