from __future__ import annotations

import argparse
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOTS = {
    "core",
    "runtime",
    "benchmarks_cpp",
    "tests_cpp",
    "src",
    "tests",
    "tools",
}
CPP_SUFFIXES = {".c", ".h", ".cc", ".cpp", ".hpp"}


# {
#   責務: [changed_paths: 指定した二つのcommit間で追加・変更されたファイル名を取得する]
#   処理: [1: refをcommit SHAへ解決する 2: NUL区切りの差分名を取得する]
#   引数: [base: 比較元 head: 比較先]
#   戻り値: [削除済みファイルを除く相対path一覧]
# }
def changed_paths(base: str, head: str) -> list[str]:
    # refを確定し、git diffのオプションとして解釈されることを防ぐ。
    commits = [
        subprocess.check_output(
            ["git", "rev-parse", "--verify", "--end-of-options", f"{ref}^{{commit}}"],
            cwd=ROOT,
        )
        .decode()
        .strip()
        for ref in (base, head)
    ]
    names = subprocess.check_output(
        ["git", "diff", "--name-only", "-z", "--diff-filter=ACMR", *commits, "--"],
        cwd=ROOT,
    )
    return names.decode("utf-8").rstrip("\0").split("\0") if names else []


# {
#   責務: [source_paths: 指定されたファイルを整形可能なsourceだけへ絞る]
#   処理: [1: 許可したsource rootと拡張子を確認する 2: 外部pathとlinkを拒否する]
#   引数: [names: repository相対のファイル名一覧]
#   戻り値: [重複を除いた整形対象の相対path一覧]
# }
def source_paths(names: list[str]) -> list[str]:
    selected = set()
    for name in names:
        path = Path(name)
        if path.is_absolute() or ".." in path.parts:
            raise ValueError(f"Repository-relative path required: {name}")
        if not path.parts or path.parts[0] not in SOURCE_ROOTS:
            continue
        if path.suffix not in CPP_SUFFIXES | {".py"}:
            continue
        # 許可root内でも生成物・vendor・cache・linkを再帰的に辿らない。
        if any(
            part.startswith(".") or part in {"vendor", "generated", "__pycache__"}
            for part in path.parts
        ):
            continue
        candidate = ROOT / path
        if candidate.resolve() != candidate.absolute():
            raise ValueError(f"Links are not formatting targets: {name}")
        if not candidate.is_file():
            raise ValueError(f"Source file not found: {name}")
        selected.add(path.as_posix())
    return sorted(selected)


# {
#   責務: [format_sources: 管理済みの固定版formatterで指定sourceを整形または検査する]
#   処理: [1: 言語別に対象を分ける 2: 依存版を照合する 3: formatterを実行する]
#   引数: [paths: 検証済み相対path一覧 check: 書換えなしで検査する場合はTrue]
#   戻り値: [formatter失敗時は例外、成功時はなし]
# }
def format_sources(paths: list[str], check: bool) -> None:
    pins = dict(
        line.split("==")
        for line in (ROOT / "requirements-ci.txt")
        .read_text(encoding="utf-8")
        .splitlines()
        if "==" in line
    )
    commands = [
        (
            "ruff",
            [sys.executable, "-m", "ruff", "format", *(["--check"] if check else [])],
            {".py"},
        ),
        (
            "clang-format",
            [
                sys.executable,
                "-c",
                "import clang_format; clang_format.clang_format()",
                "--style=file",
                "--fallback-style=none",
                *(["--dry-run", "--Werror"] if check else ["-i"]),
            ],
            CPP_SUFFIXES,
        ),
    ]
    for package, command, suffixes in commands:
        targets = [path for path in paths if Path(path).suffix in suffixes]
        if targets:
            if version(package) != pins[package]:
                raise ValueError(
                    f"Install requirements-ci.txt: {package}=={pins[package]} required"
                )
            # 明示したファイルだけを渡し、ディレクトリ全体の整形を避ける。
            subprocess.run([*command, "--", *targets], cwd=ROOT, check=True)


# {
#   責務: [main: 対象を明示したformat/checkコマンドを提供する]
#   処理: [1: 引数を読む 2: 対象を確定する 3: 整形を実行し結果を返す]
#   引数: [コマンドラインからファイル一覧、--check、または--baseと--headを受け取る]
#   戻り値: [成功時0、入力・実行失敗時1]
# }
def main() -> int:
    parser = argparse.ArgumentParser(
        description="Format only selected Python/C++ source files."
    )
    parser.add_argument("files", nargs="*")
    parser.add_argument("--check", action="store_true")
    parser.add_argument("--base")
    parser.add_argument("--head", default="HEAD")
    args = parser.parse_args()
    if bool(args.files) == bool(args.base):
        parser.error("Specify files OR --base REF (never the whole repository).")
    try:
        names = changed_paths(args.base, args.head) if args.base else args.files
        paths = source_paths(names)
        format_sources(paths, args.check)
        print(
            f"Format {'check' if args.check else 'write'}: {len(paths)} source file(s)"
        )
        return 0
    except (
        OSError,
        ValueError,
        PackageNotFoundError,
        subprocess.SubprocessError,
    ) as error:
        print(f"Format failed: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
