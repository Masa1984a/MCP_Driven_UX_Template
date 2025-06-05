# SSE-Based Cloud MCP Server 実装タスクリスト

## 概要

既存STDIO版MCPサーバーを保持しながら、クラウド版SSE MCPサーバーを実装するための詳細タスクリスト。並行作業・中断再開を考慮した精緻なタスク管理。

## 実装方針

- **既存保持**: `mcp_server.py` は変更最小限
- **新規追加**: `cloud_mcp_server.py` をクラウド版として実装
- **コード共有**: 共通ロジックを `shared/` に分離
- **段階的実装**: 基本機能 → 認証強化 → 将来拡張

---

## Phase 1: 基盤設計・共通コード実装

### 1.1 ディレクトリ構成整備
**目的**: プロジェクト構造の整理とファイル配置
**優先度**: 高
**推定工数**: 0.5時間

#### サブタスク
- [ ] `shared/` ディレクトリ作成
- [ ] `auth/` ディレクトリ作成  
- [ ] `transport/` ディレクトリ作成
- [ ] 各ディレクトリに `__init__.py` 作成
- [ ] `requirements-cloud.txt` 作成

#### 実装詳細
```bash
mkdir -p /workspace/mcp_server/shared
mkdir -p /workspace/mcp_server/auth
mkdir -p /workspace/mcp_server/transport
touch /workspace/mcp_server/shared/__init__.py
touch /workspace/mcp_server/auth/__init__.py
touch /workspace/mcp_server/transport/__init__.py
```

#### 完了条件
- ディレクトリ構成が完成
- 各 `__init__.py` が存在
- `requirements-cloud.txt` が作成済み

---

### 1.2 共通設定管理実装
**目的**: STDIO版・SSE版で共有する設定管理
**優先度**: 高
**推定工数**: 1時間
**依存**: 1.1

#### サブタスク
- [ ] `shared/config.py` 実装
  - [ ] `BaseSettings` クラス定義
  - [ ] `CloudSettings` クラス定義
  - [ ] 環境変数マッピング
  - [ ] デフォルト値設定
- [ ] 設定テスト用スクリプト作成

#### 実装詳細
```python
# shared/config.py 実装内容
- BaseSettings (共通設定)
- CloudSettings (クラウド固有設定)
- 環境変数プレフィックス: MCP_
- API_BASE_URL, API_KEY, MCP_API_KEY 等
```

#### 完了条件
- 設定クラスが正常に動作
- 環境変数から設定が読み込み可能
- デフォルト値が適切に設定

---

### 1.3 共通APIクライアント実装
**目的**: API呼び出しロジックの共通化
**優先度**: 高
**推定工数**: 2時間
**依存**: 1.2

#### サブタスク
- [ ] `shared/api_client.py` 実装
  - [ ] `APIClient` クラス定義
  - [ ] `get_headers()` メソッド実装
  - [ ] `get()` メソッド実装（非同期対応）
  - [ ] `post()` メソッド実装（非同期対応）
  - [ ] `put()` メソッド実装（非同期対応）
  - [ ] エラーハンドリング実装
- [ ] APIクライアントのユニットテスト作成

#### 実装詳細
```python
# APIClient の主要メソッド
- __init__(base_url, api_key)
- get_headers() -> Dict[str, str]
- async get(endpoint, params) -> Dict
- async post(endpoint, data) -> Dict
- async put(endpoint, data) -> Dict
- 例外処理: requests.RequestException
```

#### 完了条件
- APIクライアントが正常動作
- 認証ヘッダーが適切に設定
- エラーハンドリングが機能
- ユニットテストがパス

---

### 1.4 共通ツール実装
**目的**: MCPツールロジックの共通化
**優先度**: 高
**推定工数**: 4時間
**依存**: 1.3

#### サブタスク
- [ ] `shared/tools.py` 実装
  - [ ] `TicketTools` クラス定義
  - [ ] `get_ticket_list()` メソッド移植
  - [ ] `get_ticket_detail()` メソッド移植
  - [ ] `create_ticket()` メソッド移植
  - [ ] `update_ticket()` メソッド移植
  - [ ] `add_ticket_history()` メソッド移植
  - [ ] マスターデータ取得メソッド群移植
    - [ ] `get_users()`
    - [ ] `get_accounts()`
    - [ ] `get_categories()`
    - [ ] `get_category_details()`
    - [ ] `get_statuses()`
    - [ ] `get_request_channels()`

#### 実装詳細
```python
# TicketTools クラス構造
class TicketTools:
    def __init__(self, api_client: APIClient)
    
    # チケット操作
    async def get_ticket_list(**kwargs) -> str
    async def get_ticket_detail(ticket_id: str) -> str
    async def create_ticket(**kwargs) -> Dict[str, str]
    async def update_ticket(**kwargs) -> Dict[str, str]
    async def add_ticket_history(**kwargs) -> Dict[str, str]
    
    # マスターデータ
    async def get_users(role: Optional[str]) -> str
    # 他のマスターデータメソッド...
```

#### 完了条件
- 全てのツールメソッドが実装済み
- 既存の`mcp_server.py`と同等の機能
- 非同期対応済み
- エラーハンドリング実装済み

---

## Phase 2: 認証・トランスポート抽象化

### 2.1 認証プロバイダー実装
**目的**: 認証方式の抽象化と拡張性確保
**優先度**: 高
**推定工数**: 2時間
**依存**: 1.2

#### サブタスク
- [ ] `auth/providers.py` 実装
  - [ ] `AuthProvider` 抽象クラス定義
  - [ ] `APIKeyAuthProvider` 実装
  - [ ] `OAuthProvider` スケルトン実装
  - [ ] 認証エラー例外クラス定義
- [ ] 認証プロバイダーのテスト作成

#### 実装詳細
```python
# AuthProvider 抽象インターフェース
class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, request: Request) -> Dict[str, Any]

# APIKeyAuthProvider 実装
- x-api-key ヘッダー検証
- 開発環境での認証スキップ
- ユーザー情報返却

# OAuthProvider (将来実装用)
- NotImplementedError
- インターフェース定義のみ
```

#### 完了条件
- 認証プロバイダーインターフェース定義完了
- APIキー認証が正常動作
- OAuth用インターフェース準備完了
- 認証テストがパス

---

### 2.2 SSEトランスポート実装
**目的**: SSEベースのMCPプロトコル実装
**優先度**: 高
**推定工数**: 6時間
**依存**: 1.4, 2.1

#### サブタスク
- [ ] `transport/sse.py` 実装
  - [ ] `TransportHandler` 抽象クラス定義
  - [ ] `SSETransportHandler` 実装
  - [ ] セッション管理機能
  - [ ] メッセージキュー管理
  - [ ] SSEストリーム生成
  - [ ] MCP プロトコルメッセージ処理
  - [ ] Cloud Run 14分制限対応
- [ ] SSE接続テスト用クライアント作成

#### 実装詳細
```python
# SSETransportHandler 主要機能
class SSETransportHandler(TransportHandler):
    def __init__(self, tools: TicketTools)
    
    # SSE接続処理
    async def handle_request(request, auth_info) -> StreamingResponse
    async def _sse_generator(request, auth_info)
    
    # セッション管理
    sessions: Dict[str, Dict]
    message_queues: Dict[str, asyncio.Queue]
    
    # MCP プロトコル
    async def process_mcp_message(message, auth_info)
    async def handle_initialize(params)
    async def list_tools()
    async def call_tool(params, auth_info)
    
    # Cloud Run 最適化
    - 14分でリコネクト
    - ハートビート送信
    - 適切なヘッダー設定
```

#### 完了条件
- SSE接続が確立可能
- MCPプロトコルメッセージが処理可能
- セッション管理が正常動作
- Cloud Run制限に対応
- テストクライアントで動作確認

---

### 2.3 Streamable HTTP スケルトン実装
**目的**: 将来のStreamable HTTP対応準備
**優先度**: 中
**推定工数**: 1時間
**依存**: 2.2

#### サブタスク
- [ ] `transport/streamable_http.py` 実装
  - [ ] `StreamableHTTPHandler` スケルトンクラス
  - [ ] インターフェース定義
  - [ ] `NotImplementedError` 設定
- [ ] トランスポート切り替え機能準備

#### 実装詳細
```python
# StreamableHTTPHandler (将来実装用)
class StreamableHTTPHandler(TransportHandler):
    async def handle_request(self, request, auth_info):
        raise NotImplementedError("Streamable HTTP coming soon")
```

#### 完了条件
- インターフェース定義完了
- 将来実装への準備完了

---

## Phase 3: クラウド版MCPサーバー実装

### 3.1 クラウド版MCPサーバー本体実装
**目的**: SSE版MCPサーバーのメイン実装
**優先度**: 高
**推定工数**: 3時間
**依存**: 2.2

#### サブタスク
- [ ] `cloud_mcp_server.py` 実装
  - [ ] `CloudMCPServer` クラス定義
  - [ ] FastAPI アプリケーション初期化
  - [ ] 依存関係注入設定
  - [ ] ルーティング設定
  - [ ] ミドルウェア設定
  - [ ] エラーハンドリング
- [ ] 起動スクリプト実装

#### 実装詳細
```python
# CloudMCPServer 構造
class CloudMCPServer:
    def __init__(self):
        # FastAPI アプリ初期化
        # 設定読み込み
        # APIクライアント初期化
        # ツール初期化
        # 認証プロバイダー初期化
        # トランスポートハンドラー初期化
    
    def setup_routes(self):
        # /health エンドポイント
        # /sse エンドポイント
        # /message エンドポイント
        # /capabilities エンドポイント
    
    async def authenticate(self, request) -> Dict[str, Any]
```

#### 完了条件
- FastAPIアプリケーションが起動
- 全エンドポイントが応答
- 認証機能が動作
- エラーハンドリングが機能

---

### 3.2 Docker設定実装
**目的**: Cloud Run デプロイ用Docker設定
**優先度**: 高
**推定工数**: 1時間
**依存**: 3.1

#### サブタスク
- [ ] `Dockerfile` 作成
  - [ ] ベースイメージ選定（python:3.11-slim）
  - [ ] 依存関係インストール
  - [ ] アプリケーションコピー
  - [ ] ポート設定
  - [ ] ヘルスチェック設定
  - [ ] 起動コマンド設定
- [ ] `.dockerignore` 作成
- [ ] ローカルDocker動作確認

#### 実装詳細
```dockerfile
# Dockerfile 主要設定
FROM python:3.11-slim
WORKDIR /app
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt
COPY . .
ENV PORT=8080
EXPOSE 8080
HEALTHCHECK --interval=30s CMD curl -f http://localhost:8080/health
CMD ["uvicorn", "cloud_mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

#### 完了条件
- Dockerイメージがビルド可能
- コンテナが正常起動
- ヘルスチェックが機能
- ローカル環境で動作確認

---

### 3.3 Cloud Run デプロイ設定
**目的**: GCP Cloud Run 用デプロイ設定
**優先度**: 高
**推定工数**: 2時間
**依存**: 3.2

#### サブタスク
- [ ] `gcp-deploy/` ディレクトリ作成
- [ ] Cloud Run Service 設定ファイル作成
  - [ ] `cloud-run-service.yaml`
  - [ ] SSE対応設定
  - [ ] 環境変数設定
  - [ ] リソース制限設定
  - [ ] オートスケーリング設定
- [ ] Secret 設定ファイル作成
- [ ] デプロイスクリプト作成

#### 実装詳細
```yaml
# cloud-run-service.yaml 主要設定
metadata:
  name: mcp-server
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/cpu-throttling: "false"
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 1000
      timeoutSeconds: 900
      containers:
      - image: gcr.io/PROJECT_ID/mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: MCP_API_BASE_URL
        - name: MCP_API_KEY
        - name: MCP_MCP_API_KEY
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
```

#### 完了条件
- Cloud Run設定ファイル完成
- Secret設定ファイル完成
- デプロイスクリプト動作確認

---

## Phase 4: 既存STDIO版の更新

### 4.1 既存STDIO版の共通コード対応
**目的**: STDIO版でも共通コードを利用
**優先度**: 中
**推定工数**: 3時間
**依存**: 1.4

#### サブタスク
- [ ] `mcp_server.py` の修正
  - [ ] 共通ツールクラスのインポート
  - [ ] 各ツール関数の共通クラス呼び出しに変更
  - [ ] Context から APIClient 初期化
  - [ ] 非同期対応（必要に応じて）
- [ ] STDIO版動作確認
- [ ] 既存機能の回帰テスト

#### 実装詳細
```python
# mcp_server.py 修正例
from shared.tools import TicketTools
from shared.api_client import APIClient

@mcp.tool(description="...")
def get_ticket_list(**kwargs) -> str:
    api_client = APIClient(
        base_url=ctx.request_context.lifespan_context.api_base_url,
        api_key=ctx.request_context.lifespan_context.api_key
    )
    tools = TicketTools(api_client)
    # 非同期の場合は asyncio.run() 使用
    return asyncio.run(tools.get_ticket_list(**kwargs))
```

#### 完了条件
- STDIO版が共通コードを利用
- 既存機能に影響なし
- Claude Desktop での動作確認完了

---

## Phase 5: デプロイ・運用設定

### 5.1 GCP リソース作成スクリプト
**目的**: GCP環境の自動構築
**優先度**: 中
**推定工数**: 2時間
**依存**: 3.3

#### サブタスク
- [ ] `gcp-deploy/setup-gcp.sh` 作成
  - [ ] Cloud SQL インスタンス作成
  - [ ] Secret Manager 設定
  - [ ] IAM 設定
  - [ ] Container Registry 設定
- [ ] `gcp-deploy/deploy.sh` 作成
  - [ ] Docker イメージビルド・プッシュ
  - [ ] Cloud Run デプロイ
  - [ ] 環境変数設定
- [ ] 設定ファイルテンプレート作成

#### 実装詳細
```bash
# setup-gcp.sh 主要コマンド
gcloud sql instances create mcp-postgres
gcloud secrets create api-key
gcloud secrets create mcp-api-key
gcloud run deploy mcp-server

# deploy.sh 主要コマンド
docker build -t gcr.io/PROJECT_ID/mcp-server .
docker push gcr.io/PROJECT_ID/mcp-server
gcloud run deploy mcp-server --image gcr.io/PROJECT_ID/mcp-server
```

#### 完了条件
- GCP リソース作成スクリプト完成
- デプロイスクリプト完成
- ドキュメント整備

---

### 5.2 モニタリング・ログ設定
**目的**: 運用監視体制の構築
**優先度**: 低
**推定工数**: 2時間
**依存**: 5.1

#### サブタスク
- [ ] 構造化ログ実装
  - [ ] Python logging 設定
  - [ ] JSON フォーマット対応
  - [ ] リクエストID 追跡
- [ ] Cloud Monitoring 設定
  - [ ] カスタムメトリクス定義
  - [ ] アラート設定
  - [ ] ダッシュボード作成
- [ ] エラー追跡設定

#### 実装詳細
```python
# 構造化ログ設定
import structlog
logger = structlog.get_logger()

# メトリクス例
- SSE 接続数
- API レスポンス時間
- エラー率
- リクエスト数
```

#### 完了条件
- 構造化ログが出力
- Cloud Monitoring で監視可能
- アラートが設定済み

---

### 5.3 ドキュメント作成
**目的**: 運用・保守ドキュメントの整備
**優先度**: 低
**推定工数**: 3時間
**依存**: 5.2

#### サブタスク
- [ ] デプロイメントガイド作成
  - [ ] GCP 環境構築手順
  - [ ] 初回デプロイ手順
  - [ ] 更新デプロイ手順
- [ ] 運用ガイド作成
  - [ ] 監視項目・対応手順
  - [ ] トラブルシューティング
  - [ ] ログ確認方法
- [ ] 開発者ガイド作成
  - [ ] ローカル開発環境構築
  - [ ] テスト実行方法
  - [ ] コントリビューション方法

#### 完了条件
- 全ドキュメント作成完了
- 第三者がデプロイ可能なレベル
- トラブルシューティング網羅

---

## Phase 6: 将来拡張準備

### 6.1 OAuth 実装準備
**目的**: 将来のOAuth実装のための基盤整備
**優先度**: 低
**推定工数**: 2時間
**依存**: 2.1

#### サブタスク
- [ ] `auth/oauth.py` スケルトン実装
- [ ] Google OAuth 2.0 設定調査
- [ ] OAuth フロー設計
- [ ] 設定項目追加

#### 完了条件
- OAuth実装の準備完了
- 設計ドキュメント作成完了

---

### 6.2 テスト体制整備
**目的**: 継続的な品質保証体制構築
**優先度**: 低
**推定工数**: 4時間
**依存**: 全Phase

#### サブタスク
- [ ] ユニットテスト拡充
- [ ] 統合テスト作成
- [ ] E2Eテスト作成
- [ ] CI/CD パイプライン設定

#### 完了条件
- テストカバレッジ80%以上
- CI/CD パイプライン稼働

---

## 実装スケジュール

### 推奨実装順序
1. **Phase 1**: 基盤設計・共通コード（8時間）
2. **Phase 2**: 認証・トランスポート（9時間）
3. **Phase 3**: クラウド版実装（6時間）
4. **Phase 4**: STDIO版更新（3時間）
5. **Phase 5**: デプロイ・運用（7時間）
6. **Phase 6**: 将来拡張準備（6時間）

### 並行実施可能タスク
- Phase 1 と Phase 5.3（ドキュメント作成）
- Phase 2.3 と Phase 6.1（将来拡張準備）
- Phase 4 と Phase 5.1（GCP設定）

### 中断・再開対応
- 各サブタスクは独立性を保つ
- 完了条件を明確に定義
- テストコードで動作確認可能

---

## リスク管理

### 技術リスク
- **Cloud Run 15分制限**: SSE リコネクト機能で対応
- **認証実装複雑性**: 段階的実装で複雑性を分散
- **既存機能影響**: 共通コード化での回帰テスト必須

### スケジュールリスク
- **Phase 2**: SSE実装が最も複雑、十分な時間確保必要
- **Phase 3**: Cloud Run特有の設定が必要、GCP知識必須
- **Phase 4**: 既存コードへの影響、慎重な実装必要

### 対策
- 各Phaseでの動作確認を徹底
- ロールバック可能な実装方式
- 十分なテストとドキュメント整備