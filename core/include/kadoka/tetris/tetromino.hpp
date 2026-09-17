#pragma once

#include <array>
#include <cstdint>

namespace kadoka::tetris {

enum class PieceType : std::uint8_t {
    I,
    O,
    T,
    S,
    Z,
    J,
    L,
};

struct Offset {
    int x{};
    int y{};

    friend constexpr bool operator==(Offset, Offset) = default;
};

struct Position {
    int x{};
    int y{};

    friend constexpr bool operator==(Position, Position) = default;
};

struct Tetromino {
    PieceType kind{PieceType::I};
    std::array<Offset, 4> cells{};
};

[[nodiscard]] Tetromino make_tetromino(PieceType kind);

}  // namespace kadoka::tetris
