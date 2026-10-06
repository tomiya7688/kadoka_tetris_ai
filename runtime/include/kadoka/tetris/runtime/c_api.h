#ifndef KADOKA_TETRIS_RUNTIME_C_API_H
#define KADOKA_TETRIS_RUNTIME_C_API_H

#include <stdint.h>

#if defined(_WIN32)
#define KT_CALL __cdecl
#if defined(KADOKA_TETRIS_C_API_BUILD)
#define KT_API __declspec(dllexport)
#else
#define KT_API __declspec(dllimport)
#endif
#else
#define KT_CALL
#define KT_API __attribute__((visibility("default")))
#endif

#ifdef __cplusplus
extern "C" {
#endif

typedef struct kt_runtime kt_runtime;

enum kt_status {
    KT_OK = 0,
    KT_INVALID_ARGUMENT = 1,
    KT_OUT_OF_RANGE = 2,
    KT_OUT_OF_MEMORY = 3,
    KT_INTERNAL_ERROR = 4
};

enum kt_action {
    KT_MOVE_LEFT = 0, KT_MOVE_RIGHT = 1,
    KT_ROTATE_CLOCKWISE = 2, KT_ROTATE_COUNTERCLOCKWISE = 3,
    KT_SOFT_DROP = 4, KT_HARD_DROP = 5, KT_HOLD = 6
};

/* ABI v1 uses the default 10x20 visible board and five visible NEXT pieces.
   Piece codes: I=0, O=1, T=2, S=3, Z=4, J=5, L=6; absent=-1.
   Board masks are row-major boolean bytes; hidden rows are never exported. */
typedef struct kt_observation {
    uint64_t tick;
    uint64_t pieces_locked;
    int32_t active_kind;
    int32_t active_x;
    int32_t active_y;
    int32_t active_rotation;
    int32_t hold_kind;
    int32_t lines;
    int32_t combo;
    int32_t next_pieces[5];
    uint32_t hold_used;
    uint32_t game_over;
    uint32_t back_to_back_active;
    uint8_t locked_cells[200];
    uint8_t active_cells[200];
} kt_observation;

typedef struct kt_proposal {
    uint32_t player;
    uint64_t first_sequence;
    uint32_t action_offset;
    uint32_t action_count;
} kt_proposal;

KT_API uint32_t KT_CALL kt_abi_version(void);
KT_API uint32_t KT_CALL kt_observation_size(void);
/* On failure *output is NULL. Seeds count is 1..64. */
KT_API int32_t KT_CALL kt_create(const uint64_t* seeds, uint32_t count, kt_runtime** output);
/* NULL is allowed. A successful create must be paired with exactly one destroy. */
KT_API void KT_CALL kt_destroy(kt_runtime* runtime);
/* Output is changed only on success. size must match kt_observation_size(). */
KT_API int32_t KT_CALL kt_observe(const kt_runtime* runtime, uint32_t player,
    kt_observation* output, uint32_t size);
/* Count must match the runtime's player count (1..64); output changes only on success. */
KT_API int32_t KT_CALL kt_observe_many(const kt_runtime* runtime,
    kt_observation* outputs, uint32_t count);
/* Proposal length is 0..4096. Empty proposal permits NULL actions. */
KT_API int32_t KT_CALL kt_submit(kt_runtime* runtime, uint32_t player,
    uint64_t tick, uint64_t first_sequence, const uint8_t* actions, uint32_t count);
/* Up to 64 proposal descriptors and 4096 flattened actions; all validate atomically. */
KT_API int32_t KT_CALL kt_submit_many(kt_runtime* runtime, uint64_t tick,
    const kt_proposal* proposals, uint32_t proposal_count,
    const uint8_t* actions, uint32_t action_count);
/* Returns the processed tick and command count; output pointers are required. */
KT_API int32_t KT_CALL kt_advance(kt_runtime* runtime, uint64_t* tick, uint64_t* commands);

#ifdef __cplusplus
}
#endif
#endif
