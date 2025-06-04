# Google Cloud Platform Deployment Guide for MCP Driven UX Template

## Overview
This guide provides step-by-step instructions for deploying the MCP Driven UX Template to Google Cloud Platform (GCP). The template consists of a Node.js API server with PostgreSQL database, designed to work with Claude Desktop via Model Context Protocol (MCP).

### Key Features
- **Environment Variable-Based Configuration**: All GCP resources use consistent naming with a configurable prefix
- **Automated Resource Management**: gcloud CLI commands for streamlined deployment
- **Secure Credential Management**: Google Secret Manager integration for secrets
- **Claude Desktop Integration**: Complete MCP Server setup for AI-powered ticket management

## Architecture Overview

The MCP Driven UX Template implements a modern microservices architecture optimized for Google Cloud Platform:

```
┌─────────────────┐
│ Claude Desktop  │
└────────┬────────┘
         │ MCP Protocol
┌────────▼────────┐
│  MCP Server     │ (Python)
│  Port: Dynamic  │
└────────┬────────┘
         │ HTTP/REST
┌────────▼────────┐
│  API Server     │ (Node.js/TypeScript)
│  Port: 8080     │ (Cloud Run)
└────────┬────────┘
         │ SQL
┌────────▼────────┐
│  PostgreSQL     │ (Cloud SQL)
│  Port: 5432     │
└─────────────────┘
```

### GCP Service Mapping

| Component | GCP Service | Purpose |
|-----------|-------------|---------|
| Container Registry | Google Artifact Registry | Docker image storage |
| Secret Management | Google Secret Manager | Secure credential storage |
| API Hosting | Google Cloud Run | Serverless API server hosting |
| Database | Google Cloud SQL (PostgreSQL) | Managed PostgreSQL database |
| Authentication | Service Account | Inter-service authentication |

### Technology Stack

**Backend Components:**
- **MCP Server**: Python 3.9+ with FastMCP framework
- **API Server**: Node.js 18+ with TypeScript, Express.js, PgTyped
- **Database**: PostgreSQL 16 with mcp_ux schema

**Infrastructure:**
- Docker containerization
- Environment variable-based configuration
- API Key authentication
- Automatic scaling with Cloud Run

## Prerequisites
- **Google Cloud Subscription**: Active GCP project with billing enabled
- **Required Tools**: Google Cloud SDK (gcloud), PowerShell 5.1+, Docker, PostgreSQL client (psql)
- **Naming Convention**: All resource names are generated from a configurable `$PREFIX` variable to ensure consistency
- **Security**: API keys and passwords are automatically generated and stored in Google Secret Manager

---

## 0. Existing Environment Cleanup

### 0.1 Check Existing Resources

現在のプロジェクトと既存リソースを確認します：

```powershell
# 現在のプロジェクトを確認
gcloud config get-value project

# 既存のサービスアカウントを確認
gcloud iam service-accounts list

# 利用可能な課金アカウントを確認
gcloud beta billing accounts list

# 現在のプロジェクトの課金状態を確認（PROJECT_IDを実際の値に置き換え）
gcloud beta billing projects describe $PROJECT_ID
```

### 0.2 Clean Up Existing Resources (Optional)

既存のサービスアカウントを削除する場合：

```powershell
# 不要なサービスアカウントの削除（必要な場合のみ）
# gcloud iam service-accounts delete [SERVICE_ACCOUNT_EMAIL] --quiet
```

---

## 1. Initial Setup

### 1.1 Environment Variables Configuration

プロジェクト全体で使用する環境変数を設定します：

```powershell
# プロジェクトの基本設定
$PROJECT_ID = "your-gcp-project-id"
$REGION = "asia-northeast1"
$ZONE = "asia-northeast1-a"

# リソース名のプレフィックス
$PREFIX = "your-project-name"

# 各リソース名
$ARTIFACT_REGISTRY_REPO = "$PREFIX-repo"
$CLOUD_SQL_INSTANCE = "$PREFIX-db"
$CLOUD_RUN_SERVICE = "$PREFIX-api"
$SERVICE_ACCOUNT_NAME = "$PREFIX-sa"

# 設定内容を確認
Write-Host "=== 環境設定 ===" -ForegroundColor Cyan
Write-Host "PROJECT_ID: $PROJECT_ID"
Write-Host "REGION: $REGION"
Write-Host "ZONE: $ZONE"
Write-Host "PREFIX: $PREFIX"
Write-Host "ARTIFACT_REGISTRY_REPO: $ARTIFACT_REGISTRY_REPO"
Write-Host "CLOUD_SQL_INSTANCE: $CLOUD_SQL_INSTANCE"
Write-Host "CLOUD_RUN_SERVICE: $CLOUD_RUN_SERVICE"
Write-Host "SERVICE_ACCOUNT_NAME: $SERVICE_ACCOUNT_NAME"
```

### 1.2 Local Environment Verification

必要なツールがインストールされているか確認します：

```powershell
# Google Cloud SDK
gcloud --version

# Docker
docker --version

# PowerShell
$PSVersionTable.PSVersion

# PostgreSQL client
psql --version
```

### 1.3 Google Cloud Project Setup

```powershell
# 現在のプロジェクトを設定
gcloud config set project $PROJECT_ID

# デフォルトリージョン/ゾーンを設定
gcloud config set compute/region $REGION
gcloud config set compute/zone $ZONE

# 設定を確認
gcloud config list
```

### 1.4 Enable Billing

```powershell
# 利用可能な課金アカウントを確認
$BILLING_ACCOUNTS = gcloud beta billing accounts list --format="value(name)"
Write-Host "Available billing accounts:"
Write-Host $BILLING_ACCOUNTS

# 課金アカウントをプロジェクトにリンク（BILLING_ACCOUNT_IDを実際の値に置き換えてください）
# 例: gcloud beta billing projects link $PROJECT_ID --billing-account=01234-56789-ABCDEF
```

**重要**: 上記のコマンドで表示された課金アカウントIDを使用して、以下のコマンドを実行してください：

```powershell
# 実際の課金アカウントIDに置き換えて実行
gcloud beta billing projects link $PROJECT_ID --billing-account=[YOUR_BILLING_ACCOUNT_ID]
```

### 1.5 Enable Required APIs

```powershell
# 必要なAPIを有効化
gcloud services enable cloudresourcemanager.googleapis.com
gcloud services enable sqladmin.googleapis.com
gcloud services enable run.googleapis.com
gcloud services enable artifactregistry.googleapis.com
gcloud services enable secretmanager.googleapis.com
gcloud services enable cloudbuild.googleapis.com
gcloud services enable compute.googleapis.com
gcloud services enable servicenetworking.googleapis.com

# 有効化されたAPIを確認
gcloud services list --enabled
```

---

## 2. Generate Required Credentials

### 2.1 Authentication Information Generation

```powershell
# API Keyの生成
$API_KEY = "mcp_api_" + [guid]::NewGuid().ToString()
Write-Host "Generated API Key: $API_KEY" -ForegroundColor Green

# データベースパスワードの生成（特殊文字を制限）
$DB_PASSWORD = -join ((65..90) + (97..122) + (48..57) + (33,35,36,37,42,43,45,61,64,95) | Get-Random -Count 16 | ForEach-Object {[char]$_})
Write-Host "Generated DB Password: $DB_PASSWORD" -ForegroundColor Green

# 生成した値を環境変数として保存
$env:API_KEY = $API_KEY
$env:DB_PASSWORD = $DB_PASSWORD

# 後で参照できるようにファイルに保存（セキュリティに注意）
@"
API_KEY=$API_KEY
DB_PASSWORD=$DB_PASSWORD
"@ | Out-File -FilePath "credentials.txt" -Encoding UTF8
Write-Host "Credentials saved to credentials.txt (DO NOT COMMIT THIS FILE)" -ForegroundColor Yellow
```

### 2.2 Register Secrets to Secret Manager

```powershell
# API Keyの登録
Write-Output -n $API_KEY | gcloud secrets create api-key --data-file=-

# データベースパスワードの登録
Write-Output -n $DB_PASSWORD | gcloud secrets create db-password --data-file=-

# MCP API Keyの登録（同じ値）
Write-Output -n $API_KEY | gcloud secrets create mcp-api-key --data-file=-

# 登録されたシークレットを確認
gcloud secrets list
```

---

## 3. Network and Security Configuration

### 3.1 Create Service Account

```powershell
# Cloud Run用サービスアカウントを作成
gcloud iam service-accounts create $SERVICE_ACCOUNT_NAME `
    --display-name="MCP UX Service Account" `
    --description="Service account for MCP UX Cloud Run services"

# サービスアカウントのメールアドレスを取得
$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"
Write-Host "Service Account Email: $SERVICE_ACCOUNT_EMAIL" -ForegroundColor Green

# 環境変数に保存
$env:SERVICE_ACCOUNT_EMAIL = $SERVICE_ACCOUNT_EMAIL
```

### 3.2 Configure IAM Permissions

```powershell
# Cloud SQL Client権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
    --role="roles/cloudsql.client"

# Secret Manager Accessor権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member="serviceAccount:$SERVICE_ACCOUNT_EMAIL" `
    --role="roles/secretmanager.secretAccessor"

# Cloud Build サービスアカウントを設定（プロジェクト番号を取得）
$PROJECT_NUMBER = gcloud projects describe $PROJECT_ID --format="value(projectNumber)"
$CLOUD_BUILD_SA = "serviceAccount:$PROJECT_NUMBER@cloudbuild.gserviceaccount.com"
Write-Host "Cloud Build Service Account: $CLOUD_BUILD_SA" -ForegroundColor Green

# Cloud Build サービスアカウントに権限を付与
gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member=$CLOUD_BUILD_SA `
    --role="roles/artifactregistry.writer"

gcloud projects add-iam-policy-binding $PROJECT_ID `
    --member=$CLOUD_BUILD_SA `
    --role="roles/run.developer"
```

---

## 4. Database (Cloud SQL) Setup

### 4.1 Create Cloud SQL Instance

```powershell
# PostgreSQL インスタンスを作成（これには数分かかります）
Write-Host "Creating Cloud SQL instance... This may take 5-10 minutes" -ForegroundColor Yellow

gcloud sql instances create $CLOUD_SQL_INSTANCE `
    --database-version=POSTGRES_16 `
    --tier=db-perf-optimized-N-2 `
    --region=$REGION `
    --assign-ip `
    --authorized-networks=0.0.0.0/0 `
    --root-password=$DB_PASSWORD

# インスタンスの状態を確認
gcloud sql instances describe $CLOUD_SQL_INSTANCE --format="value(state)"

# インスタンスのパブリックIPアドレスを取得
$DB_HOST = gcloud sql instances describe $CLOUD_SQL_INSTANCE --format="value(ipAddresses[0].ipAddress)"
Write-Host "Database Host IP: $DB_HOST" -ForegroundColor Green
$env:DB_HOST = $DB_HOST
```

### 4.2 Create Database and User

```powershell
# データベースを作成
gcloud sql databases create mcp_ux --instance=$CLOUD_SQL_INSTANCE

# データベースユーザーを作成
gcloud sql users create pgadmin `
    --instance=$CLOUD_SQL_INSTANCE `
    --password=$DB_PASSWORD

# 作成されたデータベースとユーザーを確認
gcloud sql databases list --instance=$CLOUD_SQL_INSTANCE
gcloud sql users list --instance=$CLOUD_SQL_INSTANCE
```

### 4.3 Initialize Database

```powershell
# PostgreSQL接続環境変数を設定
$env:PGPASSWORD = $DB_PASSWORD

# Windows環境でのエンコーディング対策
# UTF-8を明示的に指定して初期化SQLを実行
$env:PGCLIENTENCODING = "UTF8"
psql -h $DB_HOST -p 5432 -U pgadmin -d mcp_ux -c "SET client_encoding TO 'UTF8';" -f db\init\ja\init.sql

# テーブルが作成されたことを確認
psql -h $DB_HOST -p 5432 -U pgadmin -d mcp_ux -c "SELECT tablename FROM pg_tables WHERE schemaname = 'mcp_ux' ORDER BY tablename;"

# サンプルデータの確認
psql -h $DB_HOST -p 5432 -U pgadmin -d mcp_ux -c "SET search_path TO mcp_ux; SELECT COUNT(*) as total_records FROM accounts;"
```

---

## 5. Container Registry Configuration

### 5.1 Create Artifact Registry Repository

```powershell
# Artifact Registry リポジトリを作成
gcloud artifacts repositories create $ARTIFACT_REGISTRY_REPO `
    --repository-format=docker `
    --location=$REGION `
    --description="MCP UX Docker images"

# リポジトリURLを構築
$REPOSITORY_URL = "$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO"
Write-Host "Repository URL: $REPOSITORY_URL" -ForegroundColor Green
$env:REPOSITORY_URL = $REPOSITORY_URL

# リポジトリを確認
gcloud artifacts repositories list --location=$REGION
```

### 5.2 Configure Docker Authentication

```powershell
# Docker認証を設定
gcloud auth configure-docker $REGION-docker.pkg.dev

# 認証が成功したことを確認
docker images
```

---

## 6. Application Build and Deploy

### 6.1 Build API Server Docker Image

```powershell
# APIディレクトリに移動
cd api

# 依存関係をインストール
npm ci

# TypeScriptをビルド
npm run build:ci

# Dockerイメージをビルド
docker build -t "$REPOSITORY_URL/api-server:latest" .
docker tag "$REPOSITORY_URL/api-server:latest" "$REPOSITORY_URL/api-server:v1.0"

# ビルドされたイメージを確認
docker images | Select-String $ARTIFACT_REGISTRY_REPO
```

### 6.2 Push Images to Artifact Registry

```powershell
# イメージをプッシュ
docker push "$REPOSITORY_URL/api-server:latest"
docker push "$REPOSITORY_URL/api-server:v1.0"

# プッシュされたイメージを確認
gcloud artifacts docker images list $REPOSITORY_URL

# プロジェクトルートに戻る
cd ..
```

### 6.3 Deploy to Cloud Run

```powershell
# Cloud Runサービスをデプロイ
Write-Host "Deploying to Cloud Run..." -ForegroundColor Yellow

# 注意: 環境変数はすべて --set-env-vars で一度に設定する必要があります
# SECRET の参照に問題がある場合は、環境変数として直接設定します
gcloud run deploy $CLOUD_RUN_SERVICE `
    --image=$REPOSITORY_URL/api-server:latest `
    --platform=managed `
    --region=$REGION `
    --service-account=$SERVICE_ACCOUNT_EMAIL `
    --set-env-vars="NODE_ENV=production,LOG_LEVEL=info,DB_HOST=$DB_HOST,DB_PORT=5432,DB_NAME=mcp_ux,DB_USER=pgadmin,DB_PASSWORD=$DB_PASSWORD,API_KEY=$API_KEY" `
    --allow-unauthenticated `
    --port=8080 `
    --memory=512Mi `
    --cpu=1

# サービスURLを取得
$SERVICE_URL = gcloud run services describe $CLOUD_RUN_SERVICE --platform=managed --region=$REGION --format="value(status.url)"
Write-Host "Service URL: $SERVICE_URL" -ForegroundColor Green
$env:SERVICE_URL = $SERVICE_URL
```

---

## 7. Deployment Verification

### 7.1 Health Check

```powershell
# ヘルスチェックエンドポイントを確認
$healthUrl = "$SERVICE_URL/health"
Write-Host "Testing health endpoint: $healthUrl" -ForegroundColor Yellow

curl -v "$healthUrl"
```

### 7.2 API Testing

```powershell
# APIキーなしでアクセス（401エラーを期待）
Write-Host "Testing without API key (expecting 401 error)..." -ForegroundColor Yellow
curl -v "$SERVICE_URL/tickets"

# APIキーありでアクセス
Write-Host "`nTesting with API key..." -ForegroundColor Yellow
curl -v -H "x-api-key: $API_KEY" "$SERVICE_URL/tickets"
```

### 7.3 Check Logs

```powershell
# Cloud Runのログを確認
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$CLOUD_RUN_SERVICE" --limit=50 --format=json | ConvertFrom-Json | ForEach-Object { 
    Write-Host "[$($_.timestamp)] $($_.jsonPayload.message)" -ForegroundColor Cyan 
}
```

---

## 8. MCP Server Configuration and Claude Desktop Integration

### 8.1 Create MCP Server Configuration File

```powershell
# mcp_server/.envファイルを作成
$envContent = @"
# MCP Server Configuration for GCP API

# API Server URL
API_BASE_URL=$SERVICE_URL

# Environment mode
NODE_ENV=production

# API Key for authentication
API_KEY=$API_KEY

# Logging
LOG_LEVEL=INFO
"@

# ファイルに出力
$envContent | Out-File -FilePath "mcp_server\.env" -Encoding UTF8

# 設定内容を確認
Write-Host "=== mcp_server/.env content ===" -ForegroundColor Cyan
Get-Content mcp_server\.env
```

### 8.2 Create Claude Desktop Configuration File

```powershell
# mcp_serverディレクトリの絶対パスを取得
$MCP_SERVER_PATH = Join-Path (Get-Location).Path "mcp_server"
Write-Host "MCP Server path: $MCP_SERVER_PATH" -ForegroundColor Green

# Windowsのパス区切り文字をエスケープ（\を\\に変換）
$MCP_SERVER_PATH_ESCAPED = $MCP_SERVER_PATH.Replace('\', '\\')

# Claude Desktop設定ファイルを作成
$configContent = @"
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "$MCP_SERVER_PATH_ESCAPED",
        "run",
        "mcp_server.py"
      ],
      "env": {
        "API_BASE_URL": "$SERVICE_URL",
        "API_KEY": "$API_KEY",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
"@

$configContent | Out-File -FilePath "claude_desktop_config_gcp.json" -Encoding UTF8

# 設定内容を確認
Write-Host "=== claude_desktop_config_gcp.json content ===" -ForegroundColor Cyan
Get-Content claude_desktop_config_gcp.json
```

### 8.3 MCP Server Testing

```powershell
# mcp_serverディレクトリに移動
cd mcp_server

# uvをインストール（未インストールの場合）
pip install uv

# 依存関係をインストール
uv pip install -r requirements.txt

# プロジェクトルートに戻る
cd ..

# 環境変数を設定してMCP Serverをテスト
$env:API_BASE_URL = $SERVICE_URL
$env:API_KEY = $API_KEY
$env:LOG_LEVEL = "INFO"

# MCP Serverの起動テスト（Ctrl+Cで終了）
Write-Host "Starting MCP Server test... Press Ctrl+C to stop" -ForegroundColor Yellow
python mcp_server/mcp_server.py
```

### 8.4 Claude Desktop Configuration

1. **設定ファイルの配置**
   ```powershell
   # Claude Desktopの設定ディレクトリパスを表示
   Write-Host "Claude Desktop設定ファイルを以下の場所にコピーしてください:" -ForegroundColor Yellow
   Write-Host "Windows: %APPDATA%\Claude\claude_desktop_config.json" -ForegroundColor Cyan
   
   # Windowsの場合の自動コピー
   Copy-Item claude_desktop_config_gcp.json "$env:APPDATA\Claude\claude_desktop_config.json" -Force
   Write-Host "Configuration file copied successfully!" -ForegroundColor Green
   ```

2. **Claude Desktopの再起動**
   - Claude Desktopを完全に終了
   - 再起動して設定を反映

3. **接続テスト**
   Claude Desktopで以下のような質問をしてテストします：
   ```
   チケット一覧を表示してください
   ```

---

## 9. Operations Configuration

### 9.1 Backup Configuration

```powershell
# Cloud SQLの自動バックアップを設定
gcloud sql instances patch $CLOUD_SQL_INSTANCE `
    --backup-start-time=03:00 `
    --retained-backups-count=7 `
    --retained-transaction-log-days=7

# バックアップ設定を確認
gcloud sql instances describe $CLOUD_SQL_INSTANCE --format="yaml(settings.backupConfiguration)"
```

### 9.2 Monitoring Configuration

```powershell
# Cloud Runのメトリクスを確認
Write-Host "Cloud Run service metrics URL:" -ForegroundColor Yellow
Write-Host "https://console.cloud.google.com/run/detail/$REGION/$CLOUD_RUN_SERVICE/metrics?project=$PROJECT_ID" -ForegroundColor Cyan

# Cloud SQLのメトリクスを確認
Write-Host "`nCloud SQL instance metrics URL:" -ForegroundColor Yellow
Write-Host "https://console.cloud.google.com/sql/instances/$CLOUD_SQL_INSTANCE/overview?project=$PROJECT_ID" -ForegroundColor Cyan
```

---

## 10. Troubleshooting

### 10.1 Common Issues and Solutions

1. **Cloud Runサービスが起動しない場合**
   ```powershell
   # サービスの詳細を確認
   gcloud run services describe $CLOUD_RUN_SERVICE --region=$REGION --platform=managed
   
   # リビジョンのログを確認
   gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=$CLOUD_RUN_SERVICE" --limit=100
   ```

2. **データベース接続エラー**
   ```powershell
   # Cloud SQL接続を確認
   gcloud sql instances describe $CLOUD_SQL_INSTANCE --format="yaml(ipAddresses)"
   
   # Cloud SQL Proxyの接続テスト
   psql -h localhost -p 5432 -U pgadmin -d mcp_ux -c "SELECT version();"
   ```

3. **イメージプルエラー**
   ```powershell
   # Artifact Registryの権限を確認
   gcloud artifacts repositories get-iam-policy $ARTIFACT_REGISTRY_REPO --location=$REGION
   ```

### 10.2 Environment Variables Recovery

PowerShellセッションが失われた場合、以下のスクリプトで環境変数を復元できます：

```powershell
# 基本設定
$PROJECT_ID = "your-gcp-project-id"
$REGION = "asia-northeast1"
$ZONE = "asia-northeast1-a"
$PREFIX = "your-project-name"

# リソース名
$ARTIFACT_REGISTRY_REPO = "$PREFIX-repo"
$CLOUD_SQL_INSTANCE = "$PREFIX-db"
$CLOUD_RUN_SERVICE = "$PREFIX-api"
$SERVICE_ACCOUNT_NAME = "$PREFIX-sa"
$SERVICE_ACCOUNT_EMAIL = "$SERVICE_ACCOUNT_NAME@$PROJECT_ID.iam.gserviceaccount.com"

# URL取得
$SERVICE_URL = gcloud run services describe $CLOUD_RUN_SERVICE --platform=managed --region=$REGION --format="value(status.url)"
$REPOSITORY_URL = "$REGION-docker.pkg.dev/$PROJECT_ID/$ARTIFACT_REGISTRY_REPO"

# シークレットの再取得（必要に応じて）
# credentials.txtファイルから読み取るか、Secret Managerから取得
```

---

## 11. Cleanup

### 11.1 Delete All Resources

すべてのリソースを削除する場合は、以下の手順を実行します：

```powershell
# Cloud Runサービスの削除
gcloud run services delete $CLOUD_RUN_SERVICE --region=$REGION --quiet

# Cloud SQLインスタンスの削除
gcloud sql instances delete $CLOUD_SQL_INSTANCE --quiet

# Artifact Registryリポジトリの削除
gcloud artifacts repositories delete $ARTIFACT_REGISTRY_REPO --location=$REGION --quiet

# Secret Managerのシークレット削除
gcloud secrets delete api-key --quiet
gcloud secrets delete db-password --quiet
gcloud secrets delete mcp-api-key --quiet

# サービスアカウントの削除
gcloud iam service-accounts delete $SERVICE_ACCOUNT_EMAIL --quiet

# 削除確認
Write-Host "Resources deleted successfully!" -ForegroundColor Green
```

---

## Appendix: Important Information Summary

デプロイ後、以下の重要な情報が必要になります：

- **API Server URL**: Cloud Runサービスの自動生成URL
- **Health Check URL**: `{SERVICE_URL}/health`
- **API Key**: Secret Manager の `api-key` シークレットに保存
- **Database Connection**: Cloud SQL Proxy経由で接続

### Configuration Files

以下のファイルには機密情報が含まれているため、Gitにコミットしないでください：

- `credentials.txt` - API KeyとDB Password
- `mcp_server/.env` - API設定
- `claude_desktop_config_gcp.json` - Claude Desktop設定
- `cloud-sql-proxy.exe` - Cloud SQL Proxyバイナリ

### Update .gitignore

```powershell
# .gitignoreに追加
Add-Content .gitignore "`ncredentials.txt"
Add-Content .gitignore "claude_desktop_config_gcp.json"
Add-Content .gitignore "mcp_server/.env"
Add-Content .gitignore "cloud-sql-proxy.exe"
```

---

## Architecture Overview

デプロイされたソリューションの構成：

- **Cloud Run**: Node.js APIサーバーをホスト
- **Cloud SQL (PostgreSQL)**: データストレージ用のフレキシブルサーバー
- **Artifact Registry**: コンテナイメージの保存
- **Secret Manager**: シークレットとAPIキーの管理
- **Service Account**: サービス間の安全な認証
- **MCP Server**: Claude Desktop統合用のPythonベースブリッジ

## Security Features
- すべてのシークレットはSecret Managerに保存
- Service Accountによるサービス間認証
- 外部アクセス用のAPIキーベース認証
- GCPの組み込みファイアウォールルールによるネットワークセキュリティ

---

## Important Notes for Production Use

### Security Best Practices
1. **Never commit sensitive files** to your repository:
   - `credentials.txt`
   - `mcp_server/.env`
   - `claude_desktop_config_gcp.json`

2. **Use least privilege principle** for Service Accounts
3. **Enable Cloud Audit Logs** for compliance
4. **Configure VPC networks** for production environments
5. **Set up monitoring and alerting**

### Cost Optimization
- **Cloud Run**: Pay per request with automatic scaling to zero
- **Cloud SQL**: Consider using smaller instances for development
- **Artifact Registry**: Clean up old images regularly
- **Set up billing alerts** to monitor costs

### Scalability Considerations
- **Cloud Run concurrency**: Adjust based on your application needs
- **Cloud SQL connections**: Monitor connection pool usage
- **Resource limits**: Set appropriate CPU and memory limits

---

*This guide uses environment variables for flexible deployment across different environments.*
*Simply change the PROJECT_ID and PREFIX values to deploy to different environments or projects.*