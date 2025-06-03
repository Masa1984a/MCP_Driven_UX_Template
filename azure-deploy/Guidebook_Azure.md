# Azure Deployment Guide for MCP Driven UX Template

## Overview
This guide provides step-by-step instructions for deploying the MCP Driven UX Template to Microsoft Azure. The template consists of a Node.js API server with PostgreSQL database, designed to work with Claude Desktop via Model Context Protocol (MCP).

### Key Features
- **Environment Variable-Based Configuration**: All Azure resources use consistent naming with a configurable prefix
- **Automated Resource Management**: PowerShell scripts for streamlined deployment
- **Secure Credential Management**: Azure Key Vault integration for secrets
- **Claude Desktop Integration**: Complete MCP Server setup for AI-powered ticket management


## Prerequisites
- **Azure Subscription**: Active Azure subscription with contributor permissions
- **Required Tools**: Azure CLI, PowerShell 5.1+, Docker/Podman, PostgreSQL client (psql)
- **Naming Convention**: All resource names are generated from a configurable `$PREFIX` variable to ensure consistency
- **Security**: API keys and passwords are automatically generated and stored in Azure Key Vault

---

## 1. Initial Setup

### 1.1 Environment Variables Configuration

Set up the core environment variables that will be used throughout the deployment process:

```powershell
# プロジェクトのプレフィックスを設定（ハイフンを含む場合）
$PREFIX = "your-project-name"

# ACR用のプレフィックス（ハイフンを除去、小文字のみ）
$PREFIX_ACR = $PREFIX.Replace("-", "").ToLower()

# 場所（リージョン）
$LOCATION = "japaneast"

# リソース名を生成
$RESOURCE_GROUP = "rg-$PREFIX"
$ACR_NAME = "${PREFIX_ACR}acr"
$KEYVAULT_NAME = "$PREFIX-kv"  # Key Vaultは24文字制限のため短縮
$IDENTITY_NAME = "$PREFIX-identity"
$DB_NAME = "$PREFIX-db"
$CONTAINER_NAME = "$PREFIX-containers"
$DNS_LABEL = "$PREFIX-mcp"

# 設定内容を確認
Write-Host "=== 環境設定 ===" -ForegroundColor Cyan
Write-Host "PREFIX: $PREFIX"
Write-Host "LOCATION: $LOCATION"
Write-Host "RESOURCE_GROUP: $RESOURCE_GROUP"
Write-Host "ACR_NAME: $ACR_NAME"
Write-Host "KEYVAULT_NAME: $KEYVAULT_NAME"
Write-Host "IDENTITY_NAME: $IDENTITY_NAME"
Write-Host "DB_NAME: $DB_NAME"
Write-Host "CONTAINER_NAME: $CONTAINER_NAME"
Write-Host "DNS_LABEL: $DNS_LABEL"
```

### 1.2 Local Environment Verification

#### Verify Required Tools
```powershell
# Azure CLI
az --version

# Docker/Podman
podman --version

# PowerShell
$PSVersionTable.PSVersion

# psql
psql --version
```

### 1.3 Azure Subscription Setup

```powershell
# Azureにログイン
az login

# サブスクリプション一覧
az account list --output table

# 使用するサブスクリプションを設定（必要に応じて）
# az account set --subscription "サブスクリプションID"

# 現在のサブスクリプションを確認
az account show --output table
```

---

## 2. Environment Cleanup (If Required)

### 2.1 Check Existing Resources

```powershell
# リソースグループの存在確認
az group exists --name $RESOURCE_GROUP
```

### 2.2 Delete Resource Group

```powershell
# リソースグループとすべてのリソースを削除
az group delete --name $RESOURCE_GROUP --yes --no-wait

# 削除の進行状況を確認
az group show --name $RESOURCE_GROUP --query properties.provisioningState --output tsv
```

---

## 3. Generate Required Credentials

### 3.1 Authentication Information Generation

```powershell
# APIキーの生成
$API_KEY = "mcp_api_" + [guid]::NewGuid().ToString()
Write-Host "Generated API Key: $API_KEY"

# データベースパスワードの生成（特殊文字を制限）
$DB_PASSWORD = -join ((65..90) + (97..122) + (48..57) + (33,35,36,37,42,43,45,61,64,95) | Get-Random -Count 16 | ForEach-Object {[char]$_})
Write-Host "Generated DB Password: $DB_PASSWORD"

# 生成した値を環境変数として保存
$env:API_KEY = $API_KEY
$env:DB_PASSWORD = $DB_PASSWORD
```

---

## 4. Azure Resource Creation

### 4.1 Create Resource Group

```powershell
# リソースグループの作成
az group create --name $RESOURCE_GROUP --location $LOCATION
```

### 4.2 Create Azure Container Registry (ACR)

```powershell
# ACRの作成
az acr create `
  --resource-group $RESOURCE_GROUP `
  --name $ACR_NAME `
  --sku Basic `
  --admin-enabled true

# ACR管理者パスワードの取得
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
Write-Host "ACR Password: $ACR_PASSWORD"
$env:ACR_PASSWORD = $ACR_PASSWORD
```

### 4.3 Create Key Vault and Register Secrets

```powershell
# Key Vaultの作成
az keyvault create `
  --name $KEYVAULT_NAME `
  --resource-group $RESOURCE_GROUP `
  --location $LOCATION `
  --enable-rbac-authorization false

# シークレットの登録
az keyvault secret set --vault-name $KEYVAULT_NAME --name "acr-password" --value $ACR_PASSWORD
az keyvault secret set --vault-name $KEYVAULT_NAME --name "api-key" --value $API_KEY
az keyvault secret set --vault-name $KEYVAULT_NAME --name "db-password" --value $DB_PASSWORD
az keyvault secret set --vault-name $KEYVAULT_NAME --name "mcp-api-key" --value $API_KEY
```

### 4.4 Create Managed Identity

```powershell
# Managed Identityの作成
az identity create `
  --resource-group $RESOURCE_GROUP `
  --name $IDENTITY_NAME

# Identity情報の取得
$IDENTITY_ID = az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query id -o tsv
$IDENTITY_CLIENT_ID = az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query clientId -o tsv
$IDENTITY_PRINCIPAL_ID = az identity show --resource-group $RESOURCE_GROUP --name $IDENTITY_NAME --query principalId -o tsv

Write-Host "Identity ID: $IDENTITY_ID"
Write-Host "Identity Client ID: $IDENTITY_CLIENT_ID"
Write-Host "Identity Principal ID: $IDENTITY_PRINCIPAL_ID"

# 環境変数に保存
$env:IDENTITY_ID = $IDENTITY_ID
$env:IDENTITY_CLIENT_ID = $IDENTITY_CLIENT_ID
$env:IDENTITY_PRINCIPAL_ID = $IDENTITY_PRINCIPAL_ID
```

### 4.5 Configure Key Vault Access Policy

```powershell
# Managed IdentityにKey Vaultへのアクセス権限を付与
az keyvault set-policy `
  --name $KEYVAULT_NAME `
  --object-id $IDENTITY_PRINCIPAL_ID `
  --secret-permissions get list
```

### 4.6 Create PostgreSQL Flexible Server

```powershell
# PostgreSQL Flexible Serverの作成
az postgres flexible-server create `
  --resource-group $RESOURCE_GROUP `
  --name $DB_NAME `
  --location $LOCATION `
  --admin-user "pgadmin" `
  --admin-password $DB_PASSWORD `
  --tier "Burstable" `
  --sku-name "Standard_B1ms" `
  --storage-size 32 `
  --version "16" `
  --public-access "0.0.0.0-255.255.255.255"

# データベースの作成
az postgres flexible-server db create `
  --resource-group $RESOURCE_GROUP `
  --server-name $DB_NAME `
  --database-name "mcp_ux"
```

### 4.7 Initialize Database

```powershell
# PostgreSQL接続情報の設定
$env:PGHOST = "$DB_NAME.postgres.database.azure.com"
$env:PGUSER = "pgadmin"
$env:PGPASSWORD = $DB_PASSWORD
$env:PGDATABASE = "mcp_ux"
$env:PGSSLMODE = "require"

# Windows環境でのエンコーディング対策
# UTF-8を明示的に指定して初期化SQLを実行
psql -c "SET client_encoding TO 'UTF8';" -f db\init\ja\init.sql

# テーブルの確認
psql -c "SET search_path TO mcp_ux; SELECT tablename FROM pg_tables WHERE schemaname = 'mcp_ux';"
```

---

## 5. Container Image Build and Push

### 5.1 Build API Server Image

```powershell
# APIディレクトリに移動
cd api

# 依存関係のインストール
npm ci

# TypeScriptのビルド
npm run build:ci

# Dockerイメージのビルド
podman build -t "$ACR_NAME.azurecr.io/api-server:latest" .
podman tag "$ACR_NAME.azurecr.io/api-server:latest" "$ACR_NAME.azurecr.io/api-server:v1.0"

# イメージの確認
podman images | Select-String $ACR_NAME
```

### 5.2 Push to Azure Container Registry

```powershell
# Podmanで直接ACRにログイン（重要）
podman login "$ACR_NAME.azurecr.io" -u $ACR_NAME -p $ACR_PASSWORD

# イメージのプッシュ
podman push "$ACR_NAME.azurecr.io/api-server:latest"
podman push "$ACR_NAME.azurecr.io/api-server:v1.0"

# プッシュの確認
az acr repository list --name $ACR_NAME
az acr repository show-tags --name $ACR_NAME --repository api-server

# プロジェクトルートに戻る
cd ..
```

---

## 6. Deploy Container Instances

### 6.1 Configure Deployment Settings

```powershell
# deploy-config.yamlの作成（必要に応じて）
@"
project:
  prefix: "$PREFIX"
  location: "$LOCATION"
"@ | Out-File -FilePath "azure-deploy\deploy-config.yaml" -Encoding UTF8

# 内容確認
Get-Content azure-deploy\deploy-config.yaml
```

### 6.2 Run Automated Deployment Script

```powershell
# azure-deployディレクトリに移動
cd azure-deploy

# デプロイスクリプトの実行
.\deploy-api-only.ps1 -ConfigFile deploy-config.yaml

# プロジェクトルートに戻る
cd ..
```

### 6.3 Manual Deployment (If Script Fails)

```powershell
# デプロイYAMLの作成
@"
apiVersion: 2019-12-01
location: $LOCATION
name: $CONTAINER_NAME
identity:
  type: UserAssigned
  userAssignedIdentities:
    $($IDENTITY_ID): {}
properties:
  containers:
  - name: api-server
    properties:
      image: $ACR_NAME.azurecr.io/api-server:latest
      ports:
      - port: 8080
        protocol: TCP
      resources:
        requests:
          cpu: 0.5
          memoryInGB: 1
      environmentVariables:
      - name: NODE_ENV
        value: production
      - name: LOG_LEVEL
        value: info
      - name: PORT
        value: '8080'
      - name: DB_HOST
        value: $DB_NAME.postgres.database.azure.com
      - name: DB_PORT
        value: '5432'
      - name: DB_NAME
        value: mcp_ux
      - name: DB_USER
        value: pgadmin
      - name: DB_PASSWORD
        secureValue: $DB_PASSWORD
      - name: API_KEY
        secureValue: $API_KEY
      - name: AZURE_CLIENT_ID
        value: $IDENTITY_CLIENT_ID
  imageRegistryCredentials:
  - server: $ACR_NAME.azurecr.io
    username: $ACR_NAME
    password: $ACR_PASSWORD
  ipAddress:
    type: Public
    ports:
    - port: 8080
      protocol: TCP
    dnsNameLabel: $DNS_LABEL
  osType: Linux
  restartPolicy: Always
type: Microsoft.ContainerInstance/containerGroups
"@ | Out-File -FilePath "deploy-manual.yaml" -Encoding UTF8

# Container Instancesのデプロイ
az container create --resource-group $RESOURCE_GROUP --file deploy-manual.yaml
```

---

## 7. Deployment Verification

### 7.1 Check Deployment Status

```powershell
# Container Instancesの状態確認
az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query instanceView.state

# FQDNの取得（JSONレスポンスから直接取得、または構築）
$FQDN = "$DNS_LABEL.$LOCATION.azurecontainer.io"
Write-Host "API Server URL: http://$FQDN:8080"

# または、コンテナ情報から取得
$containerInfo = az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME | ConvertFrom-Json
$FQDN = $containerInfo.properties.ipAddress.fqdn
$IP = $containerInfo.properties.ipAddress.ip
Write-Host "API Server URL: http://$FQDN:8080"
Write-Host "API Server IP: http://${IP}:8080"
```

### 7.2 Health Check and API Testing

```powershell
# ヘルスチェック
Invoke-WebRequest -Uri "http://$FQDN:8080/health" -Method GET

# API認証テスト（APIキーなし - 401エラーを期待）
try {
    Invoke-WebRequest -Uri "http://$FQDN:8080/tickets" -Method GET
} catch {
    Write-Host "Expected 401 error: $_"
}

# API認証テスト（APIキーあり）
$headers = @{ "x-api-key" = $API_KEY }
Invoke-WebRequest -Uri "http://$FQDN:8080/tickets" -Method GET -Headers $headers
```

### 7.3 Check Application Logs

```powershell
# コンテナログの確認
az container logs --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --container-name api-server
```

---

## 8. Troubleshooting

### 8.1 Common Issues and Solutions

1. **コンテナが起動しない場合**
   ```powershell
   # イベントログの確認
   az container show --resource-group $RESOURCE_GROUP --name $CONTAINER_NAME --query "containers[0].instanceView.events"
   ```

2. **データベース接続エラー**
   ```powershell
   # ファイアウォールルールの確認
   az postgres flexible-server firewall-rule list --resource-group $RESOURCE_GROUP --server-name $DB_NAME
   ```

3. **イメージプルエラー**
   ```powershell
   # ACR認証情報の確認
   az acr credential show --name $ACR_NAME
   ```

### 8.2 Environment Variables Recovery

Use this script to restore environment variables if your PowerShell session is lost:

```powershell
# 基本設定
$PREFIX = "your-project-name"
$PREFIX_ACR = $PREFIX.Replace("-", "").ToLower()
$LOCATION = "japaneast"

# リソース名
$RESOURCE_GROUP = "rg-$PREFIX"
$ACR_NAME = "${PREFIX_ACR}acr"
$KEYVAULT_NAME = "$PREFIX-keyvault"
$IDENTITY_NAME = "$PREFIX-identity"
$DB_NAME = "$PREFIX-db"
$CONTAINER_NAME = "$PREFIX-containers"
$DNS_LABEL = "$PREFIX-mcp"

# シークレットの再取得（必要に応じて）
$API_KEY = az keyvault secret show --vault-name $KEYVAULT_NAME --name "api-key" --query value -o tsv
$DB_PASSWORD = az keyvault secret show --vault-name $KEYVAULT_NAME --name "db-password" --query value -o tsv
$ACR_PASSWORD = az acr credential show --name $ACR_NAME --query "passwords[0].value" -o tsv
```

---

## 9. Cleanup

### 9.1 Delete All Resources

```powershell
# リソースグループごと削除（すべてのリソースが削除される）
az group delete --name $RESOURCE_GROUP --yes

# 削除の確認
az group exists --name $RESOURCE_GROUP
```

---

## Appendix: Important Information Summary

After deployment, you'll need these key endpoints and information:

- **API Server URL**: `http://{DNS_LABEL}.{LOCATION}.azurecontainer.io:8080`
- **Health Check URL**: `http://{DNS_LABEL}.{LOCATION}.azurecontainer.io:8080/health`
- **API Key**: Key Vault の `api-key` シークレットに保存
- **Database Connection**: `{DB_NAME}.postgres.database.azure.com`

---

## 10. MCP Server and Claude Desktop Integration

### 10.1 Configure MCP Server for Azure API Connection

This section covers how to connect Claude Desktop to your deployed Azure API through the MCP (Model Context Protocol) Server.

#### Configure mcp_server/.env File

Update the MCP Server configuration to connect to your Azure deployment:

```powershell
# FQDNの確認
Write-Host "FQDN value: $FQDN"

# 文字列展開を使用せずに直接値を含める方法
$envContent = @"
# MCP Server Configuration for Azure API

# API Server URL
API_BASE_URL=http://$($FQDN):8080

# Environment mode
NODE_ENV=production

# API Key for authentication
API_KEY=$($API_KEY)

# Logging
LOG_LEVEL=INFO
"@

# ファイルに出力
$envContent | Out-File -FilePath "mcp_server\.env" -Encoding UTF8

# 設定内容の確認
Write-Host "=== mcp_server/.env content ===" -ForegroundColor Cyan
Get-Content mcp_server\.env
```

**Note**: If PowerShell here-document variable expansion fails, manually replace variables with their actual values.

#### Create Claude Desktop Configuration File

Generate the configuration file for Claude Desktop to use your MCP Server:

```powershell
# mcp_serverディレクトリの絶対パスを取得
$MCP_SERVER_PATH = Join-Path (Get-Location).Path "mcp_server"
Write-Host "MCP Server path: $MCP_SERVER_PATH"

# Windowsのパス区切り文字をエスケープ（\を\\に変換）
$MCP_SERVER_PATH_ESCAPED = $MCP_SERVER_PATH.Replace('\', '\\')

# API URLの構築
$API_URL = "http://$($FQDN):8080"

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
        "API_BASE_URL": "$API_URL",
        "API_KEY": "$($API_KEY)",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
"@

$configContent | Out-File -FilePath "claude_desktop_config_azure.json" -Encoding UTF8

# 設定内容の確認
Write-Host "=== claude_desktop_config_azure.json content ===" -ForegroundColor Cyan
Get-Content claude_desktop_config_azure.json
```

**Important Notes**: 
- Windows JSON files require double backslashes (`\\`) for path separators
- The `--directory` option must point to the `mcp_server` directory
- Use `$($variableName)` syntax for variable expansion in PowerShell here-documents

### 10.2 MCP Server Testing

#### 1. Install Required Python Packages

```powershell
# mcp_serverディレクトリに移動
cd mcp_server

# uvをインストール（未インストールの場合）
pip install uv

# 依存関係のインストール
uv pip install -r requirements.txt

# プロジェクトルートに戻る
cd ..
```

#### 2. Test MCP Server Execution

```powershell
# 環境変数を設定してMCP Serverを実行
$env:API_BASE_URL = "http://$FQDN:8080"
$env:API_KEY = $API_KEY
$env:LOG_LEVEL = "INFO"

# MCP Serverの起動テスト
python mcp_server/mcp_server.py
```

### 10.3 Claude Desktop Configuration

1. **設定ファイルの配置**
   ```powershell
   # Claude Desktopの設定ディレクトリパスを表示
   Write-Host "Claude Desktop設定ファイルを以下の場所にコピーしてください:"
   Write-Host "Windows: %APPDATA%\Claude\claude_desktop_config.json"
   Write-Host "Mac: ~/Library/Application Support/Claude/claude_desktop_config.json"
   ```

2. **設定ファイルのコピー**
   ```powershell
   # Windowsの場合の例
   Copy-Item claude_desktop_config_azure.json "$env:APPDATA\Claude\claude_desktop_config.json"
   ```

3. **Claude Desktopの再起動**
   - Claude Desktopを完全に終了
   - 再起動して設定を反映

### 10.4 Connection Testing

Test the connection in Claude Desktop with prompts like:

```
Show me the ticket list
```

If successful, you'll see ticket data retrieved from your Azure-deployed database.

---

## 11. Configuration File Management

### 11.1 Files Containing Sensitive Information (Do Not Commit)

These files contain sensitive information and should NOT be committed to Git:

- `mcp_server/.env` - API KeyとURLが含まれる
- `claude_desktop_config_azure.json` - API Keyが含まれる
- `azure-deploy/deploy-config.yaml` - プロジェクト固有の設定

### 11.2 Update .gitignore

```powershell
# .gitignoreに追加（必要な場合）
Add-Content .gitignore "`nclaude_desktop_config_azure.json"
Add-Content .gitignore "mcp_server/.env"
```

---

---

## Architecture Overview

The deployed solution includes:
- **Azure Container Instances**: Hosts the Node.js API server
- **Azure Database for PostgreSQL**: Flexible server for data storage
- **Azure Container Registry**: Stores container images
- **Azure Key Vault**: Manages secrets and API keys
- **Managed Identity**: Secure authentication between services
- **MCP Server**: Python-based bridge for Claude Desktop integration

## Security Features
- All secrets stored in Azure Key Vault
- Managed Identity for service-to-service authentication
- API key-based authentication for external access
- Network security through Azure's built-in firewall rules

---

*This guide uses environment variables for flexible deployment across different environments.*
*Simply change the PREFIX value to deploy to different environments or projects.*