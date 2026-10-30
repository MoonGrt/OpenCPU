"""Portable, explicit source lists for a freestanding OpenCPU C program."""
from dataclasses import dataclass, field
import hashlib
import json
from pathlib import Path


def _strings(value, name, *, required=False):
    if not isinstance(value, (list, tuple)) or any(not isinstance(item, str) or not item for item in value):
        raise ValueError(f"C project {name} must be a list of nonempty strings")
    if required and not value:
        raise ValueError(f"C project {name} must not be empty")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class CProject:
    sources: tuple[Path, ...]
    include_dirs: tuple[Path, ...] = ()
    defines: tuple[str, ...] = ()
    path: Path | None = None
    version: int = 1
    _manifest_hash: str | None = field(default=None, repr=False, compare=False)

    def __post_init__(self):
        if type(self.version) is not int or self.version != 1:
            raise ValueError("C project version must be 1")
        path = Path(self.path).expanduser().resolve() if self.path is not None else None
        base = path.parent if path is not None else Path.cwd()
        def absolute(value):
            candidate = Path(value).expanduser()
            return (base / candidate).resolve() if not candidate.is_absolute() else candidate.resolve()
        sources = tuple(absolute(source) for source in self.sources)
        if not sources:
            raise ValueError("C project requires at least one source file")
        if any(source.suffix.lower() != ".c" for source in sources):
            raise ValueError("C project sources must be .c files")
        if len(set(sources)) != len(sources):
            raise ValueError("C project sources must not contain duplicates")
        defines = _strings(self.defines, "defines")
        if any("\n" in value or "\r" in value or "\x00" in value for value in defines):
            raise ValueError("C project definitions must each be a single argument")
        object.__setattr__(self, "path", path)
        object.__setattr__(self, "sources", sources)
        object.__setattr__(self, "include_dirs", tuple(absolute(directory) for directory in self.include_dirs))
        object.__setattr__(self, "defines", defines)

    @classmethod
    def load(cls, path):
        path = Path(path).expanduser().resolve()
        content = path.read_bytes()
        try:
            value = json.loads(content.decode("utf-8-sig"))
        except json.JSONDecodeError as error:
            raise ValueError(f"Invalid C project {path}: {error}") from error
        if not isinstance(value, dict):
            raise ValueError("C project must be a JSON object")
        unknown = set(value) - {"version", "sources", "include_dirs", "defines"}
        if unknown:
            raise ValueError("Unknown C project fields: " + ", ".join(sorted(unknown)))
        return cls(
            sources=_strings(value.get("sources"), "sources", required=True),
            include_dirs=_strings(value.get("include_dirs", []), "include_dirs"),
            defines=_strings(value.get("defines", []), "defines"),
            path=path, version=value.get("version"),
            _manifest_hash=hashlib.sha256(content).hexdigest(),
        )
