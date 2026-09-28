#pragma once

#include "kadoka/tetris/game_state.hpp"

#include <cstdint>
#include <optional>
#include <vector>

namespace kadoka::tetris::runtime {

struct BoardObservation {
    int width{};
    int height{};
    std::vector<Position> locked_cells;
    std::vector<Position> active_cells;
};

struct ActivePieceObservation {
    PieceType kind{};
    int x{};
    int y{};
    int rotation{};
};

struct PlayerObservation {
    BoardObservation board;
    std::optional<ActivePieceObservation> active_piece;
    std::optional<PieceType> hold_piece;
    bool hold_used{};
    std::vector<PieceType> next_pieces;
    bool game_over{};
    int lines{};
    int combo{};
    bool back_to_back_active{};
    std::uint64_t pieces_locked{};
};

[[nodiscard]] BoardObservation observe_board(const Board& board);
[[nodiscard]] PlayerObservation observe_player(const GameState& game);

}  // namespace kadoka::tetris::runtime
