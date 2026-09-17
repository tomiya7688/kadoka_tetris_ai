#include "kadoka/tetris/combat_rules.hpp"
#include "kadoka/tetris/game_state.hpp"

#include <cassert>
#include <vector>

using namespace kadoka::tetris;

int main() {
    {
        GameState a(1);
        GameState b(1);
        assert(a.active().kind == b.active().kind);
        assert(a.next_pieces() == b.next_pieces());
    }

    {
        GameState game(1);
        const PieceType first = game.active().kind;
        assert(game.move(1));
        assert(game.rotate());
        const int distance = game.hard_drop();
        assert(distance > 0);
        assert(!game.board().occupied_cells().empty());
        assert(game.pieces_locked() == 1);
        assert(game.last_lock_event().has_value());
        assert(game.last_lock_event()->lock_id == 1);
        assert(game.last_lock_event()->piece == first);
        assert(!game.hold_used());
    }

    {
        GameState game(2);
        const PieceType first = game.active().kind;
        assert(game.hold_piece());
        assert(game.hold().has_value());
        assert(*game.hold() == first);
        assert(game.hold_used());
        assert(!game.hold_piece());

        (void)game.hard_drop();
        assert(!game.hold_used());
        const PieceType before_swap = game.active().kind;
        assert(game.hold_piece());
        assert(game.active().kind == first);
        assert(game.hold().has_value());
        assert(*game.hold() == before_swap);
    }

    {
        GameState game(3, 4, 4, 0, 2);
        assert(game.next_pieces().size() == 2);
        const bool overflow = game.add_garbage({0, 1, 2, 3, 0});
        assert(overflow);
        assert(game.game_over());
    }

    {
        const auto occupied = [](int x, int y) {
            return (x == 0 && y == 0) ||
                   (x == 2 && y == 0) ||
                   (x == 0 && y == 2);
        };
        assert(is_t_spin_placement(
            PieceType::T,
            0,
            0,
            0,
            4,
            4,
            occupied,
            true));
        assert(!is_t_spin_placement(
            PieceType::T,
            0,
            0,
            0,
            4,
            4,
            occupied,
            false));
        assert(!is_t_spin_placement(
            PieceType::I,
            0,
            0,
            0,
            4,
            4,
            occupied,
            true));
    }

    return 0;
}
