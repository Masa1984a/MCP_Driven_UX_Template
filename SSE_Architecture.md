# SSE-Based Cloud MCP Server Architecture

## 概要

MCP (Model Context Protocol) サーバーをGCP Cloud Run上でSSEベースで実装し、将来のOAuth認証およびStreamable HTTP対応への拡張性を持たせたアーキテクチャ設計。

既存のSTDIO版MCPサーバー（`mcp_server.py`）を維持しながら、クラウド版（`cloud_mcp_server.py`）を追加する方式。

## アーキテクチャ図

### PC環境（開発・個人利用）
```
Claude Desktop -<STDIO>-> mcp_server.py -<HTTP>-> API(localhost:8080) -<DB>-> PostgreSQL(local)
```

### クラウド環境（本番・チーム利用）
```
MCP Client -<SSE+APIKey>-> cloud_mcp_server.py(Cloud Run) -<HTTP>-> API(Cloud Run) -<DB>-> PostgreSQL(Cloud SQL)
                              ↑
                        拡張可能な設計
                    - 認証アブストラクション
                    - トランスポートアブストラクション
```

## 設計方針

### 現在の実装
- **PC版**: STDIO + FastMCP（既存維持）
- **クラウド版**: SSE + APIキー認証 + FastAPI
- **コード共有**: 共通ツール実装で重複回避

### 将来の拡張性
- **OAuth 2.0認証**: Google OAuth対応予定
- **Streamable HTTP**: 新しいMCP仕様への移行対応
- **マルチテナント**: 複数組織対応

## 技術スタック

| 層 | PC環境 | クラウド環境 | 説明 |
|---|---|---|---|
| MCP Client | Claude Desktop | Claude Desktop/Web等 | STDIO / SSE対応 |
| MCP Server | Python + FastMCP | Python + FastAPI | STDIO / SSE |
| API Server | Node.js + Express | Node.js + Express | 共通（変更最小限） |
| Database | PostgreSQL | Cloud SQL PostgreSQL | 共通スキーマ |
| Platform | localhost | GCP Cloud Run | 環境分離 |

## ディレクトリ構成

```
/workspace/mcp_server/
├── mcp_server.py              # 既存STDIO版（変更なし）
├── cloud_mcp_server.py        # 新規SSE版（クラウド用）
├── shared/
│   ├── __init__.py
│   ├── tools.py              # 共通ツール実装
│   ├── api_client.py         # 共通API呼び出しロジック
│   └── config.py             # 共通設定管理
├── auth/
│   ├── __init__.py
│   ├── providers.py          # 認証プロバイダー抽象化
│   └── oauth.py             # OAuth実装（将来）
├── transport/
│   ├── __init__.py
│   ├── sse.py               # SSE実装
│   └── streamable_http.py   # Streamable HTTP（将来）
├── requirements.txt          # 既存（STDIO版用）
├── requirements-cloud.txt    # クラウド版追加依存関係
└── Dockerfile               # Cloud Run用
```

## 詳細設計

### 1. 共通コード設計

#### shared/tools.py - ツール実装の共通化
```python
from typing import Dict, Any, Optional, List
from .api_client import APIClient

class TicketTools:
    def __init__(self, api_client: APIClient):
        self.api_client = api_client
    
    async def get_ticket_list(self, **kwargs) -> str:
        """チケット一覧取得（STDIO/SSE共通ロジック）"""
        
    async def get_ticket_detail(self, ticket_id: str) -> str:
        """チケット詳細取得（STDIO/SSE共通ロジック）"""
        
    # 他のツールも同様に実装
```

#### shared/api_client.py - API呼び出しの共通化
```python
import requests
from typing import Dict, Any, Optional

class APIClient:
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url
        self.api_key = api_key
    
    def get_headers(self) -> Dict[str, str]:
        """認証ヘッダー生成"""
        headers = {'Content-Type': 'application/json'}
        if self.api_key:
            headers['x-api-key'] = self.api_key
        return headers
    
    async def get(self, endpoint: str, params: Dict = None) -> Dict[str, Any]:
        """GET リクエスト"""
        
    async def post(self, endpoint: str, data: Dict = None) -> Dict[str, Any]:
        """POST リクエスト"""
```

### 2. 認証アブストラクション層

```python
# auth/providers.py
from abc import ABC, abstractmethod
from typing import Dict, Any
from fastapi import Request

class AuthProvider(ABC):
    @abstractmethod
    async def authenticate(self, request: Request) -> Dict[str, Any]:
        """認証を実行し、ユーザー情報を返す"""
        pass

class APIKeyAuthProvider(AuthProvider):
    """現在の実装：APIキー認証"""
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
    
    async def authenticate(self, request: Request) -> Dict[str, Any]:
        if not self.api_key:
            return {"auth_type": "none", "user": "anonymous"}
        
        api_key = request.headers.get("x-api-key")
        if not api_key or api_key != self.api_key:
            raise HTTPException(401, "Invalid API key")
        
        return {"auth_type": "api_key", "user": "api_key_user"}

class OAuthProvider(AuthProvider):
    """将来の実装：OAuth認証（未実装）"""
    async def authenticate(self, request: Request) -> Dict[str, Any]:
        raise NotImplementedError("OAuth support coming soon")
```

### 3. トランスポートアブストラクション層

```python
# transport/sse.py
from abc import ABC, abstractmethod
from typing import Dict, Any
import asyncio
import uuid
import json
from fastapi import Request
from fastapi.responses import StreamingResponse

class TransportHandler(ABC):
    @abstractmethod
    async def handle_request(self, request: Request, auth_info: Dict[str, Any]):
        pass

class SSETransportHandler(TransportHandler):
    """SSEトランスポート実装"""
    def __init__(self, tools: TicketTools):
        self.tools = tools
        self.sessions = {}
        self.message_queues = {}
    
    async def handle_request(self, request: Request, auth_info: Dict[str, Any]):
        return StreamingResponse(
            self._sse_generator(request, auth_info),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no"  # Cloud Run最適化
            }
        )
    
    async def _sse_generator(self, request: Request, auth_info: Dict[str, Any]):
        session_id = str(uuid.uuid4())
        # SSE実装詳細
```

### 4. クラウド版MCPサーバー

```python
# cloud_mcp_server.py
from fastapi import FastAPI, Request, Depends, HTTPException
from fastapi.responses import StreamingResponse
import os
from shared.tools import TicketTools
from shared.api_client import APIClient
from shared.config import CloudSettings
from auth.providers import APIKeyAuthProvider, AuthProvider
from transport.sse import SSETransportHandler

class CloudMCPServer:
    def __init__(self):
        self.app = FastAPI(title="Cloud MCP Ticket System")
        self.settings = CloudSettings()
        
        # API クライアント初期化
        self.api_client = APIClient(
            base_url=self.settings.api_base_url,
            api_key=self.settings.api_key
        )
        
        # ツール初期化
        self.tools = TicketTools(self.api_client)
        
        # 認証プロバイダー初期化
        self.auth_provider = APIKeyAuthProvider(self.settings.mcp_api_key)
        
        # トランスポートハンドラー初期化
        self.transport_handler = SSETransportHandler(self.tools)
        
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/health")
        async def health_check():
            return {
                "status": "healthy",
                "transport": "sse",
                "auth_enabled": bool(self.settings.mcp_api_key)
            }
        
        @self.app.get("/sse")
        async def sse_endpoint(
            request: Request,
            auth_info: Dict[str, Any] = Depends(self.authenticate)
        ):
            return await self.transport_handler.handle_request(request, auth_info)
    
    async def authenticate(self, request: Request) -> Dict[str, Any]:
        return await self.auth_provider.authenticate(request)

# メイン実行
app = CloudMCPServer().app

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
```

### 5. 既存STDIO版の修正

```python
# mcp_server.py の修正箇所
from shared.tools import TicketTools
from shared.api_client import APIClient

# 既存のツール実装を共通クラスに移行
@mcp.tool(description="Get ticket list - Display list of tickets according to search criteria")
def get_ticket_list(**kwargs) -> str:
    # 共通ツールクラスを呼び出し
    api_client = APIClient(
        base_url=ctx.request_context.lifespan_context.api_base_url,
        api_key=ctx.request_context.lifespan_context.api_key
    )
    tools = TicketTools(api_client)
    return tools.get_ticket_list(**kwargs)
```

## Cloud Run対応設計

### 環境設定管理

```python
# shared/config.py
from pydantic import BaseSettings
from typing import Optional

class CloudSettings(BaseSettings):
    # 基本設定
    api_base_url: str = "http://api:8080"
    api_key: Optional[str] = None
    mcp_api_key: Optional[str] = None
    
    # 将来のOAuth設定
    oauth_enabled: bool = False
    oauth_client_id: Optional[str] = None
    oauth_client_secret: Optional[str] = None
    
    # トランスポート設定
    transport_type: str = "sse"
    
    # Cloud Run最適化
    cloud_run_timeout: int = 840  # 14分
    
    class Config:
        env_file = ".env"
        env_prefix = "MCP_"
```

### Dockerfile

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

# 依存関係インストール
COPY requirements-cloud.txt .
RUN pip install --no-cache-dir -r requirements-cloud.txt

# アプリケーションコピー
COPY . .

# Cloud Run用設定
ENV PORT=8080
EXPOSE 8080

# ヘルスチェック
HEALTHCHECK --interval=30s --timeout=10s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

# 起動コマンド
CMD ["uvicorn", "cloud_mcp_server:app", "--host", "0.0.0.0", "--port", "8080"]
```

### Cloud Run Service設定

```yaml
# gcp-deploy/cloud-run-service.yaml
apiVersion: serving.knative.dev/v1
kind: Service
metadata:
  name: mcp-server
  annotations:
    run.googleapis.com/ingress: all
spec:
  template:
    metadata:
      annotations:
        run.googleapis.com/execution-environment: gen2
        run.googleapis.com/cpu-throttling: "false"  # SSE対応
        autoscaling.knative.dev/minScale: "1"
        autoscaling.knative.dev/maxScale: "10"
    spec:
      containerConcurrency: 1000
      timeoutSeconds: 900  # 15分
      containers:
      - image: gcr.io/PROJECT_ID/mcp-server:latest
        ports:
        - containerPort: 8080
        env:
        - name: MCP_API_BASE_URL
          value: "https://api-service-xxx.run.app"
        - name: MCP_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-secrets
              key: api_key
        - name: MCP_MCP_API_KEY
          valueFrom:
            secretKeyRef:
              name: mcp-secrets
              key: mcp_api_key
        - name: MCP_TRANSPORT_TYPE
          value: "sse"
        resources:
          limits:
            cpu: "1"
            memory: "512Mi"
          requests:
            cpu: "0.5"
            memory: "256Mi"
```

## セキュリティ設計

### 現在の認証
- **PC版**: 認証なし（開発環境）
- **クラウド版**: APIキー認証
- **API間通信**: x-api-key ヘッダー
- **HTTPS強制**: Cloud Runで自動対応

### 将来のOAuth対応
- **Google OAuth 2.0**: 段階的実装
- **スコープ制御**: ユーザー権限管理
- **トークン管理**: JWT セッション

## パフォーマンス設計

### スケーラビリティ
- **Cloud Run**: 自動スケーリング（1-10インスタンス）
- **SSE接続**: 14分リコネクト対応
- **CPU常時割り当て**: リアルタイム性確保

### モニタリング
- **Cloud Logging**: 構造化ログ
- **Cloud Monitoring**: パフォーマンスメトリクス
- **エラー追跡**: 統合ログ分析

## 移行戦略

### Phase 1: 基本SSE実装
1. 共通コード分離
2. cloud_mcp_server.py 実装
3. 基本SSE機能実装

### Phase 2: Cloud Run デプロイ
1. Dockerfile 作成
2. Cloud Run 設定
3. 本番デプロイ

### Phase 3: 認証強化（将来）
1. OAuth プロバイダー実装
2. 認証切り替え機能
3. ユーザー管理

### Phase 4: プロトコル拡張（将来）
1. Streamable HTTP 実装
2. 段階的移行
3. 旧プロトコル廃止

## 運用設計

### デプロイメント
- **開発環境**: PC上でSTDIO版
- **本番環境**: Cloud Run上でSSE版
- **CI/CD**: GitHub Actions

### バックアップ・復旧
- **共通コード**: Git管理
- **設定**: 環境変数 + Secret Manager
- **ログ**: Cloud Logging 長期保存

### コスト最適化
- **予想月額**: ¥2,500-4,200
- **最小インスタンス**: 1（応答性重視）
- **オートスケーリング**: 負荷に応じて調整

## まとめ

このアーキテクチャにより以下を実現：

1. **既存機能保持**: STDIO版は変更なしで継続利用可能
2. **クラウド対応**: SSE版でクラウドネイティブな運用
3. **コード共有**: 重複を避けて保守性向上
4. **将来拡張性**: OAuth・Streamable HTTP への容易な移行
5. **段階的移行**: リスクを最小限に抑えた実装

PC環境での開発利便性を保ちながら、本番環境でのスケーラブルな運用を両立する設計。