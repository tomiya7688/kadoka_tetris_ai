from __future__ import annotations

import ast
import sys
from dataclasses import dataclass
from pathlib import Path

CORE_FORBIDDEN = (
    "pygame",
    "tkinter",
    "pathlib",
    "tetris.ai",
    "tetris.application",
    "tetris.adapters",
    "tetris.benchmark",
    "tetris.cpu",
    "tetris.observation",
)
GAMEPLAY_FORBIDDEN = ("tetris.benchmark",)


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    code: str
    message: str


def imported_names(node: ast.AST) -> list[str]:
    if isinstance(node, ast.Import):
        return [alias.name for alias in node.names]
    if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
        return [node.module]
    return []


def scan_file(root: Path, path: Path, forbidden: tuple[str, ...], code: str) -> list[Finding]:
    rel = path.relative_to(root).as_posix()
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=rel)
    except (OSError, SyntaxError) as exc:
        line = getattr(exc, "lineno", 1) or 1
        return [Finding(rel, line, "KT001", f"cannot parse Python source: {exc}")]

    findings: list[Finding] = []
    for node in ast.walk(tree):
        for name in imported_names(node):
            if any(name == item or name.startswith(item + ".") for item in forbidden):
                findings.append(
                    Finding(rel, getattr(node, "lineno", 1), code, f"forbidden dependency: {name}")
                )
    return findings


def scan_tree(root: Path, relative: str, forbidden: tuple[str, ...], code: str) -> list[Finding]:
    base = root / relative
    if not base.exists():
        return []
    findings: list[Finding] = []
    for path in sorted(base.rglob("*.py")):
        findings.extend(scan_file(root, path, forbidden, code))
    return findings


def main() -> int:
    root = Path(sys.argv[1] if len(sys.argv) > 1 else ".").resolve()
    if not (root / "src" / "tetris").exists():
        print("KT000 src/tetris not found")
        return 2

    findings = scan_tree(root, "src/tetris/core", CORE_FORBIDDEN, "KT101")
    findings += scan_tree(root, "src/tetris/application", GAMEPLAY_FORBIDDEN, "KT102")
    findings += scan_tree(root, "src/tetris/adapters", GAMEPLAY_FORBIDDEN, "KT102")
    findings.sort(key=lambda item: (item.path, item.line, item.code))

    for item in findings:
        print(f"{item.path}:{item.line} {item.code} {item.message}")

    if findings:
        print(f"Kadoka Tetris check: {len(findings)} error(s)")
        return 1
    print("Kadoka Tetris check: OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
