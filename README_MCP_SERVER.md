# チケット管理システム MCP サーバー

このMCPサーバーは、チケット管理システムのAPIサービスと連携して、Claudeでチケット操作を行うためのインターフェースを提供します。

## 概要

このMCPサーバーは、Claude for Desktopなどのクライアントからのリクエストを受け取り、バックエンドのチケット管理APIに対してリクエストを行い、結果を返します。これにより、Claudeをチケット管理システムと連携させることができます。

## 前提条件

- Python 3.9以上
- MCP Python SDK
- チケット管理システムAPI（podman composeで起動）

## インストール

必要なパッケージをインストールします。

```bash
# uv を使用する場合
uv pip install "mcp[cli]" requests

# pip を使用する場合
pip install "mcp[cli]" requests
```

## 実行方法

1. チケット管理システムAPIを起動します（podman composeを使用）。

```bash
cd /path/to/api
podman-compose up -d
```

2. MCP サーバーを起動します。

```bash
# APIが別のホストまたはポートにある場合は、環境変数で指定
export API_BASE_URL="http://localhost:8080"

# サーバーを起動
python mcp_server.py
```

3. 開発モードで実行するには:

```bash
mcp dev mcp_server.py
```

4. Claude for Desktop にインストールするには:

```bash
mcp install mcp_server.py
```

## 利用可能な機能

### チケット操作

- **チケット一覧取得** (`get_ticket_list`): 検索条件に応じてチケットのリストを取得
- **チケット詳細取得** (`get_ticket_detail`): 特定のチケットの詳細情報を取得
- **チケット作成** (`create_ticket`): 新規チケットを作成
- **チケット更新** (`update_ticket`): 既存チケットの情報を更新
- **履歴追加** (`add_ticket_history`): チケットにコメントや履歴を追加

### マスターデータ参照

- **ユーザー一覧** (`get_users`): システムに登録されているユーザー情報を取得
- **アカウント一覧** (`get_accounts`): システムに登録されているアカウント情報を取得
- **カテゴリ一覧** (`get_categories`): システムに登録されているカテゴリ情報を取得
- **カテゴリ詳細一覧** (`get_category_details`): システムに登録されているカテゴリ詳細情報を取得 
- **ステータス一覧** (`get_statuses`): システムに登録されているステータス情報を取得
- **受付チャネル一覧** (`get_request_channels`): システムに登録されている受付チャネル情報を取得

## 環境変数

- `API_BASE_URL`: チケット管理システムAPIのURL（デフォルト: `http://localhost:8080`）

## 注意事項

- このサーバーはローカルでテスト用に実装されたものです。本番環境での利用には適切なセキュリティ対策が必要です。
- API接続のエラーハンドリングは実装されていますが、より堅牢な実装が必要な場合は拡張してください。

## トラブルシューティング

- APIに接続できない場合は、API_BASE_URLが正しく設定されているか確認してください。
- ログメッセージを確認して、問題の特定に役立ててください。