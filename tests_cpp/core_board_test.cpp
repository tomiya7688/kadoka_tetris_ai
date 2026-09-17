#include "kadoka/tetris/board.hpp"
#include "kadoka/tetris/tetromino.hpp"

#include <cassert>
#include <stdexcept>
#include <vector>

using namespace kadoka::tetris;

int main() {
    {
        Board board;
        assert(board.width() == 10);
        assert(board.visible_height() == 20);
        assert(board.hidden_rows() == 2);
        assert(board.height() == 22);
        assert(board.occupied_cells().empty());
    }

    {
        const Tetromino piece = make_tetromino(PieceType::I);
        assert((piece.cells[0] == Offset{0, 1}));
        assert((piece.cells[1] == Offset{1, 1}));
        assert((piece.cells[2] == Offset{2, 1}));
        assert((piece.cells[3] == Offset{3, 1}));

        Board board;
        assert(board.can_place(piece, {3, 0}));
        board.lock(piece, {3, 0});
        for (int x = 3; x <= 6; ++x) {
            assert(board.occupied(x, 1));
        }
        assert(!board.can_place(piece, {3, 0}));
        assert(!board.can_place(piece, {-1, 0}));
    }

    {
        Board board(4, 4, 0);
        const Tetromino row{
            PieceType::I,
            {{{0, 0}, {1, 0}, {2, 0}, {3, 0}}},
        };
        board.lock(row, {0, 3});
        assert(board.clear_full_rows() == 1);
        assert(board.occupied_cells().empty());
    }

    {
        Board board(4, 4, 0);
        const bool overflow = board.add_garbage({1, 2});
        assert(!overflow);
        for (int x = 0; x < 4; ++x) {
            assert(board.occupied(x, 2) == (x != 1));
            assert(board.occupied(x, 3) == (x != 2));
        }
    }

    {
        Board board(4, 2, 0);
        assert(board.add_garbage({0, 1, 2}));
        for (int x = 0; x < 4; ++x) {
            assert(board.occupied(x, 0) == (x != 1));
            assert(board.occupied(x, 1) == (x != 2));
        }
    }

    {
        Board board(4, 4, 0);
        const Tetromino marker{
            PieceType::O,
            {{{0, 0}, {1, 0}, {0, 1}, {1, 1}}},
        };
        board.lock(marker, {0, 0});
        assert(board.add_garbage({2}));
    }

    {
        Board board;
        bool rejected = false;
        try {
            (void)board.add_garbage({10});
        } catch (const std::invalid_argument&) {
            rejected = true;
        }
        assert(rejected);
    }

    return 0;
}
