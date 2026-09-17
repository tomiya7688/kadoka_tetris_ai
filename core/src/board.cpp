#include "kadoka/tetris/board.hpp"

#include <algorithm>
#include <stdexcept>

namespace kadoka::tetris {

Board::Board(int width, int visible_height, int hidden_rows)
    : width_(width),
      visible_height_(visible_height),
      hidden_rows_(hidden_rows),
      height_(visible_height + hidden_rows) {
    if (width <= 0 || visible_height <= 0 || hidden_rows < 0) {
        throw std::invalid_argument("invalid board dimensions");
    }
    cells_.assign(static_cast<std::size_t>(width_ * height_), 0);
}

bool Board::occupied(int x, int y) const {
    if (!in_bounds(x, y)) {
        throw std::out_of_range("board coordinate is out of range");
    }
    return cells_[index(x, y)] != 0;
}

bool Board::can_place(const Tetromino& piece, Position origin) const noexcept {
    for (const Offset cell : piece.cells) {
        const int x = origin.x + cell.x;
        const int y = origin.y + cell.y;
        if (!in_bounds(x, y) || cells_[index(x, y)] != 0) {
            return false;
        }
    }
    return true;
}

void Board::lock(const Tetromino& piece, Position origin) {
    if (!can_place(piece, origin)) {
        throw std::invalid_argument("piece cannot be locked");
    }
    for (const Offset cell : piece.cells) {
        cells_[index(origin.x + cell.x, origin.y + cell.y)] = 1;
    }
}

int Board::clear_full_rows() {
    std::vector<std::uint8_t> kept;
    kept.reserve(cells_.size());
    int cleared = 0;

    for (int y = 0; y < height_; ++y) {
        bool full = true;
        for (int x = 0; x < width_; ++x) {
            if (cells_[index(x, y)] == 0) {
                full = false;
                break;
            }
        }

        if (full) {
            ++cleared;
            continue;
        }

        for (int x = 0; x < width_; ++x) {
            kept.push_back(cells_[index(x, y)]);
        }
    }

    if (cleared == 0) return 0;

    cells_.assign(static_cast<std::size_t>(width_ * height_), 0);
    const std::size_t destination = static_cast<std::size_t>(cleared * width_);
    std::copy(kept.begin(), kept.end(), cells_.begin() + static_cast<std::ptrdiff_t>(destination));
    return cleared;
}

bool Board::add_garbage(const std::vector<int>& hole_columns) {
    for (const int hole : hole_columns) {
        if (hole < 0 || hole >= width_) {
            throw std::invalid_argument("garbage hole must be a valid column");
        }
    }
    if (hole_columns.empty()) return false;

    const int count = static_cast<int>(hole_columns.size());
    const int dropped_rows = std::min(count, height_);
    bool overflow = count > height_;
    for (int y = 0; y < dropped_rows && !overflow; ++y) {
        for (int x = 0; x < width_; ++x) {
            if (cells_[index(x, y)] != 0) {
                overflow = true;
                break;
            }
        }
    }

    std::vector<std::uint8_t> next(static_cast<std::size_t>(width_ * height_), 0);

    const int kept_rows = std::max(0, height_ - count);
    if (kept_rows > 0) {
        for (int y = 0; y < kept_rows; ++y) {
            for (int x = 0; x < width_; ++x) {
                next[static_cast<std::size_t>(y * width_ + x)] =
                    cells_[index(x, y + count)];
            }
        }
    }

    const int visible_count = std::min(count, height_);
    const int hole_start = count - visible_count;
    const int garbage_start_y = height_ - visible_count;
    for (int row = 0; row < visible_count; ++row) {
        const int hole = hole_columns[static_cast<std::size_t>(hole_start + row)];
        const int y = garbage_start_y + row;
        for (int x = 0; x < width_; ++x) {
            next[static_cast<std::size_t>(y * width_ + x)] = static_cast<std::uint8_t>(x != hole);
        }
    }

    cells_ = std::move(next);
    return overflow;
}

std::vector<Position> Board::occupied_cells() const {
    std::vector<Position> result;
    for (int y = 0; y < height_; ++y) {
        for (int x = 0; x < width_; ++x) {
            if (cells_[index(x, y)] != 0) {
                result.push_back({x, y});
            }
        }
    }
    return result;
}

bool Board::in_bounds(int x, int y) const noexcept {
    return x >= 0 && x < width_ && y >= 0 && y < height_;
}

std::size_t Board::index(int x, int y) const noexcept {
    return static_cast<std::size_t>(y * width_ + x);
}

}  // namespace kadoka::tetris
