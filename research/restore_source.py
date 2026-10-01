"""Restore checked embedded sources; never execute document commands."""
import argparse
import hashlib
import json
import re
from pathlib import Path, PurePosixPath


def restore(master, destination):
    document = master.read_text(encoding="utf-8")
    blocks = re.findall(
        r"^<!-- CHAMGAP_FILE_BEGIN path=([^\n ]+) sha256=([0-9a-f]{64}) -->\n"
        r"~~~~[^\n]*\n(.*?)^~~~~\n<!-- CHAMGAP_FILE_END -->\s*$",
        document, re.MULTILINE | re.DOTALL,
    )
    if len(blocks) != 52:
        raise ValueError(f"Expected 52 source files; found {len(blocks)}")
    destination = destination.resolve()
    if destination.exists() and any(destination.iterdir()):
        raise FileExistsError("Restoration requires a new or empty directory")
    checked, names = [], set()
    for name, expected, body in blocks:
        path = PurePosixPath(name)
        if path.is_absolute() or any(p in (".", "..") for p in path.parts) or ":" in name or "\\" in name:
            raise ValueError(f"Unsafe source path: {name}")
        if name in names:
            raise ValueError(f"Duplicate path: {name}")
        names.add(name)
        target = (destination / Path(*path.parts)).resolve()
        if destination not in target.parents:
            raise ValueError(f"Path escaped output: {name}")
        raw = body.encode("utf-8")
        actual = hashlib.sha256(raw).hexdigest()
        if actual != expected:
            raise ValueError(f"Checksum mismatch: {name}")
        checked.append((target, raw, name, actual))
    for target, raw, _, _ in checked:
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as stream:
            stream.write(raw)
    manifest = {
        "source_document": master.name,
        "source_document_sha256": hashlib.sha256(master.read_bytes()).hexdigest(),
        "restored_files": len(checked),
        "document_commands_executed": False,
        "files": {name: digest for _, _, name, digest in checked},
    }
    (destination.parent / "source-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(f"Restored {len(checked)} files with SHA-256 checks. No source executed.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("master", type=Path)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    restore(args.master, args.out)
