#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace kadoka::tetris {

// {
//   責務: [Board: 盤面寸法と占有セルを保持し、配置・固定・行消去・garbage反映を提供する]
//   フィールド: [width_: 盤面の列数 visible_height_: 表示領域の行数 hidden_rows_: 表示領域より上の隠し行数 height_: 隠し行を含む総行数 cells_: 行優先で保持する占有セル]
//   処理: [盤面座標を検証し、Tetrominoの配置可能性を判定してセル状態を更新する]
// }
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
