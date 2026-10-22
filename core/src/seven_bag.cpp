#include "kadoka/tetris/seven_bag.hpp"

#include <limits>
#include <utility>

namespace kadoka::tetris {

PieceType SevenBag::next() {
    if (remaining_ == 0) {
        refill();
    }
    // 先頭から取り出す方式へ変えると、同じseedの既存ツモ順も変わる。
    --remaining_;
    return queue_[remaining_];
}

std::uint64_t SevenBag::next_random() noexcept {
    // 符号なし64bitの桁あふれを利用して状態を進める。
    state_ += 0x9E3779B97F4A7C15ULL;
    std::uint64_t z = state_;
    z = (z ^ (z >> 30U)) * 0xBF58476D1CE4E5B9ULL;
    z = (z ^ (z >> 27U)) * 0x94D049BB133111EBULL;
    return z ^ (z >> 31U);
}

std::uint64_t SevenBag::bounded(std::uint64_t bound) noexcept {
    if (bound <= 1) return 0;
    // 2^64個の値をboundで等分できない端数を、下端側から棄却する。
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

    // 未確定範囲から交換先を選び、各種類が1個ずつある状態を保つ。
    for (std::size_t index = queue_.size() - 1; index > 0; --index) {
        const std::size_t selected = static_cast<std::size_t>(bounded(index + 1));
        std::swap(queue_[index], queue_[selected]);
    }
    remaining_ = queue_.size();
}

}  // namespace kadoka::tetris
