"""One validated machine-image format for the CLI, GUI and serial transport."""
from collections.abc import Iterable

from .isa import OPCODES

ROM_WORDS = 1024


def _limit(words: list[int], max_words: int | None) -> list[int]:
    if max_words is not None:
        if type(max_words) is not int or max_words < 0:
            raise ValueError("max_words must be a nonnegative integer or None")
        if len(words) > max_words:
            raise ValueError(f"Image exceeds the configured {max_words}-word ROM")
    return words


def _parse(text: str, *, base: int, width: int, max_words: int | None) -> list[int]:
    alphabet = set("01" if base == 2 else "0123456789abcdefABCDEF")
    words = []
    for line_number, raw in enumerate(text.splitlines(), 1):
        line = raw.strip()
        if not line:
            continue
        if len(line) != width or set(line) - alphabet:
            description = "16-bit binary" if base == 2 else "4-digit hexadecimal"
            raise ValueError(f"line {line_number}: expected one {description} word")
        words.append(int(line, base))
    return _limit(words, max_words)


def parse_binary(text: str, max_words: int | None = ROM_WORDS) -> list[int]:
    return _parse(text, base=2, width=16, max_words=max_words)


def parse_hex(text: str, max_words: int | None = ROM_WORDS) -> list[int]:
    return _parse(text, base=16, width=4, max_words=max_words)


def validate_words(words: Iterable[int], max_words: int | None = None) -> list[int]:
    result = list(words)
    for index, value in enumerate(result):
        if type(value) is not int or not 0 <= value <= 0xFFFF:
            raise ValueError(f"word {index}: expected an integer in 0..65535")
    return _limit(result, max_words)


def format_binary(words: Iterable[int]) -> str:
    return "".join(f"{value:016b}\n" for value in validate_words(words))


def encode_image(text: str, hexadecimal: bool = False, pad_rom: bool = False) -> bytes:
    """Validate the complete image before producing any big-endian payload."""
    words = parse_hex(text) if hexadecimal else parse_binary(text)
    if not words:
        raise ValueError("No machine code to download")
    if pad_rom:
        words += [OPCODES["halt"]] * (ROM_WORDS - len(words))
    return b"".join(value.to_bytes(2, "big") for value in words)
