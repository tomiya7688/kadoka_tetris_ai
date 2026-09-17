#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace kadoka::tetris {

class Board {
public:
    explicit Board(int width = 10, int visible_height = 20, int hidden_rows = 2);

    [[nodiscard]] int width() const noexcept { return width_; }
    [[nodiscard]] int visible_height() const noexcept { return visible_height_; }
    [[nodiscard]] int hidden_rows() const noexcept { return hidden_rows_; }
    [[nodiscard]] int height() const noexcept { return height_; }

    [[nodiscard]] bool occupied(int x, int y) const;
    [[nodiscard]] bool can_place(const Tetromino& piece, Position origin) const noexcept;

    void lock(const Tetromino& piece, Position origin);
    [[nodiscard]] int clear_full_rows();
    [[nodiscard]] bool add_garbage(const std::vector<int>& hole_columns);

    [[nodiscard]] std::vector<Position> occupied_cells() const;

private:
    [[nodiscard]] bool in_bounds(int x, int y) const noexcept;
    [[nodiscard]] std::size_t index(int x, int y) const noexcept;

    int width_{};
    int visible_height_{};
    int hidden_rows_{};
    int height_{};
    std::vector<std::uint8_t> cells_;
};

}  // namespace kadoka::tetris
