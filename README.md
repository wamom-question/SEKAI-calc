# SEKAI-calc OCR API

プロセカのリザルト画像からスコアや判定数を自動で抽出するOCR APIサーバーです。

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

## Dockerでの実行方法
1. `docker-compose.yml` と `dockerfile` が同梱されています。
2. 以下のコマンドでビルド＆起動できます。

```sh
docker compose up --build -d
```

3. 停止は以下で可能です。

```sh
docker compose down
```

## 必要な環境
- Docker（推奨）または Python 3.8以降
- 必要なパッケージは `requirements.txt` を参照し、`pip install -r requirements.txt` でインストールしてください。
- OpenCV, pytesseract, easyocr などが必要です。

## 注意事項
- 画像の内容や画質によっては正しく認識できない場合があります。
- 本ツールは非公式のファンメイドツールです。
- 今後プロセカのアップデートでUI変更があると動かなくなります。

---

ご質問・不具合報告はリポジトリのIssueまでお願いします。
