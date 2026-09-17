#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace kadoka::tetris {

class SevenBag {
public:
    explicit SevenBag(std::uint64_t seed = 0) noexcept : state_(seed) {}

    [[nodiscard]] PieceType next();

private:
    [[nodiscard]] std::uint64_t next_random() noexcept;
    [[nodiscard]] std::uint64_t bounded(std::uint64_t bound) noexcept;
    void refill() noexcept;

    std::uint64_t state_{};
    std::array<PieceType, 7> queue_{};
    std::size_t remaining_{};
};

}  // namespace kadoka::tetris
