#include "kadoka/tetris/tetromino.hpp"

#include <stdexcept>

namespace kadoka::tetris {

Tetromino make_tetromino(PieceType kind) {
    switch (kind) {
        case PieceType::I:
            return {kind, {{{0, 1}, {1, 1}, {2, 1}, {3, 1}}}};
        case PieceType::O:
            return {kind, {{{1, 0}, {2, 0}, {1, 1}, {2, 1}}}};
        case PieceType::T:
            return {kind, {{{1, 0}, {0, 1}, {1, 1}, {2, 1}}}};
        case PieceType::S:
            return {kind, {{{1, 0}, {2, 0}, {0, 1}, {1, 1}}}};
        case PieceType::Z:
            return {kind, {{{0, 0}, {1, 0}, {1, 1}, {2, 1}}}};
        case PieceType::J:
            return {kind, {{{0, 0}, {0, 1}, {1, 1}, {2, 1}}}};
        case PieceType::L:
            return {kind, {{{2, 0}, {0, 1}, {1, 1}, {2, 1}}}};
    }
    throw std::invalid_argument("unknown tetromino type");
}

}  // namespace kadoka::tetris
