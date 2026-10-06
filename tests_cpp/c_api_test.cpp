#include "kadoka/tetris/runtime/c_api.h"
#include "kadoka/tetris/runtime/headless_runtime.hpp"

#include <algorithm>
#include <memory>
#include <iostream>
#include <source_location>
#include <stdexcept>
#include <string>

using namespace kadoka::tetris::runtime;

namespace {

void require(bool condition, std::source_location location = std::source_location::current()) {
    if (!condition) { throw std::runtime_error("C ABI contract check failed at line " + std::to_string(location.line())); }
}

using Owner = std::unique_ptr<kt_runtime, decltype(&kt_destroy)>;

Owner create(uint64_t seed) {
    kt_runtime* pointer = nullptr;
    require(kt_create(&seed, 1, &pointer) == KT_OK);
    return Owner(pointer, kt_destroy);
}

kt_observation observe(const Owner& owner) {
    kt_observation result{};
    require(kt_observe(owner.get(), 0, &result, sizeof(result)) == KT_OK);
    return result;
}

void check_snapshot(const kt_observation& actual, const PlayerObservation& expected) {
    require(actual.pieces_locked == expected.pieces_locked);
    require(actual.game_over == static_cast<uint32_t>(expected.game_over));
    require(actual.lines == expected.lines && actual.combo == expected.combo);
    require(actual.back_to_back_active == static_cast<uint32_t>(expected.back_to_back_active));
    require(actual.hold_used == static_cast<uint32_t>(expected.hold_used));
    require(actual.hold_kind == (expected.hold_piece ? static_cast<int32_t>(*expected.hold_piece) : -1));
    require(actual.active_kind == (expected.active_piece ? static_cast<int32_t>(expected.active_piece->kind) : -1));
    if (expected.active_piece) {
        require(actual.active_x == expected.active_piece->x && actual.active_y == expected.active_piece->y);
        require(actual.active_rotation == expected.active_piece->rotation);
    }
    uint8_t locked[200]{};
    uint8_t active[200]{};
    for (const auto cell : expected.board.locked_cells) { locked[cell.y * 10 + cell.x] = 1; }
    for (const auto cell : expected.board.active_cells) { active[cell.y * 10 + cell.x] = 1; }
    require(std::equal(locked, locked + 200, actual.locked_cells));
    require(std::equal(active, active + 200, actual.active_cells));
    for (uint32_t index = 0; index < 5; ++index) {
        require(actual.next_pieces[index] == static_cast<int32_t>(expected.next_pieces[index]));
    }
}

void check_invalid_inputs() {
    kt_runtime* pointer = nullptr;
    const uint64_t seed = 11;
    require(kt_create(&seed, 0, &pointer) == KT_INVALID_ARGUMENT && pointer == nullptr);
    require(kt_create(&seed, 65, &pointer) == KT_INVALID_ARGUMENT);
    require(kt_create(nullptr, 1, &pointer) == KT_INVALID_ARGUMENT);
    require(kt_create(&seed, 1, nullptr) == KT_INVALID_ARGUMENT);
    kt_destroy(nullptr);
    auto owner = create(seed);
    auto output = observe(owner);
    output.tick = 99;
    require(kt_observe(owner.get(), 1, &output, sizeof(output)) == KT_OUT_OF_RANGE);
    require(output.tick == 99);
    require(kt_observe(owner.get(), 0, &output, sizeof(output) - 1) == KT_INVALID_ARGUMENT);
    require(kt_observe(nullptr, 0, &output, sizeof(output)) == KT_INVALID_ARGUMENT);
    require(kt_observe(owner.get(), 0, nullptr, sizeof(output)) == KT_INVALID_ARGUMENT);
    require(kt_submit(owner.get(), 0, 0, 0, nullptr, 1) == KT_INVALID_ARGUMENT);
    require(kt_submit(owner.get(), 0, 0, 0, nullptr, 4097) == KT_INVALID_ARGUMENT);
    const uint8_t invalid[]{KT_MOVE_LEFT, 255};
    require(kt_submit(owner.get(), 0, 0, 0, invalid, 2) == KT_INVALID_ARGUMENT);
    uint64_t tick = 99;
    uint64_t commands = 99;
    require(kt_advance(owner.get(), &tick, &tick) == KT_INVALID_ARGUMENT);
    require(kt_advance(owner.get(), nullptr, &commands) == KT_INVALID_ARGUMENT);
    require(kt_advance(nullptr, &tick, &commands) == KT_INVALID_ARGUMENT);
    require(kt_advance(owner.get(), &tick, &commands) == KT_OK && commands == 0 && tick == 0);
    require(kt_submit(owner.get(), 0, 0, 0, nullptr, 0) == KT_INVALID_ARGUMENT);
    require(kt_submit(owner.get(), 1, 1, 0, nullptr, 0) == KT_INVALID_ARGUMENT);
    const uint8_t actions[]{KT_HOLD, KT_MOVE_LEFT};
    require(kt_submit(owner.get(), 0, 1, UINT64_MAX, actions, 2) == KT_INVALID_ARGUMENT);
    require(kt_submit(owner.get(), 0, 1, 0, actions, 2) == KT_OK);
    require(kt_submit(owner.get(), 0, 1, 1, actions, 2) == KT_INVALID_ARGUMENT);
    require(kt_advance(owner.get(), &tick, &commands) == KT_OK && commands == 2);
}

void check_native_parity_and_lifetime() {
    bool saw_terminal = false;
    // Every scope frees the real shared-library handle. ASan/LSan runs this loop.
    for (uint64_t seed = 0; seed < 32; ++seed) {
        auto owner = create(seed);
        auto independent = create(seed);
        HeadlessRuntime native({seed});
        for (uint64_t tick = 0; tick < 32; ++tick) {
            auto copy = observe(owner);
            require(copy.tick == tick);
            check_snapshot(copy, native.observe(0));
            const auto locked_before = copy.pieces_locked;
            const bool terminal = copy.game_over != 0;
            saw_terminal = saw_terminal || terminal;
            copy.active_x = 999;  // A copied observation cannot mutate canonical state.
            require(observe(owner).active_x != 999);
            const uint8_t actions[]{static_cast<uint8_t>(tick % 7), KT_HARD_DROP};
            require(kt_submit(owner.get(), 0, tick, 0, actions, 2) == KT_OK);
            native.submit_proposal(0, tick, 0, {static_cast<SemanticAction>(actions[0]), SemanticAction::HardDrop});
            uint64_t processed_tick = 0;
            uint64_t commands = 0;
            require(kt_advance(owner.get(), &processed_tick, &commands) == KT_OK);
            const auto result = native.advance();
            require(result.tick == processed_tick && result.commands_processed == commands);
            if (terminal) {
                const auto after = observe(owner);
                require(after.pieces_locked == locked_before && after.game_over != 0);
                require(after.hold_kind == copy.hold_kind && after.hold_used == copy.hold_used);
                require(std::equal(copy.locked_cells, copy.locked_cells + 200, after.locked_cells));
            }
        }
        check_snapshot(observe(owner), native.observe(0));
        require(observe(independent).tick == 0 && observe(independent).pieces_locked == 0);
    }
    require(saw_terminal);
}

void check_multiple_players() {
    const uint64_t seeds[]{11, 29};
    kt_runtime* pointer = nullptr;
    require(kt_create(seeds, 2, &pointer) == KT_OK);
    Owner owner(pointer, kt_destroy);
    const uint8_t drop = KT_HARD_DROP;
    require(kt_submit(owner.get(), 1, 0, 0, &drop, 1) == KT_OK);
    uint64_t tick = 0;
    uint64_t commands = 0;
    require(kt_advance(owner.get(), &tick, &commands) == KT_OK && commands == 1);
    require(observe(owner).pieces_locked == 0);
    kt_observation second{};
    require(kt_observe(owner.get(), 1, &second, sizeof(second)) == KT_OK && second.pieces_locked == 1);
}

void check_benchmark_policy_parity() {
    const std::vector<uint64_t> seeds{123, 124};
    kt_runtime* pointer = nullptr;
    require(kt_create(seeds.data(), static_cast<uint32_t>(seeds.size()), &pointer) == KT_OK);
    Owner owner(pointer, kt_destroy);
    HeadlessRuntime native(seeds);
    for (uint64_t tick = 0; tick < 96; ++tick) {
        for (uint32_t player = 0; player < seeds.size(); ++player) {
            const auto expected = native.observe(player);
            auto actual = observe(owner);
            if (player != 0) {
                require(kt_observe(owner.get(), player, &actual, sizeof(actual)) == KT_OK);
            }
            check_snapshot(actual, expected);
            std::vector<SemanticAction> native_actions;
            if (!expected.game_over && expected.active_piece) {
                const auto choice = (tick + player + expected.pieces_locked) % 7U;
                native_actions.push_back(static_cast<SemanticAction>(choice));
            }
            std::vector<uint8_t> actions;
            for (const auto action : native_actions) { actions.push_back(static_cast<uint8_t>(action)); }
            require(kt_submit(owner.get(), player, tick, 0,
                actions.empty() ? nullptr : actions.data(), static_cast<uint32_t>(actions.size())) == KT_OK);
            native.submit_proposal(player, tick, 0, native_actions);
        }
        uint64_t actual_tick = 0;
        uint64_t actual_commands = 0;
        require(kt_advance(owner.get(), &actual_tick, &actual_commands) == KT_OK);
        const auto expected = native.advance();
        require(actual_tick == expected.tick && actual_commands == expected.commands_processed);
    }
}

}  // namespace

int main() {
    try {
        require(kt_abi_version() == 1 && kt_observation_size() == sizeof(kt_observation));
        check_invalid_inputs();
        check_native_parity_and_lifetime();
        check_multiple_players();
        check_benchmark_policy_parity();
    } catch (const std::exception& error) {
        std::cerr << error.what() << '\n';
        return 1;
    }
}
