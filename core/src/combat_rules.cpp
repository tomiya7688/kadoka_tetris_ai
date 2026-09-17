#include "kadoka/tetris/combat_rules.hpp"

#include <array>

namespace kadoka::tetris {

bool is_t_spin_placement(
    PieceType piece,
    int rotation,
    int origin_x,
    int origin_y,
    int width,
    int height,
    const std::function<bool(int, int)>& occupied,
    bool last_rotation,
    bool top_out_of_bounds_occupied) {
    if (piece != PieceType::T || !last_rotation) {
        return false;
    }

    constexpr std::array<Offset, 4> pivots{{
        {1, 1},
        {0, 1},
        {1, 0},
        {1, 1},
    }};
    const int normalized_rotation = ((rotation % 4) + 4) % 4;
    const Offset pivot = pivots[static_cast<std::size_t>(normalized_rotation)];
    const int center_x = origin_x + pivot.x;
    const int center_y = origin_y + pivot.y;

    constexpr std::array<Offset, 4> corners{{
        {-1, -1},
        {1, -1},
        {-1, 1},
        {1, 1},
    }};

    int occupied_corners = 0;
    for (const Offset corner : corners) {
        const int x = center_x + corner.x;
        const int y = center_y + corner.y;
        if (x < 0 || x >= width || y >= height) {
            ++occupied_corners;
        } else if (y < 0) {
            occupied_corners += top_out_of_bounds_occupied ? 1 : 0;
        } else if (occupied(x, y)) {
            ++occupied_corners;
        }
    }
    return occupied_corners >= 3;
}

}  // namespace kadoka::tetris
