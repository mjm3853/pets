"""
Content-addressed disk cache shared by ingest and render.

Both detection and cropping are pure functions of (file bytes, parameters),
so both are cacheable on a key derived from content rather than path. That
also lays the groundwork for stable identity (D13): a content key survives
renames, moves and re-imports, which positional ids do not.

Hashing 20 GB on every run would defeat the point, so digests are memoised
against (path, size, mtime_ns) in a sidecar index. A file that has not been
touched is never read twice.
"""

import hashlib
import json
from pathlib import Path

INDEX = "index.json"


class Cache:
    """A sharded blob store under `root`, namespaced by kind."""

    def __init__(self, root: Path, namespace: str):
        self.dir = Path(root) / namespace
        self.dir.mkdir(parents=True, exist_ok=True)
        self.hits = self.misses = 0

    def _path(self, key: str, ext: str) -> Path:
        d = self.dir / key[:2]
        return d / f"{key}{ext}"

    def get(self, key: str, ext: str = ".bin") -> bytes | None:
        p = self._path(key, ext)
        if p.exists():
            self.hits += 1
            return p.read_bytes()
        self.misses += 1
        return None

    def put(self, key: str, data: bytes, ext: str = ".bin") -> None:
        p = self._path(key, ext)
        p.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.with_suffix(p.suffix + ".tmp")
        tmp.write_bytes(data)
        tmp.replace(p)

    def get_json(self, key: str):
        raw = self.get(key, ".json")
        return json.loads(raw) if raw else None

    def put_json(self, key: str, obj) -> None:
        self.put(key, json.dumps(obj, separators=(",", ":")).encode(), ".json")

    @property
    def rate(self) -> str:
        total = self.hits + self.misses
        return f"{self.hits}/{total} ({self.hits / total:.0%})" if total else "0/0"


class Digests:
    """sha256 of file contents, memoised on (path, size, mtime_ns)."""

    def __init__(self, root: Path):
        self.file = Path(root) / INDEX
        self.file.parent.mkdir(parents=True, exist_ok=True)
        try:
            self._map = json.loads(self.file.read_text())
        except Exception:
            self._map = {}
        self._dirty = False

    def of(self, path: Path) -> str:
        st = path.stat()
        stamp = f"{st.st_size}:{st.st_mtime_ns}"
        hit = self._map.get(str(path))
        if hit and hit[0] == stamp:
            return hit[1]
        h = hashlib.sha256()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
        key = h.hexdigest()[:20]
        self._map[str(path)] = [stamp, key]
        self._dirty = True
        return key

    def save(self) -> None:
        if self._dirty:
            self.file.write_text(json.dumps(self._map, separators=(",", ":")))
            self._dirty = False


def param_key(content_key: str, *parts) -> str:
    """Key for a derived artifact: content plus the parameters that made it."""
    tag = ":".join(str(p) for p in parts)
    return hashlib.sha256(f"{content_key}:{tag}".encode()).hexdigest()[:20]
