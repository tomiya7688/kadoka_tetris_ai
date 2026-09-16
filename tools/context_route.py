from __future__ import annotations

import sys

ROUTES = {
    "core": ("src/tetris/core", "tests/test_core.py + tests/test_game_state.py", "docs/context-routing.md#core"),
    "commands-runtime": ("src/tetris/application + adapters", "tests/test_commands.py + tests/test_adapters.py", "docs/context-routing.md#commands-runtime"),
    "ai-cpu": ("src/tetris/ai + cpu", "tests/test_ai*.py + tests/test_cpu*.py", "docs/context-routing.md#ai-cpu"),
    "combat": ("core/application combat code", "tests/test_attack.py + test_combat_events.py + test_garbage.py", "docs/context-routing.md#combat"),
    "observation": ("src/tetris/observation", "observation/AI tests", "docs/対戦UIと可視Observation.md"),
    "benchmark": ("src/tetris/benchmark + cpu", "tests/test_cpu_benchmark*.py", "docs/CPUベンチマーク.md"),
    "distribution": ("build.bat + tools/distribution + runtime_paths.py", "unit tests + distribution smoke", ".github/workflows/windows-build.yml"),
    "build-policy": (".github/workflows + pyproject.toml + checker", "checker + compileall + ruff + unittest", "docs/コーディングルール.md"),
}


def main() -> int:
    if len(sys.argv) != 2 or sys.argv[1] in {"-h", "--help"}:
        print("usage: python tools/context_route.py <route|--list>")
        return 0
    if sys.argv[1] == "--list":
        for name in ROUTES:
            print(name)
        return 0
    route = ROUTES.get(sys.argv[1])
    if route is None:
        print(f"unknown route: {sys.argv[1]}")
        return 2
    source, tests, docs = route
    print(f"route={sys.argv[1]}")
    print(f"source={source}")
    print(f"tests={tests}")
    print(f"docs={docs}")
    print("stop=when target contract and acceptance evidence are clear")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
