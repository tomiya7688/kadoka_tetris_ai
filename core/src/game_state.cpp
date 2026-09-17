#include "kadoka/tetris/game_state.hpp"

#include "kadoka/tetris/combat_rules.hpp"

#include <utility>

namespace kadoka::tetris {

GameState::GameState(
    std::uint64_t seed,
    int width,
    int visible_height,
    int hidden_rows,
    std::size_t next_count)
    : board_(width, visible_height, hidden_rows),
      bag_(seed),
      next_count_(next_count) {
    next_queue_.reserve(next_count_);
    for (std::size_t i = 0; i < next_count_; ++i) {
        next_queue_.push_back(bag_.next());
    }
    spawn();
}

bool GameState::move(int dx, int dy) {
    ActivePiece candidate = active_;
    candidate.x += dx;
    candidate.y += dy;
    if (!can_place(candidate)) {
        return false;
    }

    active_ = candidate;
    if (dx != 0) {
        last_rotation_successful_ = false;
    }
    return true;
}

bool GameState::rotate(int direction) {
    ActivePiece candidate = active_;
    candidate.rotation += direction;
    if (can_place(candidate)) {
        active_ = candidate;
        last_rotation_successful_ = true;
        return true;
    }

    for (const int dx : {-1, 1, -2, 2}) {
        candidate.x = active_.x + dx;
        if (can_place(candidate)) {
            active_ = candidate;
            last_rotation_successful_ = true;
            return true;
        }
    }
    return false;
}

int GameState::hard_drop() {
    int distance = 0;
    while (move(0, 1)) {
        ++distance;
    }
    (void)lock();
    return distance;
}

LockEvent GameState::lock() {
    const ActivePiece locked_piece = active_;
    const bool t_spin = is_t_spin(locked_piece);

    board_.lock(as_tetromino(locked_piece), {locked_piece.x, locked_piece.y});
    const int cleared_lines = board_.clear_full_rows();
    lines_ += cleared_lines;
    ++pieces_locked_;

    if (cleared_lines > 0) {
        ++combo_;
    } else {
        combo_ = 0;
    }

    const bool difficult_clear = cleared_lines == 4 || (t_spin && cleared_lines > 0);
    const bool back_to_back = difficult_clear && back_to_back_active_;
    if (difficult_clear) {
        back_to_back_active_ = true;
    } else if (cleared_lines > 0) {
        back_to_back_active_ = false;
    }

    const bool perfect_clear = cleared_lines > 0 && board_.occupied_cells().empty();
    LockEvent event{
        pieces_locked_,
        locked_piece.kind,
        cleared_lines,
        t_spin,
        combo_,
        back_to_back,
        perfect_clear,
    };
    last_lock_event_ = event;

    hold_used_ = false;
    spawn();
    return event;
}

bool GameState::add_garbage(const std::vector<int>& hole_columns) {
    const bool overflow = board_.add_garbage(hole_columns);
    last_rotation_successful_ = false;
    if (overflow || !can_place(active_)) {
        game_over_ = true;
    }
    return overflow;
}

bool GameState::hold_piece() {
    if (hold_used_) {
        return false;
    }

    const std::optional<PieceType> previous_hold = hold_;
    hold_ = active_.kind;
    hold_used_ = true;
    last_rotation_successful_ = false;

    if (!previous_hold.has_value()) {
        spawn();
    } else {
        active_ = ActivePiece{
            *previous_hold,
            (board_.width() - 4) / 2,
            0,
            0,
        };
    }

    if (!can_place(active_)) {
        game_over_ = true;
    }
    return true;
}

void GameState::spawn() {
    PieceType kind{};
    if (!next_queue_.empty()) {
        kind = next_queue_.front();
        next_queue_.erase(next_queue_.begin());
        next_queue_.push_back(bag_.next());
    } else {
        kind = bag_.next();
    }

    active_ = ActivePiece{
        kind,
        (board_.width() - 4) / 2,
        0,
        0,
    };
    last_rotation_successful_ = false;
    if (!can_place(active_)) {
        game_over_ = true;
    }
}

bool GameState::can_place(const ActivePiece& piece) const noexcept {
    return board_.can_place(as_tetromino(piece), {piece.x, piece.y});
}

bool GameState::is_t_spin(const ActivePiece& piece) const {
    return is_t_spin_placement(
        piece.kind,
        piece.rotation,
        piece.x,
        piece.y,
        board_.width(),
        board_.height(),
        [this](int x, int y) { return board_.occupied(x, y); },
        last_rotation_successful_);
}

Tetromino GameState::as_tetromino(const ActivePiece& piece) {
    return Tetromino{piece.kind, piece.cells()};
}

}  // namespace kadoka::tetris
