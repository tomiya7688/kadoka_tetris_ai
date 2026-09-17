#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <array>

namespace kadoka::tetris {

struct ActivePiece {
    PieceType kind{PieceType::I};
    int x{3};
    int y{0};
    int rotation{0};

    [[nodiscard]] std::array<Offset, 4> cells() const;
};

}  // namespace kadoka::tetris
