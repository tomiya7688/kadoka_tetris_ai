#pragma once

#include "kadoka/tetris/runtime/observation.hpp"

#include <cstddef>
#include <cstdint>
#include <map>
#include <string_view>
#include <vector>

namespace kadoka::tetris::runtime {

enum class SemanticAction : std::uint8_t {
    MoveLeft,
    MoveRight,
    RotateClockwise,
    RotateCounterClockwise,
    SoftDrop,
    HardDrop,
    Hold,
};

struct SemanticCommand {
    std::size_t player{};
    std::uint64_t tick{};
    std::uint64_t sequence{};
    SemanticAction action{};
};

struct PlayerProposal {
    std::size_t player{};
    std::uint64_t first_sequence{};
    std::vector<SemanticAction> actions;
};

struct TickResult {
    std::uint64_t tick{};
    std::size_t commands_processed{};
};

[[nodiscard]] std::string_view semantic_action_name(SemanticAction action) noexcept;

// Deterministic headless command boundary. GameState remains the sole owner of
// each player's canonical state; commands are ordered by player then sequence.
class HeadlessRuntime {
public:
    explicit HeadlessRuntime(
        const std::vector<std::uint64_t>& seeds,
        int width = 10,
        int visible_height = 20,
        int hidden_rows = 2,
        std::size_t next_count = 5);

    void submit(const SemanticCommand& command);
    // Validate every action before queueing any of them. Sequence numbers are
    // assigned consecutively from first_sequence.
    void submit_proposal(
        std::size_t player,
        std::uint64_t tick,
        std::uint64_t first_sequence,
        const std::vector<SemanticAction>& actions);
    // Validate every proposal and sequence as one transaction before queueing.
    void submit_proposals(std::uint64_t tick, const std::vector<PlayerProposal>& proposals);
    [[nodiscard]] TickResult advance();
    [[nodiscard]] std::uint64_t current_tick() const noexcept { return current_tick_; }
    [[nodiscard]] std::size_t player_count() const noexcept { return games_.size(); }
    [[nodiscard]] const GameState& game(std::size_t player) const;
    [[nodiscard]] PlayerObservation observe(std::size_t player) const;

private:
    void apply(const SemanticCommand& command);

    std::vector<GameState> games_;
    std::map<std::uint64_t, std::vector<SemanticCommand>> pending_;
    std::uint64_t current_tick_{};
};

}  // namespace kadoka::tetris::runtime
