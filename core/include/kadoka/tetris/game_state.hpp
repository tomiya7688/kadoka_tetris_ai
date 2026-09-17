#pragma once

#include "kadoka/tetris/active_piece.hpp"
#include "kadoka/tetris/board.hpp"
#include "kadoka/tetris/lock_event.hpp"
#include "kadoka/tetris/seven_bag.hpp"

#include <cstddef>
#include <cstdint>
#include <optional>
#include <vector>

namespace kadoka::tetris {

class GameState {
public:
    explicit GameState(
        std::uint64_t seed = 0,
        int width = 10,
        int visible_height = 20,
        int hidden_rows = 2,
        std::size_t next_count = 5);

    [[nodiscard]] const Board& board() const noexcept { return board_; }
    [[nodiscard]] const ActivePiece& active() const noexcept { return active_; }
    [[nodiscard]] std::optional<PieceType> hold() const noexcept { return hold_; }
    [[nodiscard]] bool hold_used() const noexcept { return hold_used_; }
    [[nodiscard]] bool game_over() const noexcept { return game_over_; }
    [[nodiscard]] int lines() const noexcept { return lines_; }
    [[nodiscard]] int combo() const noexcept { return combo_; }
    [[nodiscard]] bool back_to_back_active() const noexcept { return back_to_back_active_; }
    [[nodiscard]] std::uint64_t pieces_locked() const noexcept { return pieces_locked_; }
    [[nodiscard]] const std::optional<LockEvent>& last_lock_event() const noexcept {
        return last_lock_event_;
    }
    [[nodiscard]] const std::vector<PieceType>& next_pieces() const noexcept {
        return next_queue_;
    }

    bool move(int dx, int dy = 0);
    bool rotate(int direction = 1);
    [[nodiscard]] int hard_drop();
    [[nodiscard]] LockEvent lock();
    [[nodiscard]] bool add_garbage(const std::vector<int>& hole_columns);
    bool hold_piece();

private:
    void spawn();
    [[nodiscard]] bool can_place(const ActivePiece& piece) const noexcept;
    [[nodiscard]] bool is_t_spin(const ActivePiece& piece) const;
    [[nodiscard]] static Tetromino as_tetromino(const ActivePiece& piece);

    Board board_;
    SevenBag bag_;
    std::size_t next_count_{};
    std::vector<PieceType> next_queue_;
    ActivePiece active_{};
    std::optional<PieceType> hold_;
    bool hold_used_{};
    bool game_over_{};
    int lines_{};
    int combo_{};
    bool back_to_back_active_{};
    std::uint64_t pieces_locked_{};
    std::optional<LockEvent> last_lock_event_;
    bool last_rotation_successful_{};
};

}  // namespace kadoka::tetris
