# SEKAI-calc OCR API

プロセカのリザルト画像からスコアや判定数を自動で抽出するOCR APIサーバーです。

## 主な機能
- プロセカのリザルト画像をAPIに送信すると、スコア・判定数をOCR認識し、計算結果をJSONで返します。
- デバッグモード（`debug=1`）で認識領域の可視化画像やサマリーも返します。

## APIエンドポイント
### POST `/ocr`
- 画像ファイル（`image`）を`multipart/form-data`で送信。
- デバッグ情報が必要な場合は`debug=1`をフォームデータに含めてください。

#### レスポンス例
```json
{
  "results": [
    {
      "player": 1,
      "perfect": 1234,
      "great": 56,
      "good": 7,
      "bad": 0,
      "miss": 0,
      "score": 3704
    },
    ...
  ],
  "debug_image_base64": "...",
  "debug_summary": "..."
}
```
- `score`は `PERFECT×3 + GREAT×2 + GOOD×1 + BAD×0 + MISS×0` で計算されます。
- エラー時は`error`キーが含まれます。

## セットアップ
- Docker（推奨）または Python 3.8以降
- 必要パッケージは`requirements.txt`参照
- Dockerの場合：
  ```sh
  docker compose up --build -d
  ```
- ローカル実行：
  ```sh
  pip install -r requirements.txt
  python result-calc.py
  ```

## 注意事項
- ランクマッチの対戦結果画面には非対応。
- 画像内容や画質によっては認識できない場合あり。
- 本ツールは非公式のファンメイドツールです。

ご質問・不具合報告はリポジトリのIssueまでお願いします。
