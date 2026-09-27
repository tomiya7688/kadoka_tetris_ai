#include "kadoka/tetris/runtime/observation.hpp"

namespace kadoka::tetris::runtime {

BoardObservation observe_board(const Board& board) {
    BoardObservation observation;
    observation.width = board.width();
    observation.height = board.visible_height();
    for (const Position cell : board.occupied_cells()) {
        if (cell.y >= board.hidden_rows()) {
            observation.locked_cells.push_back({cell.x, cell.y - board.hidden_rows()});
        }
    }
    return observation;
}

PlayerObservation observe_player(const GameState& game) {
    PlayerObservation observation;
    observation.board = observe_board(game.board());
    observation.hold_piece = game.hold();
    observation.next_pieces = game.next_pieces();
    if (game.game_over()) {
        return observation;
    }

    const ActivePiece& active = game.active();
    observation.current_piece = active.kind;
    for (const Offset cell : active.cells()) {
        const int x = active.x + cell.x;
        const int y = active.y + cell.y - game.board().hidden_rows();
        if (x >= 0 && x < observation.board.width && y >= 0 && y < observation.board.height) {
            observation.board.active_cells.push_back({x, y});
        }
    }
    return observation;
}

}  // namespace kadoka::tetris::runtime
