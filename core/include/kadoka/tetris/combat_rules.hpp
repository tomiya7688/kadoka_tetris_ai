#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <functional>

namespace kadoka::tetris {

[[nodiscard]] bool is_t_spin_placement(
    PieceType piece,
    int rotation,
    int origin_x,
    int origin_y,
    int width,
    int height,
    const std::function<bool(int, int)>& occupied,
    bool last_rotation,
    bool top_out_of_bounds_occupied = true);

}  // namespace kadoka::tetris
