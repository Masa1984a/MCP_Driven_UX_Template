# MCP Driven UX テンプレート

<div align="center">

<p align="center">
  <img src="assets/MCP_Driven_UX_logo.png" width="648"/>
</p>

![MCP Logo](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)
![TypeScript](https://img.shields.io/badge/TypeScript-3.0+-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)

<p align="center">
  <a href="./README.md"><img alt="README in English" src="https://img.shields.io/badge/English-d9d9d9"></a>
  <a href="./README_JA.md"><img alt="日本語のREADME" src="https://img.shields.io/badge/日本語-d9d9d9"></a>
  <a href="./README_CN.md"><img alt="简体中文版自述文件" src="https://img.shields.io/badge/简体中文-d9d9d9"></a>
  <a href="./README_TW.md"><img alt="繁體中文版README" src="https://img.shields.io/badge/繁體中文-d9d9d9"></a>
  <a href="./README_KR.md"><img alt="README in Korean" src="https://img.shields.io/badge/한국어-d9d9d9"></a>
  <a href="./README_AR.md"><img alt="README بالعربية" src="https://img.shields.io/badge/العربية-d9d9d9"></a>
</p>

**次世代ユーザ体験「MCP Driven UX」を実現するチケット管理システムテンプレート**

<a href="https://www.youtube.com/watch?v=Q7iKhyOF_OM" target="_blank" rel="noopener noreferrer">
  <img src="https://img.youtube.com/vi/Q7iKhyOF_OM/0.jpg" alt="Introduction: MCP Driven UX Template">
</a>

*YouTube: Introduction: MCP Driven UX Template*

</div>

## 📋 概要

このプロジェクトは、従来のMVC（Model-View-Controller）アーキテクチャから、LLMとの対話型インターフェースへのパラダイムシフトを提案する「MCP Driven UX」のリファレンス実装です。

Model Context Protocol（MCP）を活用し、チケット管理システムをサンプルとして、以下の技術スタックの役割分担と実装方法を示します：

- **MCP Server (Python)**: LLMとバックエンドAPIの連携
- **ビジネスロジック (TypeScript)**: RESTful APIの実装
- **データモデル (PostgreSQL)**: 永続化層の管理

## 🎯 コンセプト

### MVC から MCP Driven UX へ

現在のWebサービスやクライアント・サーバーアプリケーションは主にMVCパターンに基づいています。しかし、LLMの台頭とMCPのような標準化により、UIベースのサービスから対話型（チャット・音声）インターフェースへの転換が期待されます。

このリポジトリは、その転換を実現するためのテンプレートとして、チケット管理システムを例に実装しています。

### アーキテクチャ

<img src="assets/MCP_Driven_UX_Architecture.png" width="648"/>

```
┌─────────────┐     MCP      ┌───────────────┐     HTTP     ┌──────────────┐
│   Claude    │◄────────────►│  MCP Server   │◄────────────►│  API Server  │
│  Desktop    │              │   (Python)    │              │ (TypeScript) │
└─────────────┘              └───────────────┘              └──────┬───────┘
                                                                   │
                                                                   ▼
                                                             ┌──────────────┐
                                                             │  PostgreSQL  │
                                                             │     (DB)     │
                                                             └──────────────┘
```

## ✨ 主な機能

- **チケット管理**
  - チケットの作成、更新、検索、詳細表示
  - 履歴管理とコメント機能
  - ステータス管理と担当者割り当て

- **MCP インテグレーション**
  - Claude Desktop からの自然言語によるチケット操作
  - マスターデータの参照とフィルタリング
  - リアルタイムステータス確認

- **エンタープライズ機能**
  - ロールベースのアクセス制御
  - 監査証跡とログ管理
  - マルチテナント対応

## 🛠️ 技術スタック

### Backend
- **MCP Server**: Python 3.9+, MCP SDK
- **API Server**: Node.js, TypeScript, Express
- **Database**: PostgreSQL 16

### Infrastructure
- **Container**: Docker/Podman
- **Orchestration**: Docker Compose

## 📥 インストール方法

### 前提条件

- Docker または Podman（推奨）
- docker-compose または podman-compose
- Python 3.9以上（MCP サーバー用）
- Node.js 18以上（API サーバー用）
- Claude Desktop（MCP クライアント）

### セットアップ手順

1. **リポジトリのクローン**

```bash
git clone https://github.com/Masa1984a/MCP_Driven_UX_Template.git
cd MCP_Driven_UX_Template
```

2. **認証設定**（Podman/Docker）

```bash
# Podman の場合
podman login docker.io --username <username>

# Docker の場合 (Podmanでcomposeする時も必要)
docker login docker.io --username <username>
```

3. **環境変数の設定**

```bash
cp .env.sample .env
# 必要に応じて .env ファイルを編集 (データを日本語に変えたい時は、INIT_LANG=jaに変更ください)
```

4. **コンテナの起動**

```bash
# Podman の場合
podman compose up -d

# Docker の場合
docker-compose up -d
```

5. **Python仮想環境の構築**

MCPサーバー用のPython環境をセットアップします：

```bash
cd ./mcp_server
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShellの場合
# Bash/Linux/Macの場合: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. **Claude for Desktopの設定**

Claude for Desktopの設定ファイル`claude_desktop_config.json`を編集：

```json
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "プロジェクトディレクトリパス",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**注意**: `プロジェクトディレクトリパス`は実際のプロジェクトパスに置き換えてください。Windowsの場合はパスのバックスラッシュをエスケープする必要があります。例: `C:\\Users\\username\\projects\\ticket-system`

### データのリセット

既存のデータを削除して再初期化する場合：

```bash
# ボリュームを含めて停止
podman compose down -v

# 再起動
podman compose up --build -d
```

## 🔍 使用方法

### Claude Desktop からの操作

MCP サーバーが起動したら、Claude Desktop から以下のような自然言語でチケットを操作できます：

```
# チケット一覧の表示
"現在のチケット一覧を表示して"

# 特定条件での検索
"今週完了予定のチケットは？"

# チケットの作成
"新しいチケットを作成して。ユーザーマスター更新の依頼。"

# チケットの更新
"チケット TCK-0002 のステータスを対応中に変更"
```

### API エンドポイント

API サーバーは以下のエンドポイントを提供します：

- `GET /tickets` - チケット一覧の取得（フィルタリング・ページネーション対応）
- `GET /tickets/:id` - チケット詳細の取得
- `POST /tickets` - 新規チケットの作成
- `PUT /tickets/:id` - チケットの更新
- `POST /tickets/:id/history` - 履歴の追加
- `GET /tickets/:id/history` - 履歴の取得

マスターデータ：
- `GET /tickets/master/users` - ユーザー一覧
- `GET /tickets/master/accounts` - アカウント一覧
- `GET /tickets/master/categories` - カテゴリ一覧
- `GET /tickets/master/statuses` - ステータス一覧

## 📊 データモデル

主要なテーブル構造：

```sql
-- チケットテーブル (tickets)
- id: チケットID (TCK-XXXX形式)
- reception_date_time: 受付日時
- requestor_id/name: 依頼者
- account_id/name: アカウント（企業）
- category_id/name: カテゴリ
- status_id/name: ステータス
- person_in_charge_id/name: 担当者
- scheduled_completion_date: 完了予定日
```

詳細な構造は `/db/init/en/init.sql` または `/db/init/ja/init.sql` を参照してください。

## 🚀 デプロイメント

### 本番環境への展開

このアプリケーションは以下のプラットフォームにデプロイ可能です(要検証)：

- **Google Cloud Platform**
  - Cloud Functions v2（ソースアップロード）
  - Cloud Run（Docker イメージ）
  - Cloud SQL for PostgreSQL

- **AWS**
  - Lambda + API Gateway
  - ECS/Fargate
  - RDS for PostgreSQL

- **Azure**
  - Functions
  - Container Instances
  - Azure Database for PostgreSQL

## 🧩 拡張性

このテンプレートは以下の拡張が可能です：

- **追加の MCP ツール**: ファイル操作、外部 API 連携など
- **認証・認可**: OAuth 2.0、SAML 対応
- **通知機能**: メール、Slack、Teams 連携
- **レポート機能**: PDF 生成、ダッシュボード
- **マルチ言語対応**: i18n 実装

## 🤝 コントリビューション

プルリクエストは歓迎します。大きな変更の場合は、まず Issue を作成して議論してください。

1. Fork リポジトリ
2. Feature ブランチを作成 (`git checkout -b feature/AmazingFeature`)
3. 変更をコミット (`git commit -m 'Add some AmazingFeature'`)
4. ブランチをプッシュ (`git push origin feature/AmazingFeature`)
5. プルリクエストを作成

## README_JA 更新内容要約

PgTyped 導入に伴い開発フローの変更点をまとめました。

- `src/sql` ディレクトリにテーブルごとの SQL ファイルを配置
- `user` テーブル以外のクエリは PgTyped で型を自動生成
- ローカル開発では `pgtyped -w`、CI では `pgtyped -c` を使用
- パッケージスクリプトと CI に型生成ステップを追加

## 🔐 セキュリティ

- 本番環境では環境変数を適切に管理してください
- データベースの認証情報は決してコミットしないでください
- MCP サーバーのアクセス制御を適切に設定してください

## 📄 ライセンス

[MIT License](LICENSE)

## 🙏 謝辞

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - Anthropic によるSWE(Software Engineering) Agent
- [Codex CLI](https://github.com/openai/codex) - OpenAI によるSWE(Software Engineering) Agent
- [Model Context Protocol](https://modelcontextprotocol.io) - Anthropic によるオープンスタンダード
- Claude Desktop - MCP クライアント実装
- すべてのコントリビューターの皆様

## ⚠️ 商標・ブランドに関する注意書き

本リポジトリは OSS として MIT License で公開されていますが、下記の製品名・サービス名・ロゴは
各社の登録商標または商標です。プロジェクトは各社による公式な後援・提携・承認を
受けておらず、商標権者との間に資本・契約関係はありません。

| 商標 | 権利者 | 参考ブランドガイドライン |
| ---- | ------ | ------------------------ |
| Claude™, Anthropic™ | Anthropic PBC | ブランドガイドラインに従ってご利用ください<sup>※1</sup> |
| OpenAI®, ChatGPT®, Codex® | OpenAI OpCo, LLC | OpenAI Brand Guidelines<sup>※2</sup> |
| GPT | OpenAI（申請中）ほか | 一般名詞として使用する場合でも誤認を避ける表記を推奨 |
| PostgreSQL® | The PostgreSQL Global Development Group | — |
| Docker® | Docker, Inc. | — |

<sup>※1</sup> Anthropic は公式サイトで商標ポリシーを随時更新しています。利用時は最新の指針を確認してください。  
<sup>※2</sup> OpenAI の名称・ロゴを使用する際は OpenAI Brand Guidelines に従う必要があります。ガイドラインは変更される可能性があるため、定期的な確認を推奨します。

### API・サービス利用規約

- **OpenAI API / Claude API** などの生成 AI サービスを組み込む場合、各社の
  [Terms of Use](https://openai.com/policies/row-terms-of-use) や AUP を遵守してください。
- 商用利用や大量アクセスが想定される場合は、レート制限・出力の二次利用条件・
  個人情報の取り扱いに関する条項を必ず確認してください。

> **Disclaimer:**  
> This project is distributed “AS IS”, without warranty of any kind.  
> Use of third-party services is at your own risk and subject to their respective terms.

---

<div align="center">
Built with ❤️ for the future of human-AI interaction
</div>