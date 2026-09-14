"""Backward-compatible default keyboard lookup."""

from .keyboard_bindings import KeyboardBindings


_DEFAULT_BINDINGS = KeyboardBindings.default()
KEY_ACTIONS = {
    key_name: action
    for action, key_name in _DEFAULT_BINDINGS.action_keys_for_player(0).items()
}


def action_for_key(name: str) -> str | None:
    return _DEFAULT_BINDINGS.action_for_key(0, name)
