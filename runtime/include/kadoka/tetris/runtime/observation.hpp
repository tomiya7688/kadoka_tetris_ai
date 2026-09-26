#pragma once

#include "kadoka/tetris/game_state.hpp"

#include <optional>
#include <vector>

namespace kadoka::tetris::runtime {

struct BoardObservation {
    int width{};
    int height{};
    std::vector<Position> locked_cells;
    std::vector<Position> active_cells;
};

struct PlayerObservation {
    BoardObservation board;
    std::optional<PieceType> current_piece;
    std::optional<PieceType> hold_piece;
    std::vector<PieceType> next_pieces;
};

[[nodiscard]] BoardObservation observe_board(const Board& board);
[[nodiscard]] PlayerObservation observe_player(const GameState& game);

}  // namespace kadoka::tetris::runtime
