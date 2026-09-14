"""Validated keyboard bindings shared by configurable input adapters."""

from collections.abc import Mapping


KEYBOARD_ACTIONS = frozenset(
    {
        "move_left",
        "move_right",
        "rotate_cw",
        "rotate_ccw",
        "soft_drop",
        "hard_drop",
        "hold",
    }
)

DEFAULT_ACTION_KEYS: dict[int, dict[str, str]] = {
    0: {
        "move_left": "left",
        "move_right": "right",
        "rotate_cw": "up",
        "rotate_ccw": "z",
        "soft_drop": "down",
        "hard_drop": "space",
        "hold": "c",
    },
    1: {
        "move_left": "a",
        "move_right": "d",
        "rotate_cw": "w",
        "rotate_ccw": "q",
        "soft_drop": "s",
        "hard_drop": "f",
        "hold": "e",
    },
}


class KeyboardBindings:
    """Resolve physical keyboard names to semantic actions per player."""

    def __init__(self, action_keys: Mapping[int, Mapping[str, str]]):
        self._action_keys = self._normalize(action_keys)
        self._key_actions = self._invert(self._action_keys)

    @classmethod
    def default(cls) -> "KeyboardBindings":
        return cls(DEFAULT_ACTION_KEYS)

    @property
    def players(self) -> tuple[int, ...]:
        return tuple(sorted(self._action_keys))

    def action_for_key(self, player: int, key_name: str) -> str | None:
        player_actions = self._key_actions.get(player)
        if player_actions is None:
            raise ValueError(f"unknown player: {player}")
        return player_actions.get(self._normalize_key(key_name))

    def action_keys_for_player(self, player: int) -> dict[str, str]:
        if player not in self._action_keys:
            raise ValueError(f"unknown player: {player}")
        return dict(self._action_keys[player])

    def _normalize(
        self,
        action_keys: Mapping[int, Mapping[str, str]],
    ) -> dict[int, dict[str, str]]:
        if not action_keys:
            raise ValueError("at least one player's keyboard bindings are required")

        normalized: dict[int, dict[str, str]] = {}
        globally_used_keys: dict[str, int] = {}

        for player, bindings in action_keys.items():
            if not isinstance(player, int) or isinstance(player, bool) or player < 0:
                raise ValueError("player ids must be nonnegative integers")
            if not isinstance(bindings, Mapping):
                raise ValueError(f"bindings for player {player} must be an object")

            actions = set(bindings)
            missing = KEYBOARD_ACTIONS - actions
            unknown = actions - KEYBOARD_ACTIONS
            if missing:
                names = ", ".join(sorted(missing))
                raise ValueError(f"player {player} is missing actions: {names}")
            if unknown:
                names = ", ".join(sorted(unknown))
                raise ValueError(f"player {player} has unknown actions: {names}")

            player_bindings: dict[str, str] = {}
            used_keys: set[str] = set()
            for action in sorted(KEYBOARD_ACTIONS):
                key_name = self._normalize_key(bindings[action])
                if key_name in used_keys:
                    raise ValueError(
                        f"player {player} assigns key {key_name!r} more than once"
                    )
                previous_player = globally_used_keys.get(key_name)
                if previous_player is not None:
                    raise ValueError(
                        f"key {key_name!r} is shared by players "
                        f"{previous_player} and {player}"
                    )
                used_keys.add(key_name)
                globally_used_keys[key_name] = player
                player_bindings[action] = key_name

            normalized[player] = player_bindings

        return normalized

    def _invert(
        self,
        action_keys: Mapping[int, Mapping[str, str]],
    ) -> dict[int, dict[str, str]]:
        return {
            player: {key_name: action for action, key_name in bindings.items()}
            for player, bindings in action_keys.items()
        }

    def _normalize_key(self, key_name: str) -> str:
        if not isinstance(key_name, str):
            raise ValueError("key names must be strings")
        normalized = key_name.strip().lower()
        if not normalized:
            raise ValueError("key names must not be empty")
        return normalized
