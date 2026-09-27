#include "kadoka/tetris/runtime/headless_runtime.hpp"

#include <algorithm>
#include <stdexcept>
#include <tuple>

namespace kadoka::tetris::runtime {

std::string_view semantic_action_name(SemanticAction action) noexcept {
    switch (action) {
        case SemanticAction::MoveLeft: return "move_left";
        case SemanticAction::MoveRight: return "move_right";
        case SemanticAction::RotateClockwise: return "rotate_cw";
        case SemanticAction::RotateCounterClockwise: return "rotate_ccw";
        case SemanticAction::SoftDrop: return "soft_drop";
        case SemanticAction::HardDrop: return "hard_drop";
        case SemanticAction::Hold: return "hold";
    }
    return {};
}

HeadlessRuntime::HeadlessRuntime(
    const std::vector<std::uint64_t>& seeds,
    int width,
    int visible_height,
    int hidden_rows,
    std::size_t next_count
) {
    if (seeds.empty()) {
        throw std::invalid_argument("runtime requires at least one player seed");
    }
    games_.reserve(seeds.size());
    for (const auto seed : seeds) {
        games_.emplace_back(seed, width, visible_height, hidden_rows, next_count);
    }
}

void HeadlessRuntime::submit(const SemanticCommand& command) {
    if (command.player >= games_.size()) {
        throw std::invalid_argument("command player is out of range");
    }
    if (command.tick < current_tick_) {
        throw std::invalid_argument("command tick is in the past");
    }
    if (semantic_action_name(command.action).empty()) {
        throw std::invalid_argument("command action is invalid");
    }

    auto& commands = pending_[command.tick];
    const auto duplicate = std::find_if(commands.begin(), commands.end(), [&](const auto& queued) {
        return queued.player == command.player && queued.sequence == command.sequence;
    });
    if (duplicate != commands.end()) {
        throw std::invalid_argument("command sequence is duplicated for this player and tick");
    }
    commands.push_back(command);
}

TickResult HeadlessRuntime::advance() {
    const auto found = pending_.find(current_tick_);
    std::size_t processed = 0;
    if (found != pending_.end()) {
        auto& commands = found->second;
        std::sort(commands.begin(), commands.end(), [](const auto& left, const auto& right) {
            return std::tie(left.player, left.sequence) < std::tie(right.player, right.sequence);
        });
        for (const auto& command : commands) {
            apply(command);
            ++processed;
        }
        pending_.erase(found);
    }

    const TickResult result{current_tick_, processed};
    ++current_tick_;
    return result;
}

const GameState& HeadlessRuntime::game(std::size_t player) const {
    if (player >= games_.size()) {
        throw std::out_of_range("player is out of range");
    }
    return games_[player];
}

void HeadlessRuntime::apply(const SemanticCommand& command) {
    auto& game = games_[command.player];
    switch (command.action) {
        case SemanticAction::MoveLeft: (void)game.move(-1); return;
        case SemanticAction::MoveRight: (void)game.move(1); return;
        case SemanticAction::RotateClockwise: (void)game.rotate(1); return;
        case SemanticAction::RotateCounterClockwise: (void)game.rotate(-1); return;
        case SemanticAction::SoftDrop: (void)game.move(0, 1); return;
        case SemanticAction::HardDrop: (void)game.hard_drop(); return;
        case SemanticAction::Hold: (void)game.hold_piece(); return;
    }
    throw std::invalid_argument("command action is invalid");
}

}  // namespace kadoka::tetris::runtime
