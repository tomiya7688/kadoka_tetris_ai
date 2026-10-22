#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <array>
#include <cstddef>
#include <cstdint>

namespace kadoka::tetris {

// {
//   責務: [SevenBag: seedから再現可能な、7種類を1つずつ含むbagのツモを供給する]
//   フィールド: [state_: 64bit内部乱数状態 queue_: 現在のbagを保持する配列 remaining_: 現在のbagからまだ取り出していない個数]
//   処理: [現在のbagを末尾側から消費し、空になったら7種類を並べ替えて補充する]
// }
class SevenBag {
public:
    // {
    //   責務: [SevenBag::SevenBag: 指定したseedでツモ生成器を初期化する]
    //   処理: [内部乱数状態をseedに設定する。bagは最初のnext呼び出し時に補充する]
    //   引数: [seed: 64bitの初期乱数状態。既定値は0]
    //   戻り値: [なし]
    //   補足: [同じseedから同じ回数nextを呼ぶと、同じツモ列を得る]
    // }
    explicit SevenBag(std::uint64_t seed = 0) noexcept : state_(seed) {}

    // {
    //   責務: [SevenBag::next: 次のツモを1つ取り出す]
    //   処理: [1: 残数が0ならbagを補充する 2: 残数を減らして未取得範囲の末尾の種類を返す]
    //   引数: [なし]
    //   戻り値: [次のミノの種類]
    //   副作用: [現在のbagを消費する。補充時には内部乱数状態とbagも更新する]
    // }
    [[nodiscard]] PieceType next();

private:
    // {
    //   責務: [SevenBag::next_random: 内部状態を進めて64bit乱数値を生成する]
    //   処理: [1: 符号なし64bitの加算で状態を進める 2: シフト・排他的論理和・乗算で混合した値を返す]
    //   引数: [なし]
    //   戻り値: [混合後の64bit乱数値]
    //   副作用: [state_を更新する]
    // }
    [[nodiscard]] std::uint64_t next_random() noexcept;
    // {
    //   責務: [SevenBag::bounded: 剰余による偏りを避けて上限未満の乱数値を生成する]
    //   処理: [1: boundが0または1なら0を返す 2: 分割時の端数に当たる値を棄却する 3: 採用した値の剰余を返す]
    //   引数: [bound: 生成範囲の上限。この値自体は含めない]
    //   戻り値: [boundが2以上なら0以上bound未満の値。boundが0または1なら0]
    //   副作用: [boundが2以上なら採用されるまで内部乱数状態を進める]
    // }
    [[nodiscard]] std::uint64_t bounded(std::uint64_t bound) noexcept;
    // {
    //   責務: [SevenBag::refill: 次に取り出す7種類のbagを作り直す]
    //   処理: [1: 固定順の7種類を配列へ設定する 2: 末尾から未確定範囲内の位置を選んで交換する 3: 残数を7へ戻す]
    //   引数: [なし]
    //   戻り値: [なし]
    //   副作用: [queue_・remaining_・内部乱数状態を更新する]
    // }
    void refill() noexcept;

    std::uint64_t state_{};
    std::array<PieceType, 7> queue_{};
    std::size_t remaining_{};
};

}  // namespace kadoka::tetris
