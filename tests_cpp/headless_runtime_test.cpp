#include "kadoka/tetris/runtime/headless_runtime.hpp"

#include <cassert>
#include <stdexcept>
#include <vector>

using namespace kadoka::tetris;
using namespace kadoka::tetris::runtime;

int main() {
    {
        bool rejected = false;
        try { HeadlessRuntime runtime({}); }
        catch (const std::invalid_argument&) { rejected = true; }
        assert(rejected);
    }

    {
        HeadlessRuntime runtime({11, 29});
        const PlayerObservation observation = runtime.observe(0);
        assert(observation.active_piece.has_value());
        assert(observation.active_piece->kind == runtime.game(0).active().kind);
        assert(observation.hold_piece == runtime.game(0).hold());
        assert(observation.next_pieces == runtime.game(0).next_pieces());
        assert(observation.board.width == runtime.game(0).board().width());
        assert(observation.board.height == runtime.game(0).board().visible_height());

        const int player_zero_x = runtime.game(0).active().x;
        const int player_one_x = runtime.game(1).active().x;
        runtime.submit({0, 0, 1, SemanticAction::MoveLeft});
        runtime.submit({1, 0, 0, SemanticAction::MoveRight});
        runtime.submit({0, 0, 0, SemanticAction::MoveRight});
        const TickResult result = runtime.advance();
        assert(result.tick == 0);
        assert(result.commands_processed == 3);
        assert(runtime.current_tick() == 1);
        assert(runtime.game(0).active().x == player_zero_x);
        assert(runtime.game(1).active().x == player_one_x + 1);
    }

    {
        HeadlessRuntime runtime({11});
        bool out_of_range_rejected = false;
        try { (void)runtime.observe(1); }
        catch (const std::out_of_range&) { out_of_range_rejected = true; }
        assert(out_of_range_rejected);
    }

    {
        HeadlessRuntime runtime({7});
        runtime.submit({0, 0, 0, SemanticAction::MoveLeft});
        bool duplicate_rejected = false;
        try { runtime.submit({0, 0, 0, SemanticAction::MoveRight}); }
        catch (const std::invalid_argument&) { duplicate_rejected = true; }
        assert(duplicate_rejected);
        bool invalid_action_rejected = false;
        try { runtime.submit({0, 0, 1, static_cast<SemanticAction>(255)}); }
        catch (const std::invalid_argument&) { invalid_action_rejected = true; }
        assert(invalid_action_rejected);
        (void)runtime.advance();
        bool past_rejected = false;
        try { runtime.submit({0, 0, 2, SemanticAction::Hold}); }
        catch (const std::invalid_argument&) { past_rejected = true; }
        assert(past_rejected);
    }

    {
        HeadlessRuntime left({123});
        HeadlessRuntime right({123});
        left.submit({0, 0, 0, SemanticAction::RotateClockwise});
        right.submit({0, 0, 0, SemanticAction::RotateClockwise});
        (void)left.advance();
        (void)right.advance();
        assert(left.game(0).active().kind == right.game(0).active().kind);
        assert(left.game(0).active().rotation == right.game(0).active().rotation);
        assert(left.game(0).board().occupied_cells() == right.game(0).board().occupied_cells());
    }

    assert(semantic_action_name(SemanticAction::HardDrop) == "hard_drop");
    return 0;
}
