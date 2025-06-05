# GCP Cloud Run MCP Server Deployment Guide

この資料では、MCP Server を GCP Cloud Run にデプロイする手順を説明します。

## 📋 前提条件

### 必要なツール
- **Google Cloud CLI (gcloud)**: 最新版
- **Docker**: 20.10以上
- **Git**: 2.0以上

### GCPアカウント設定
- GCPプロジェクト作成済み
- 請求先アカウント設定済み
- 必要なIAM権限（Cloud Run Developer, Cloud Build Editor, Secret Manager Admin）

## 🚀 デプロイ手順

### 1. 環境準備

```bash
# Google Cloud CLI のインストール (Windows)
# https://cloud.google.com/sdk/docs/install-sdk からダウンロード

# 認証
gcloud auth login
gcloud auth application-default login

# プロジェクト設定
export PROJECT_ID="your-project-id"
gcloud config set project $PROJECT_ID
```

### 2. 必要なAPIの有効化

```bash
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable containerregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
```

### 3. 秘密情報の設定

```bash
# API キーの設定
echo -n "your-api-key" | gcloud secrets create mcp-api-key --data-file=-

# API ベース URL の設定
echo -n "https://your-api-server.com" | gcloud secrets create mcp-api-base-url --data-file=-

# MCP API キーの設定
echo -n "your-mcp-api-key" | gcloud secrets create mcp-mcp-api-key --data-file=-
```

### 4. サービスアカウントの作成

```bash
# サービスアカウント作成
gcloud iam service-accounts create mcp-server-sa \
    --display-name="MCP Server Service Account" \
    --description="Service account for MCP Server on Cloud Run"

# 秘密管理者権限付与
gcloud projects add-iam-policy-binding $PROJECT_ID \
    --member="serviceAccount:mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/secretmanager.secretAccessor"
```

### 5. 自動デプロイ（推奨）

```bash
# mcp_server ディレクトリに移動
cd mcp_server

# デプロイスクリプト実行
chmod +x deploy.sh
./deploy.sh
```

### 6. 手動デプロイ

```bash
# イメージビルド
docker build -t gcr.io/$PROJECT_ID/mcp-server:latest .

# イメージプッシュ
docker push gcr.io/$PROJECT_ID/mcp-server:latest

# Cloud Run デプロイ
gcloud run deploy mcp-server \
    --image=gcr.io/$PROJECT_ID/mcp-server:latest \
    --region=asia-northeast1 \
    --platform=managed \
    --allow-unauthenticated \
    --memory=512Mi \
    --cpu=1 \
    --min-instances=0 \
    --max-instances=10 \
    --timeout=900s \
    --concurrency=100 \
    --set-env-vars="MCP_CLOUD_MODE=true,MCP_LOG_LEVEL=INFO,MCP_AUTH_PROVIDER=api_key" \
    --set-secrets="MCP_API_KEY=mcp-api-key:latest,MCP_API_BASE_URL=mcp-api-base-url:latest,MCP_MCP_API_KEY=mcp-mcp-api-key:latest" \
    --service-account="mcp-server-sa@$PROJECT_ID.iam.gserviceaccount.com"
```

## 🔧 設定オプション

### 環境変数
| 変数名 | デフォルト | 説明 |
|--------|------------|------|
| `MCP_CLOUD_MODE` | `true` | クラウドモード有効化 |
| `MCP_HOST` | `0.0.0.0` | バインドホスト |
| `MCP_PORT` | `8080` | リスンポート |
| `MCP_LOG_LEVEL` | `INFO` | ログレベル |
| `MCP_AUTH_PROVIDER` | `api_key` | 認証プロバイダー |
| `MCP_TRANSPORT_TYPE` | `sse` | トランスポートタイプ |
| `MCP_CLOUD_RUN_TIMEOUT` | `840` | タイムアウト（秒） |

### 秘密情報
| シークレット名 | 説明 |
|----------------|------|
| `mcp-api-key` | バックエンドAPI認証キー |
| `mcp-api-base-url` | バックエンドAPI URL |
| `mcp-mcp-api-key` | MCP クライアント認証キー |

## 📊 監視とメンテナンス

### ログ確認
```bash
# リアルタイムログ
gcloud logs tail --service=mcp-server

# 過去のログ
gcloud logs read --service=mcp-server --limit=100
```

### メトリクス確認
```bash
# Cloud Console でメトリクス確認
https://console.cloud.google.com/run/detail/asia-northeast1/mcp-server
```

### ヘルスチェック
```bash
# サービス URL 取得
SERVICE_URL=$(gcloud run services describe mcp-server --region=asia-northeast1 --format="value(status.url)")

# ヘルスチェック
curl $SERVICE_URL/health

# API 確認
curl $SERVICE_URL/
```

## 🔄 継続的デプロイ

### Cloud Build トリガー設定
1. Cloud Console で Cloud Build > トリガー
2. 新しいトリガー作成
3. GitHub/Cloud Source Repositories 連携
4. `cloudbuild.yaml` 指定
5. トリガー条件設定（push to main branch など）

### ローカル開発とテスト
```bash
# ローカル環境でテスト
cd mcp_server
export MCP_CLOUD_MODE=false
python cloud_mcp_server.py

# Dockerでテスト
docker build -t mcp-server-local .
docker run -p 8080:8080 \
    -e MCP_API_BASE_URL=http://host.docker.internal:8080 \
    mcp-server-local
```

## 🛡️ セキュリティ設定

### IAM 最小権限設定
```bash
# Cloud Run Invoker 権限（必要に応じて）
gcloud run services add-iam-policy-binding mcp-server \
    --member="user:your-email@example.com" \
    --role="roles/run.invoker" \
    --region=asia-northeast1
```

### VPC設定（オプション）
```bash
# VPC Connector 作成（必要に応じて）
gcloud compute networks vpc-access connectors create mcp-connector \
    --network=default \
    --range=10.8.0.0/28 \
    --region=asia-northeast1

# Cloud Run でVPC使用
gcloud run deploy mcp-server \
    --vpc-connector=mcp-connector \
    --vpc-egress=private-ranges-only \
    # ... 他のオプション
```

## 📈 パフォーマンス最適化

### リソース設定
- **CPU**: 1 vCPU（軽負荷）～ 2 vCPU（高負荷）
- **Memory**: 512Mi（推奨）～ 1Gi（高負荷）
- **Concurrency**: 100（デフォルト）～ 1000（高負荷）
- **Min instances**: 0（コスト重視）～ 1（レスポンス重視）

### スケーリング設定
```bash
# オートスケーリング設定更新
gcloud run services update mcp-server \
    --min-instances=1 \
    --max-instances=20 \
    --region=asia-northeast1
```

## 🚨 トラブルシューティング

### よくある問題

1. **デプロイ失敗**
   ```bash
   # Cloud Build ログ確認
   gcloud builds list --limit=5
   gcloud builds log BUILD_ID
   ```

2. **アプリケーション起動失敗**
   ```bash
   # Cloud Run ログ確認
   gcloud logs read --service=mcp-server --limit=50
   ```

3. **SSE 接続問題**
   - Cloud Run は 15分でタイムアウト
   - クライアント側で再接続実装が必要

4. **認証エラー**
   ```bash
   # 秘密情報確認
   gcloud secrets versions access latest --secret=mcp-api-key
   ```

### デバッグ手順
1. ヘルスチェックエンドポイント確認
2. アプリケーションログ確認
3. 環境変数・秘密情報確認
4. ネットワーク接続確認
5. リソース使用量確認

## 💰 コスト最適化

### 推奨設定（コスト重視）
- Min instances: 0
- Memory: 512Mi
- CPU: 1
- Request timeout: 900s

### コスト見積もり
- **軽負荷**: 月額 $5-20
- **中負荷**: 月額 $20-100
- **高負荷**: 月額 $100-500

## 📚 参考資料

- [Cloud Run ドキュメント](https://cloud.google.com/run/docs)
- [Cloud Build ドキュメント](https://cloud.google.com/build/docs)
- [Secret Manager ドキュメント](https://cloud.google.com/secret-manager/docs)
- [MCP プロトコル仕様](https://spec.modelcontextprotocol.io/)

## 🔄 アップデート手順

### アプリケーション更新
```bash
# 新バージョンデプロイ
gcloud builds submit --config=cloudbuild.yaml

# ローリングアップデート確認
gcloud run revisions list --service=mcp-server --region=asia-northeast1
```

### 設定更新
```bash
# 環境変数更新
gcloud run services update mcp-server \
    --set-env-vars="MCP_LOG_LEVEL=DEBUG" \
    --region=asia-northeast1

# 秘密情報更新
echo -n "new-api-key" | gcloud secrets versions add mcp-api-key --data-file=-
```