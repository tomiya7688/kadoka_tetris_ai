#pragma once

#include "kadoka/tetris/tetromino.hpp"

#include <cstddef>
#include <cstdint>
#include <vector>

namespace kadoka::tetris {

// {
//   責務: [Board: 盤面寸法と占有セルを保持し、配置・固定・行消去・garbage反映を提供する]
//   フィールド: [width_: 盤面の列数 visible_height_: 表示領域の行数 hidden_rows_: 表示領域より上の隠し行数 height_: 隠し行を含む総行数 cells_: 行優先で保持する占有セル]
//   処理: [盤面座標を検証し、Tetrominoの配置可能性を判定してセル状態を更新する]
// }
class Board {
public:
    // {
    //   責務: [Board::Board: 指定した寸法の空盤面を作る]
    //   処理: [1: 盤面寸法を保持して不正な符号を拒否する 2: 隠し行を含む全セルを空で初期化する]
    //   引数: [width: 正の列数 visible_height: 正の表示行数 hidden_rows: 0以上の隠し行数]
    //   戻り値: [なし]
    //   エラー: [widthまたはvisible_heightが0以下、hidden_rowsが負ならstd::invalid_argumentを送出する]
    // }
    explicit Board(int width = 10, int visible_height = 20, int hidden_rows = 2);

    // {
    //   責務: [Board::width: 盤面の列数を返す]
    //   処理: [保持しているwidth_を読み出す]
    //   引数: [なし]
    //   戻り値: [盤面の列数]
    // }
    [[nodiscard]] int width() const noexcept { return width_; }
    // {
    //   責務: [Board::visible_height: 表示領域の行数を返す]
    //   処理: [保持しているvisible_height_を読み出す]
    //   引数: [なし]
    //   戻り値: [隠し行を含まない表示行数]
    // }
    [[nodiscard]] int visible_height() const noexcept { return visible_height_; }
    // {
    //   責務: [Board::hidden_rows: 上端の隠し行数を返す]
    //   処理: [保持しているhidden_rows_を読み出す]
    //   引数: [なし]
    //   戻り値: [表示領域より上に確保した行数]
    // }
    [[nodiscard]] int hidden_rows() const noexcept { return hidden_rows_; }
    // {
    //   責務: [Board::height: 隠し行を含む盤面の総行数を返す]
    //   処理: [保持しているheight_を読み出す]
    //   引数: [なし]
    //   戻り値: [表示行数と隠し行数の合計]
    // }
    [[nodiscard]] int height() const noexcept { return height_; }

    // {
    //   責務: [Board::occupied: 指定セルが占有されているか調べる]
    //   処理: [1: 座標が盤面内か検証する 2: 対応するセルの占有状態を返す]
    //   引数: [x: 列番号 y: 隠し行を含む上端を0とする行番号]
    //   戻り値: [占有セルならtrue、空セルならfalse]
    //   エラー: [盤面外の座標ならstd::out_of_rangeを送出する]
    // }
    [[nodiscard]] bool occupied(int x, int y) const;
    // {
    //   責務: [Board::can_place: ミノの全セルが盤面内の空きセルに収まるか判定する]
    //   処理: [各セルの相対座標にoriginを加え、盤面外または占有セルとの衝突を調べる]
    //   引数: [piece: 配置するミノのセル定義 origin: 相対座標の基準となる盤面座標]
    //   戻り値: [すべてのセルを配置できればtrue、盤面外または衝突があればfalse]
    // }
    [[nodiscard]] bool can_place(const Tetromino& piece, Position origin) const noexcept;

    // {
    //   責務: [Board::lock: 配置可能なミノのセルを盤面へ固定する]
    //   処理: [1: can_placeで配置を検証する 2: ミノの各セルを占有状態にする]
    //   引数: [piece: 固定するミノのセル定義 origin: 配置の基準座標]
    //   戻り値: [なし]
    //   副作用: [ミノが占めるセルを更新する。行消去は行わない]
    //   エラー: [配置できなければ盤面を変更せずstd::invalid_argumentを送出する]
    // }
    void lock(const Tetromino& piece, Position origin);
    // {
    //   責務: [Board::clear_full_rows: 全列が埋まった行を除去して残る行を下へ詰める]
    //   処理: [1: 隠し行を含む全行から未充填の行を順序を保って集める 2: 消去した行数だけ上端を空にして残る行を配置する]
    //   引数: [なし]
    //   戻り値: [消去した行数。対象行がなければ0]
    //   副作用: [充填行があれば盤面の占有セルを更新する]
    // }
    [[nodiscard]] int clear_full_rows();
    // {
    //   責務: [Board::add_garbage: 指定した穴を持つgarbage行を下端へ追加し、上端のあふれを検出する]
    //   処理: [1: すべての穴の列番号を検証する 2: 追加行数と押し出される占有セルからあふれを判定する 3: 既存セルを上へ移し下端へgarbageを配置する]
    //   引数: [hole_columns: 上から下への順に並ぶ追加行の穴の列番号。総行数を超える場合は末尾の行だけを保持する]
    //   戻り値: [追加行数が総行数を超えるか、占有セルが上端から押し出されればtrue。追加行がなければfalse]
    //   副作用: [追加行があれば盤面を更新する。あふれ時も追加後の盤面を保持する]
    //   エラー: [穴の列番号が盤面外なら盤面を変更せずstd::invalid_argumentを送出する]
    // }
    [[nodiscard]] bool add_garbage(const std::vector<int>& hole_columns);

    // {
    //   責務: [Board::occupied_cells: 隠し行を含む全占有セルの座標一覧を返す]
    //   処理: [上端から行順に、各行は左から右へ占有セルを集める]
    //   引数: [なし]
    //   戻り値: [盤面とは独立した占有セルの座標一覧]
    // }
    [[nodiscard]] std::vector<Position> occupied_cells() const;

private:
    // {
    //   責務: [Board::in_bounds: 座標が隠し行を含む盤面内か判定する]
    //   処理: [xとyが0以上かつ列数・総行数未満か調べる]
    //   引数: [x: 列番号 y: 行番号]
    //   戻り値: [盤面内ならtrue、盤面外ならfalse]
    // }
    [[nodiscard]] bool in_bounds(int x, int y) const noexcept;
    // {
    //   責務: [Board::index: 盤面座標を行優先のセル配列の位置へ変換する]
    //   処理: [yに列数を掛けてxを加える]
    //   引数: [x: 盤面内の列番号 y: 盤面内の行番号]
    //   戻り値: [cells_に対応する添字]
    //   補足: [呼び出し元が座標を検証する。ここでは範囲検査を行わない]
    // }
    [[nodiscard]] std::size_t index(int x, int y) const noexcept;

    int width_{};
    int visible_height_{};
    int hidden_rows_{};
    int height_{};
    std::vector<std::uint8_t> cells_;
};

}  // namespace kadoka::tetris
