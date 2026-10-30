"""Text document identity and atomic saves, without any widget dependency."""
import os
from pathlib import Path
import stat
import tempfile


class Document:
    def __init__(self, text="", path=None, kind="source", *, backend=None, language=None):
        self.path = Path(path).expanduser().resolve() if path is not None else None
        self.kind = kind
        suffix = self.path.suffix.lower() if self.path is not None else ""
        self.backend = backend or ("llvm" if language in ("c", "llvm-ir") or suffix in (".c", ".h", ".ll") else "simple")
        if self.backend not in ("simple", "llvm"):
            raise ValueError(f"Unknown compiler backend: {self.backend}")
        self.language = language or ("c" if suffix in (".c", ".h") else "llvm-ir" if self.backend == "llvm" else "auto")
        if self.language not in ("auto", "c", "llvm-ir"):
            raise ValueError(f"Unknown compiler language: {self.language}")
        if self.backend == "simple" and self.language != "auto":
            raise ValueError("C and LLVM IR languages require the LLVM backend")
        self.revision = 0
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
        normalized = self._normalize(text)
        if normalized != self.text:
            self.text = normalized
            self.revision += 1

    def set_backend(self, backend):
        if backend not in ("simple", "llvm"):
            raise ValueError(f"Unknown compiler backend: {backend}")
        if backend != self.backend:
            self.backend = backend
            if backend == "simple":
                self.language = "auto"
            elif self.language == "auto":
                self.language = "c" if self.path is not None and self.path.suffix.lower() in (".c", ".h") else "llvm-ir"
            self.revision += 1

    def set_language(self, language):
        if language not in ("c", "llvm-ir"):
            raise ValueError(f"Unknown LLVM language: {language}")
        if self.language != language or self.backend != "llvm":
            self.backend = "llvm"
            self.language = language
            self.revision += 1

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
        if self.path != target:
            self.revision += 1
        self.path = target
        self.set_text(content)
        self.saved_text = content
        return target
