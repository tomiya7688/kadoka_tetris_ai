#include <cassert>

// {
//   責務: [main: テストのassert条件式が実際に評価されることを確認する]
//   処理: [1: assert条件式で検証用flagを立てる 2: 条件式が省略されていたら失敗を返す]
//   引数: [なし]
//   戻り値: [assertが有効なら0、無効なら1]
// }
int main() {
    // 副作用を使い、NDEBUGでassert全体が除去された場合を検出する。
    bool assertion_evaluated = false;
    assert((assertion_evaluated = true));

    // assert自身を使わず、検証結果を終了コードへ反映する。
    return assertion_evaluated ? 0 : 1;
}
