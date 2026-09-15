"""Persistent configuration for the visible-only standard CPU evaluator."""

import json
import math
from dataclasses import asdict, dataclass
from pathlib import Path

from .visible_board_evaluator import VisibleBoardWeights


STANDARD_CPU_CONFIG_FILENAME = "standard_cpu.json"
STANDARD_CPU_CONFIG_VERSION = 1
_WEIGHT_FIELDS = tuple(asdict(VisibleBoardWeights()))


@dataclass(frozen=True)
class StandardCpuConfig:
    weights: VisibleBoardWeights


def load_standard_cpu_config(config_dir: Path) -> StandardCpuConfig:
    path = ensure_standard_cpu_config(config_dir)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid standard CPU config JSON: {exc.msg}") from exc
    except OSError as exc:
        raise ValueError(f"failed to read standard CPU config: {exc}") from exc
    return _parse_config(data)


def ensure_standard_cpu_config(config_dir: Path) -> Path:
    config_dir.mkdir(parents=True, exist_ok=True)
    path = config_dir / STANDARD_CPU_CONFIG_FILENAME
    if not path.exists():
        _write_default_config(path)
    return path


def _parse_config(data: object) -> StandardCpuConfig:
    if not isinstance(data, dict):
        raise ValueError("standard CPU config must be an object")

    expected_keys = {"version", "weights"}
    _require_exact_fields(data, expected_keys, "standard CPU config")

    version = data["version"]
    if (
        not isinstance(version, int)
        or isinstance(version, bool)
        or version != STANDARD_CPU_CONFIG_VERSION
    ):
        raise ValueError(f"unsupported standard CPU config version: {version!r}")

    weights_data = data["weights"]
    if not isinstance(weights_data, dict):
        raise ValueError("standard CPU config weights must be an object")
    _require_exact_fields(weights_data, set(_WEIGHT_FIELDS), "standard CPU weights")

    parsed_weights = {}
    for name in _WEIGHT_FIELDS:
        value = weights_data[name]
        if not isinstance(value, (int, float)) or isinstance(value, bool):
            raise ValueError(f"standard CPU weight {name} must be a number")
        numeric = float(value)
        if not math.isfinite(numeric):
            raise ValueError(f"standard CPU weight {name} must be finite")
        parsed_weights[name] = numeric

    return StandardCpuConfig(weights=VisibleBoardWeights(**parsed_weights))


def _require_exact_fields(data: dict[object, object], expected: set[str], label: str) -> None:
    keys = set(data)
    unknown = keys - expected
    missing = expected - keys
    if unknown:
        names = ", ".join(sorted(str(name) for name in unknown))
        raise ValueError(f"unknown {label} fields: {names}")
    if missing:
        names = ", ".join(sorted(missing))
        raise ValueError(f"missing {label} fields: {names}")


def _write_default_config(path: Path) -> None:
    payload = {
        "version": STANDARD_CPU_CONFIG_VERSION,
        "weights": asdict(VisibleBoardWeights()),
    }
    try:
        path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ValueError(f"failed to write standard CPU config: {exc}") from exc
