from __future__ import annotations

from dataclasses import dataclass

from .ai_backend import AIBackend, AIProposal
from .command import Command
from .versus import VersusSession


@dataclass(frozen=True)
class AITurnResult:
    proposal: AIProposal | None
    commands: tuple[Command, ...]
    next_sequence: int
    skipped: bool = False


def run_ai_turn(
    session: VersusSession,
    backend: AIBackend,
    *,
    player: int,
    sequence_start: int,
) -> AITurnResult:
    """Ask one AI backend for a proposal and schedule validated semantic commands.

    The backend does not own authoritative state transition. All proposed actions
    are validated by Command before anything is submitted to the TickEngine.
    Validation is completed for the whole proposal before the first command is
    queued so a malformed proposal cannot be partially applied.
    """

    if player not in session.games:
        raise ValueError("unknown player")
    if not isinstance(sequence_start, int) or isinstance(sequence_start, bool) or sequence_start < 0:
        raise ValueError("sequence_start must be a nonnegative integer")

    game = session.games[player]
    if game.game_over:
        return AITurnResult(None, (), sequence_start, skipped=True)

    proposal = backend.decide(game)
    if not isinstance(proposal, AIProposal):
        raise TypeError("AI backend must return AIProposal")

    base_tick = session.engine.tick
    commands = tuple(
        Command(
            player=player,
            tick=base_tick + offset,
            sequence=sequence_start + offset,
            action=action,
        )
        for offset, action in enumerate(proposal.actions)
    )

    for command in commands:
        session.submit(command)

    return AITurnResult(
        proposal=proposal,
        commands=commands,
        next_sequence=sequence_start + len(commands),
    )
