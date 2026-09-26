#include "kadoka/tetris/runtime/observation.hpp"

#include <algorithm>
#include <cassert>
#include <vector>

using namespace kadoka::tetris;
using namespace kadoka::tetris::runtime;

int main() {
    {
        Board board(4, 3, 2);
        board.lock(make_tetromino(PieceType::O), {0, 0});
        board.lock(make_tetromino(PieceType::O), {0, 2});
        const BoardObservation observation = observe_board(board);
        assert(observation.width == 4);
        assert(observation.height == 3);
        assert(observation.locked_cells.size() == 4);
        assert(std::all_of(
            observation.locked_cells.begin(), observation.locked_cells.end(),
            [](Position cell) { return cell.y == 0 || cell.y == 1; }));
    }

    {
        GameState game(27, 10, 20, 2, 3);
        PlayerObservation observation = observe_player(game);
        assert(observation.current_piece == game.active().kind);
        assert(observation.hold_piece == game.hold());
        assert(observation.next_pieces == game.next_pieces());
        assert(observation.board.height == 20);
        assert(observation.board.active_cells.empty());

        assert(game.move(0, 3));
        observation = observe_player(game);
        assert(!observation.board.active_cells.empty());
        assert(std::all_of(
            observation.board.active_cells.begin(), observation.board.active_cells.end(),
            [](Position cell) { return cell.y >= 0 && cell.y < 20; }));
    }

    return 0;
}
