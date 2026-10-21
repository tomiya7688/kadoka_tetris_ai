#include "kadoka/tetris/active_piece.hpp"

#include <algorithm>

namespace kadoka::tetris {

std::array<Offset, 4> ActivePiece::cells() const {
    auto result = make_tetromino(kind).cells;
    // 負の回転数も、同じ向きを表す0から3の回転回数へそろえる。
    const int turns = ((rotation % 4) + 4) % 4;

    for (int turn = 0; turn < turns; ++turn) {
        for (Offset& cell : result) {
            const int old_x = cell.x;
            cell.x = -cell.y;
            cell.y = old_x;
        }

        // 回転で生じた負の座標を除き、各軸の最小値を0へそろえる。
        const int min_x = std::min_element(
            result.begin(), result.end(), [](const Offset& lhs, const Offset& rhs) {
                return lhs.x < rhs.x;
            })->x;
        const int min_y = std::min_element(
            result.begin(), result.end(), [](const Offset& lhs, const Offset& rhs) {
                return lhs.y < rhs.y;
            })->y;

        for (Offset& cell : result) {
            cell.x -= min_x;
            cell.y -= min_y;
        }
    }

    return result;
}

}  // namespace kadoka::tetris
