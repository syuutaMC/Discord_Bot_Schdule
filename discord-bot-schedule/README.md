# Discord Bot Schedule

Discordのスケジュールイベントに連動して、ロールとチャンネルを管理するBotです。

## 概要

- イベント作成時にロールとテキストチャンネルを作成
- 参加者にロールを付与
- イベント名の日付は **JST (Asia/Tokyo)** で作成
- Bot起動時に自動 `sync` を実行

## 必要な権限

- Manage Guild
- Manage Roles
- Manage Channels

## 主要コマンド

`/schedule list`
- DBに保存されているスケジュール一覧を表示

`/schedule info event_id`
- 指定したイベントの詳細を表示
- `event_id` は **文字列** として入力（大きなIDに対応）

`/schedule delete event_id`
- 指定したスケジュールを削除（DB/チャンネル/ロール）
- `event_id` は **文字列** として入力

`/schedule sync`
- Bot停止中に作成されたイベントを手動同期
- 既存の参加者にロール付与、欠損ロール/チャンネルの作成・DB更新

`/schedule fix`
- 不整合の検出と修復
- **データソース**: SQLiteデータベースのレコードを基準に、Discordサーバーの実態と比較
- **修復内容**:
  - 削除されたロールを再作成
  - 削除されたチャンネルを再作成
  - イベントステータスに応じてチャンネルを正しいカテゴリに移動
- **スキップ条件**: スケジュールイベント本体が削除されている場合はスキップ（DBも保持）

## イベント終了/キャンセルの扱い

- **キャンセル/削除イベント**: チャンネル/ロール/DBを削除
- **終了イベント**: チャンネルを終了カテゴリに移動（DBは保持）
- **削除 or 終了が不明な場合**: そのまま保持

## 設定（環境変数）

- `TOKEN` / `TOKEN_TEST`
- `UPCOMING_CATEGORY_ID` / `UPCOMING_CATEGORY_ID_TEST`
- `ENDED_CATEGORY_ID` / `ENDED_CATEGORY_ID_TEST`
- `GUILD_ID` / `GUILD_ID_TEST`
- `ENV`（`prod` or `test`）

## 実行

```
python main.py
```
