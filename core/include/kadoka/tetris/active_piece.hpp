#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <array>

namespace kadoka::tetris {

// {
//   責務: [ActivePiece: 操作中ミノの種類・盤面上の位置・回転状態を保持する]
//   フィールド: [kind: ミノの種類 x: 盤面上の基準列 y: 盤面上の基準行 rotation: 90度単位の回転数。cellsでは4を法として扱う]
//   処理: [保持する種類と回転数から、配置判定に使う4セルの相対座標を求める]
// }
struct ActivePiece {
    PieceType kind{PieceType::I};
    int x{3};
    int y{0};
    int rotation{0};

    // {
    //   責務: [ActivePiece::cells: 種類と回転数に対応する4セルの相対座標を返す]
    //   処理: [1: 基本形を取得して回転数を0から3へ正規化する 2: 90度ずつ回転し、各回転後に最小xと最小yを0へ移す]
    //   引数: [なし]
    //   戻り値: [基準位置からの4セルの相対座標。盤面位置x・yは加えない]
    //   エラー: [kindが未知の値ならmake_tetrominoからstd::invalid_argumentが伝播する]
    //   補足: [正規化した回転数が0なら、基本形のセル座標を移動せず返す。保持している状態は変更しない]
    // }
    [[nodiscard]] std::array<Offset, 4> cells() const;
};

}  // namespace kadoka::tetris
