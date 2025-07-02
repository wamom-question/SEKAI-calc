# SEKAI-calc OCR API

プロセカのリザルト画像からスコアや判定数を自動で抽出するOCR APIサーバーです。

---

## 目次
- [主な機能](#主な機能)
- [APIエンドポイント](#apiエンドポイント)
- [開発環境構築](#開発環境構築)
- [コントリビュートガイド](#コントリビュートガイド)
- [コーディング規約](#コーディング規約)
- [注意事項](#注意事項)

---

## 主な機能
- プロセカのリザルト画像をAPIに送信すると、スコア・判定数を自動でOCR認識し、計算結果をJSONで返します。
- デバッグモードでは、認識領域のデバッグ画像や詳細サマリーも返します。

## APIエンドポイント
### POST `/ocr`
- 画像ファイル（`image`）を`multipart/form-data`で送信してください。
- デバッグ情報が必要な場合は、`debug=1` をフォームデータに含めてください。

#### リクエスト例（curl）
```sh
curl -X POST http://localhost:5000/ocr \
  -F "image=@result.png" \
  -F "debug=1"
```

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

- `score`は `PERFECT×3 + GREAT×2 + GOOD×1 + BAD×0 + MISS×0` で計算されます。(ランクマッチ)
- `debug=1`時は、認識領域の可視化画像（base64）や認識状況サマリーも返却されます。
- エラー時は`error`キーが含まれます。


---

## 開発環境構築

### 1. 必要な環境
- Docker（推奨）または Python 3.8以降
- OpenCV, pytesseract, easyocr など

### 2. セットアップ手順
- Docker利用の場合：
  ```sh
  docker compose up --build -d
  ```
- Pythonローカル実行の場合：
  ```sh
  pip install -r requirements.txt
  python result-calc.py
  ```

### 3. テスト・Lint
- テストコードは`tests/`配下に配置してください（pytest推奨）。
- Lintは`flake8`や`black`等を利用してください。
- 例：
  ```sh
  flake8 result-calc.py
  black result-calc.py
  ```

---

## コントリビュートガイド
- Issue/PRは日本語・英語どちらでも歓迎です。
- ブランチ運用：
  - `main`は常に安定版、開発は`feature/xxx`や`fix/xxx`で行い、PRでレビューを受けてください。
- コードには型アノテーション・docstring・コメントを推奨します。
- 重要な仕様変更時はREADMEも更新してください。

---

## コーディング規約
- Python 3.8+、PEP8準拠
- 型ヒント・docstring必須
- ログ出力は`logging`を利用
- 定数はファイル冒頭で定義

---

## 注意事項
- ランクマッチの対戦結果画面には対応していません。
- 画像の内容や画質によっては正しく認識できない場合があります。
- 本ツールは非公式のファンメイドツールです。
- 今後プロセカのアップデートでUI変更があると動かなくなります。

---

ご質問・不具合報告・コントリビュートはリポジトリのIssueまたはPRまでお願いします。
