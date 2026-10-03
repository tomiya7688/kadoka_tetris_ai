#include "kadoka/tetris/runtime/c_api.h"
#include "kadoka/tetris/runtime/headless_runtime.hpp"

#include <memory>
#include <new>
#include <stdexcept>
#include <vector>

using kadoka::tetris::runtime::HeadlessRuntime;
using kadoka::tetris::runtime::SemanticAction;

// Opaque handle owns one independent canonical runtime.
struct kt_runtime {
    HeadlessRuntime value;
};

namespace {

// Freeze wire values independently from future changes to native enums.
static_assert(static_cast<int>(SemanticAction::MoveLeft) == KT_MOVE_LEFT);
static_assert(static_cast<int>(SemanticAction::MoveRight) == KT_MOVE_RIGHT);
static_assert(static_cast<int>(SemanticAction::RotateClockwise) == KT_ROTATE_CLOCKWISE);
static_assert(static_cast<int>(SemanticAction::RotateCounterClockwise) == KT_ROTATE_COUNTERCLOCKWISE);
static_assert(static_cast<int>(SemanticAction::SoftDrop) == KT_SOFT_DROP);
static_assert(static_cast<int>(SemanticAction::HardDrop) == KT_HARD_DROP);
static_assert(static_cast<int>(SemanticAction::Hold) == KT_HOLD);
using kadoka::tetris::PieceType;
static_assert(static_cast<int>(PieceType::I) == 0 && static_cast<int>(PieceType::O) == 1
    && static_cast<int>(PieceType::T) == 2 && static_cast<int>(PieceType::S) == 3
    && static_cast<int>(PieceType::Z) == 4 && static_cast<int>(PieceType::J) == 5
    && static_cast<int>(PieceType::L) == 6);

template <typename Operation>
int32_t guarded(Operation operation) noexcept {
    try {
        operation();
        return KT_OK;
    } catch (const std::bad_alloc&) {
        return KT_OUT_OF_MEMORY;
    } catch (const std::out_of_range&) {
        return KT_OUT_OF_RANGE;
    } catch (const std::invalid_argument&) {
        return KT_INVALID_ARGUMENT;
    } catch (...) {
        return KT_INTERNAL_ERROR;
    }
}

kt_observation snapshot(const HeadlessRuntime& runtime, uint32_t player) {
    const auto source = runtime.observe(player);
    kt_observation result{};
    result.tick = runtime.current_tick();
    result.pieces_locked = source.pieces_locked;
    result.active_kind = -1;
    result.hold_kind = source.hold_piece ? static_cast<int32_t>(*source.hold_piece) : -1;
    if (source.active_piece) {
        result.active_kind = static_cast<int32_t>(source.active_piece->kind);
        result.active_x = source.active_piece->x;
        result.active_y = source.active_piece->y;
        result.active_rotation = source.active_piece->rotation;
    }
    result.lines = source.lines;
    result.combo = source.combo;
    result.hold_used = source.hold_used;
    result.game_over = source.game_over;
    result.back_to_back_active = source.back_to_back_active;
    for (uint32_t index = 0; index < 5; ++index) {
        result.next_pieces[index] = static_cast<int32_t>(source.next_pieces.at(index));
    }
    for (const auto cell : source.board.locked_cells) {
        result.locked_cells[cell.y * 10 + cell.x] = 1;
    }
    for (const auto cell : source.board.active_cells) {
        result.active_cells[cell.y * 10 + cell.x] = 1;
    }
    return result;
}

}  // namespace

uint32_t KT_CALL kt_abi_version(void) { return 1; }
uint32_t KT_CALL kt_observation_size(void) { return sizeof(kt_observation); }

int32_t KT_CALL kt_create(const uint64_t* seeds, uint32_t count, kt_runtime** output) {
    if (!output) { return KT_INVALID_ARGUMENT; }
    *output = nullptr;
    if (!seeds || count == 0 || count > 64) { return KT_INVALID_ARGUMENT; }
    return guarded([&] {
        auto owner = std::make_unique<kt_runtime>(
            kt_runtime{HeadlessRuntime(std::vector<uint64_t>(seeds, seeds + count))});
        *output = owner.release();
    });
}

void KT_CALL kt_destroy(kt_runtime* runtime) { delete runtime; }

int32_t KT_CALL kt_observe(const kt_runtime* runtime, uint32_t player,
                         kt_observation* output, uint32_t size) {
    if (!runtime || !output || size != sizeof(kt_observation)) { return KT_INVALID_ARGUMENT; }
    return guarded([&] { *output = snapshot(runtime->value, player); });
}

int32_t KT_CALL kt_submit(kt_runtime* runtime, uint32_t player,
                        uint64_t tick, uint64_t first_sequence,
                        const uint8_t* actions, uint32_t count) {
    if (!runtime || count > 4096 || (count != 0 && !actions)) { return KT_INVALID_ARGUMENT; }
    return guarded([&] {
        std::vector<SemanticAction> proposal;
        proposal.reserve(count);
        for (uint32_t index = 0; index < count; ++index) {
            if (actions[index] > KT_HOLD) { throw std::invalid_argument("invalid action"); }
            proposal.push_back(static_cast<SemanticAction>(actions[index]));
        }
        runtime->value.submit_proposal(player, tick, first_sequence, proposal);
    });
}

int32_t KT_CALL kt_advance(kt_runtime* runtime, uint64_t* tick, uint64_t* commands) {
    if (!runtime || !tick || !commands || tick == commands) { return KT_INVALID_ARGUMENT; }
    return guarded([&] {
        const auto result = runtime->value.advance();
        *tick = result.tick;
        *commands = result.commands_processed;
    });
}
