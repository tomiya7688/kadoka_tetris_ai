#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <cstdint>

namespace kadoka::tetris {

struct LockEvent {
    std::uint64_t lock_id{};
    PieceType piece{PieceType::I};
    int lines{};
    bool t_spin{};
    int combo{};
    bool back_to_back{};
    bool perfect_clear{};

    [[nodiscard]] constexpr bool difficult_clear() const noexcept {
        return lines == 4 || (t_spin && lines > 0);
    }
};

}  // namespace kadoka::tetris
