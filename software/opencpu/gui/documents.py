"""Text document identity and atomic saves, without any widget dependency."""
import os
from pathlib import Path
import stat
import tempfile


class Document:
    def __init__(self, text="", path=None, kind="source"):
        self.path = Path(path).expanduser().resolve() if path is not None else None
        self.kind = kind
        self.newline = "\n"
        self.bom = False
        self.text = self._normalize(text)
        self.saved_text = self.text

    @staticmethod
    def _normalize(text):
        return text.replace("\r\n", "\n").replace("\r", "\n")

    @classmethod
    def open(cls, path, kind="source"):
        path = Path(path).expanduser().resolve()
        data = path.read_bytes()
        text = data.decode("utf-8-sig")
        document = cls(text, path, kind)
        document.bom = data.startswith(b"\xef\xbb\xbf")
        document.newline = "\r\n" if "\r\n" in text else "\r" if "\r" in text else "\n"
        return document

    def set_text(self, text):
        self.text = self._normalize(text)

    @property
    def dirty(self):
        return self.text != self.saved_text

    @property
    def title(self):
        if self.path is None:
            return "Untitled*"
        return self.path.name + ("*" if self.dirty else "")

    def save(self, text=None, path=None):
        target = Path(path).expanduser().resolve() if path is not None else self.path
        if target is None:
            raise ValueError("A path is required to save this document")
        content = self._normalize(self.text if text is None else text)
        encoded = content.replace("\n", self.newline).encode("utf-8")
        if self.bom:
            encoded = b"\xef\xbb\xbf" + encoded
        mode = stat.S_IMODE(target.stat().st_mode) if target.exists() else None
        temporary = None
        try:
            with tempfile.NamedTemporaryFile(dir=target.parent, prefix="." + target.name + ".", delete=False) as stream:
                temporary = Path(stream.name)
                stream.write(encoded)
                stream.flush()
                os.fsync(stream.fileno())
            if mode is not None:
                temporary.chmod(mode)
            os.replace(temporary, target)
            temporary = None
        finally:
            if temporary is not None:
                temporary.unlink(missing_ok=True)
        # Failed writes never rebind a document to a destination that was not saved.
        self.path = target
        self.text = self.saved_text = content
        return target
