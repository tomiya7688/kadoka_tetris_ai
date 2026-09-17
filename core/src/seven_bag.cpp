#include "kadoka/tetris/seven_bag.hpp"

#include <limits>
#include <utility>

namespace kadoka::tetris {

PieceType SevenBag::next() {
    if (remaining_ == 0) {
        refill();
    }
    --remaining_;
    return queue_[remaining_];
}

std::uint64_t SevenBag::next_random() noexcept {
    state_ += 0x9E3779B97F4A7C15ULL;
    std::uint64_t z = state_;
    z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31U);
}

std::uint64_t SevenBag::bounded(std::uint64_t bound) noexcept {
    if (bound <= 1) return 0;
    const std::uint64_t threshold = (std::numeric_limits<std::uint64_t>::max() - bound + 1) % bound;
    while (true) {
        const std::uint64_t value = next_random();
        if (value >= threshold) return value % bound;
    }
}

void SevenBag::refill() noexcept {
    queue_ = {
        PieceType::I,
        PieceType::O,
        PieceType::T,
        PieceType::S,
        PieceType::Z,
        PieceType::J,
        PieceType::L,
    };

    for (std::size_t index = queue_.size() - 1; index > 0; --index) {
        const std::size_t selected = static_cast<std::size_t>(bounded(index + 1));
        std::swap(queue_[index], queue_[selected]);
    }
    remaining_ = queue_.size();
}

}  // namespace kadoka::tetris
