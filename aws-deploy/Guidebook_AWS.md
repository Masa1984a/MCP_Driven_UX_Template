# AWS Deployment Guide for MCP Driven UX Template

## Overview
This guide provides step-by-step instructions for deploying the MCP Driven UX Template to Amazon Web Services (AWS). The template consists of a Node.js API server with PostgreSQL database, designed to work with Claude Desktop via Model Context Protocol (MCP).

### Key Features
- **Environment Variable-Based Configuration**: All AWS resources use consistent naming with a configurable prefix
- **Automated Resource Management**: PowerShell scripts for streamlined deployment
- **Secure Credential Management**: AWS Secrets Manager integration for secrets
- **Claude Desktop Integration**: Complete MCP Server setup for AI-powered ticket management

## Prerequisites
- **AWS Account**: Active AWS account with administrator permissions
- **Required Tools**: AWS CLI v2, PowerShell 5.1+, Docker/Podman, PostgreSQL client (psql)
- **Naming Convention**: All resource names are generated from a configurable `$PREFIX` variable to ensure consistency
- **Security**: API keys and passwords are automatically generated and stored in AWS Secrets Manager
- **PowerShell Configuration**: TLS 1.2 must be enabled for HTTPS communication with App Runner

## Architecture Overview

This deployment creates a modern, cloud-native architecture leveraging AWS services to host the MCP Driven UX Template:

```
┌─────────────────────┐
│  Claude Desktop     │
│  (Local)            │
└──────────┬──────────┘
           │ MCP (STDIO)
┌──────────▼──────────┐
│  MCP Server         │
│  (Python/Local)     │
└──────────┬──────────┘
           │ HTTP/HTTPS
┌──────────▼──────────┐     ┌──────────────────┐
│  AWS App Runner     │────▶│  Amazon RDS      │
│  (API Server)       │     │  (PostgreSQL)    │
└─────────────────────┘     └──────────────────┘
           ▲
           │
┌──────────▼──────────┐
│  Amazon ECR         │
│  (Container Image)  │
└─────────────────────┘
```

### Architecture Components

- **Amazon App Runner**: Hosts the Node.js API server with automatic scaling and managed infrastructure
- **Amazon RDS for PostgreSQL**: Managed database service with automated backups and high availability
- **Amazon ECR**: Container registry for application images with secure image storage
- **AWS Secrets Manager**: Secure storage for API keys and database credentials
- **IAM Roles**: Service-to-service authentication with least privilege access
- **VPC Infrastructure**: Network isolation and security controls
- **MCP Server**: Python-based bridge for Claude Desktop integration running locally

---

## 1. Initial Setup

### 1.1 Environment Variables Configuration

Set up the core environment variables that will be used throughout the deployment process:

```powershell
# プロジェクトのプレフィックスを設定
$PREFIX = "mcp-ux-dev"

# リージョンの設定
$AWS_REGION = "ap-northeast-1"

# プロジェクト名
$PROJECT_NAME = "MCP-Driven-UX"

# リソース名を生成
$VPC_NAME = "$PREFIX-vpc"
$ECR_REPO_NAME = "$PREFIX/api-server"
$RDS_INSTANCE_ID = "$PREFIX-db"
$SECRET_DB_NAME = "$PREFIX/database"
$SECRET_API_NAME = "$PREFIX/api-key"
$APP_RUNNER_SERVICE_NAME = "$PREFIX-app-runner"

# 設定内容を確認
Write-Host "=== AWS環境設定 ===" -ForegroundColor Cyan
Write-Host "PREFIX: $PREFIX"
Write-Host "AWS_REGION: $AWS_REGION"
Write-Host "VPC_NAME: $VPC_NAME"
Write-Host "ECR_REPO_NAME: $ECR_REPO_NAME"
Write-Host "RDS_INSTANCE_ID: $RDS_INSTANCE_ID"
Write-Host "SECRET_DB_NAME: $SECRET_DB_NAME"
Write-Host "SECRET_API_NAME: $SECRET_API_NAME"
Write-Host "APP_RUNNER_SERVICE_NAME: $APP_RUNNER_SERVICE_NAME"
```

### 1.2 Local Environment Verification

#### Verify Required Tools
```powershell
# AWS CLI
aws --version

# Docker
docker --version

# PowerShell
$PSVersionTable.PSVersion

# psql
psql --version
```

### 1.3 AWS Account Setup

```powershell
# AWSにログイン（認証情報を設定）
aws configure

# 現在のアカウント情報を確認
aws sts get-caller-identity

# 現在のリージョンを確認
aws configure get region

# リージョンを設定（必要に応じて）
aws configure set region $AWS_REGION

# PowerShellのTLS設定（App Runner HTTPS通信に必要）
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
Write-Host "TLS 1.2 enabled for PowerShell HTTPS communications"
```

---

## 2. Environment Cleanup (If Required)

### 2.1 Check Existing Resources

```powershell
# CloudFormationスタックの確認
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?contains(StackName, '$PREFIX')]"

# ECRリポジトリの確認
aws ecr describe-repositories --query "repositories[?contains(repositoryName, '$PREFIX')]"

# RDSインスタンスの確認
aws rds describe-db-instances --query "DBInstances[?contains(DBInstanceIdentifier, '$PREFIX')]"

# Secrets Managerシークレットの確認
aws secretsmanager list-secrets --query "SecretList[?contains(Name, '$PREFIX')]"
```

### 2.2 Delete Existing Resources (If Needed)

```powershell
# App Runnerサービスの削除
$APP_RUNNER_ARN = aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" --output text
if ($APP_RUNNER_ARN) {
    aws apprunner delete-service --service-arn $APP_RUNNER_ARN
    Write-Host "App Runnerサービスの削除を開始しました"
}

# RDSインスタンスの削除
aws rds delete-db-instance --db-instance-identifier $RDS_INSTANCE_ID --skip-final-snapshot --delete-automated-backups

# Secrets Managerシークレットの削除
aws secretsmanager delete-secret --secret-id $SECRET_DB_NAME --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id $SECRET_API_NAME --force-delete-without-recovery

# ECRリポジトリの削除
aws ecr delete-repository --repository-name $ECR_REPO_NAME --force

Write-Host "リソースの削除を開始しました。完了までしばらくお待ちください。"
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

## 4. AWS Resource Creation

### 4.1 Create VPC and Network Infrastructure

```powershell
# VPCの作成
$VPC_ID = aws ec2 create-vpc --cidr-block 10.0.0.0/16 --tag-specifications "ResourceType=vpc,Tags=[{Key=Name,Value=$VPC_NAME},{Key=Project,Value=$PROJECT_NAME}]" --query "Vpc.VpcId" --output text
Write-Host "Created VPC: $VPC_ID"

# インターネットゲートウェイの作成
$IGW_ID = aws ec2 create-internet-gateway --tag-specifications "ResourceType=internet-gateway,Tags=[{Key=Name,Value=$PREFIX-igw},{Key=Project,Value=$PROJECT_NAME}]" --query "InternetGateway.InternetGatewayId" --output text
Write-Host "Created Internet Gateway: $IGW_ID"

# インターネットゲートウェイをVPCにアタッチ
aws ec2 attach-internet-gateway --vpc-id $VPC_ID --internet-gateway-id $IGW_ID

# VPCのDNS設定を有効化（RDS作成に必要）
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-support
aws ec2 modify-vpc-attribute --vpc-id $VPC_ID --enable-dns-hostnames
Write-Host "Enabled DNS resolution and hostnames for VPC: $VPC_ID"

# アベイラビリティゾーンの取得
$AZ1 = aws ec2 describe-availability-zones --query "AvailabilityZones[0].ZoneName" --output text
$AZ2 = aws ec2 describe-availability-zones --query "AvailabilityZones[1].ZoneName" --output text
Write-Host "Using AZs: $AZ1, $AZ2"

# パブリックサブネットの作成
$PUBLIC_SUBNET1_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.1.0/24 --availability-zone $AZ1 --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PREFIX-public-1},{Key=Project,Value=$PROJECT_NAME}]" --query "Subnet.SubnetId" --output text
$PUBLIC_SUBNET2_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.2.0/24 --availability-zone $AZ2 --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PREFIX-public-2},{Key=Project,Value=$PROJECT_NAME}]" --query "Subnet.SubnetId" --output text

# 注意: サブネット作成でCIDR競合エラーが発生した場合
# 既存のサブネットを確認: aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query "Subnets[*].[SubnetId,CidrBlock,AvailabilityZone,Tags[?Key=='Name'].Value|[0]]" --output table
# 既存サブネットにタグを追加: aws ec2 create-tags --resources <subnet-id> --tags "Key=Name,Value=$PREFIX-public-1" "Key=Project,Value=$PROJECT_NAME"

# プライベートサブネットの作成（データベース用）
$PRIVATE_SUBNET1_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.21.0/24 --availability-zone $AZ1 --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PREFIX-private-1},{Key=Project,Value=$PROJECT_NAME}]" --query "Subnet.SubnetId" --output text
$PRIVATE_SUBNET2_ID = aws ec2 create-subnet --vpc-id $VPC_ID --cidr-block 10.0.22.0/24 --availability-zone $AZ2 --tag-specifications "ResourceType=subnet,Tags=[{Key=Name,Value=$PREFIX-private-2},{Key=Project,Value=$PROJECT_NAME}]" --query "Subnet.SubnetId" --output text

Write-Host "Created subnets:"
Write-Host "  Public: $PUBLIC_SUBNET1_ID, $PUBLIC_SUBNET2_ID"
Write-Host "  Private: $PRIVATE_SUBNET1_ID, $PRIVATE_SUBNET2_ID"

# ルートテーブルの作成と設定
$ROUTE_TABLE_ID = aws ec2 create-route-table --vpc-id $VPC_ID --tag-specifications "ResourceType=route-table,Tags=[{Key=Name,Value=$PREFIX-public-rt},{Key=Project,Value=$PROJECT_NAME}]" --query "RouteTable.RouteTableId" --output text
aws ec2 create-route --route-table-id $ROUTE_TABLE_ID --destination-cidr-block 0.0.0.0/0 --gateway-id $IGW_ID
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET1_ID --route-table-id $ROUTE_TABLE_ID
aws ec2 associate-route-table --subnet-id $PUBLIC_SUBNET2_ID --route-table-id $ROUTE_TABLE_ID

# パブリックサブネットでパブリックIPの自動割り当てを有効化
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET1_ID --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --subnet-id $PUBLIC_SUBNET2_ID --map-public-ip-on-launch

# 環境変数に保存
$env:VPC_ID = $VPC_ID
$env:PUBLIC_SUBNET1_ID = $PUBLIC_SUBNET1_ID
$env:PUBLIC_SUBNET2_ID = $PUBLIC_SUBNET2_ID
$env:PRIVATE_SUBNET1_ID = $PRIVATE_SUBNET1_ID
$env:PRIVATE_SUBNET2_ID = $PRIVATE_SUBNET2_ID
```

### 4.2 Create Security Groups

```powershell
# RDS用セキュリティグループ
$RDS_SG_ID = aws ec2 create-security-group --group-name "$PREFIX-rds-sg" --description "Security group for RDS PostgreSQL" --vpc-id $VPC_ID --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PREFIX-rds-sg},{Key=Project,Value=$PROJECT_NAME}]" --query "GroupId" --output text
Write-Host "Created RDS Security Group: $RDS_SG_ID"

# App Runner用セキュリティグループ（実際にはApp Runnerが自動管理するため、RDSからの接続許可用）
$APP_SG_ID = aws ec2 create-security-group --group-name "$PREFIX-app-sg" --description "Security group for App Runner" --vpc-id $VPC_ID --tag-specifications "ResourceType=security-group,Tags=[{Key=Name,Value=$PREFIX-app-sg},{Key=Project,Value=$PROJECT_NAME}]" --query "GroupId" --output text
Write-Host "Created App Security Group: $APP_SG_ID"

# 環境変数に保存
$env:RDS_SG_ID = $RDS_SG_ID
$env:APP_SG_ID = $APP_SG_ID
```

### 4.3 Create AWS Secrets Manager Secrets

```powershell
# データベース認証情報シークレット
$DB_SECRET_STRING = "{`"username`":`"postgres`",`"password`":`"$DB_PASSWORD`"}"
aws secretsmanager create-secret --name $SECRET_DB_NAME --secret-string $DB_SECRET_STRING --description "Database credentials for $PREFIX"

# API認証情報シークレット
$API_SECRET_STRING = "{`"api_key`":`"$API_KEY`"}"
aws secretsmanager create-secret --name $SECRET_API_NAME --secret-string $API_SECRET_STRING --description "API key for $PREFIX"

Write-Host "Created secrets in AWS Secrets Manager"
```

### 4.4 Create IAM Roles

```powershell
# App Runner用IAMロールのトラストポリシー
$TRUST_POLICY = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": [
                    "tasks.apprunner.amazonaws.com",
                    "build.apprunner.amazonaws.com"
                ]
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
"@

$TRUST_POLICY | Out-File -FilePath "aws-deploy\trust-policy.json" -Encoding UTF8

# IAMロールの作成
aws iam create-role --role-name "$PREFIX-app-runner-role" --assume-role-policy-document file://aws-deploy/trust-policy.json

# App Runner用ポリシー（変数を明示的に展開）
$APP_RUNNER_POLICY = @"
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "secretsmanager:GetSecretValue"
            ],
            "Resource": [
                "arn:aws:secretsmanager:$($AWS_REGION):*:secret:$($SECRET_DB_NAME)*",
                "arn:aws:secretsmanager:$($AWS_REGION):*:secret:$($SECRET_API_NAME)*"
            ]
        },
        {
            "Effect": "Allow",
            "Action": [
                "logs:CreateLogGroup",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:$($AWS_REGION):*:*"
        }
    ]
}
"@

$APP_RUNNER_POLICY | Out-File -FilePath "aws-deploy\app-runner-policy.json" -Encoding UTF8

# ポリシーの作成とアタッチ
aws iam create-policy --policy-name "$PREFIX-app-runner-policy" --policy-document file://aws-deploy/app-runner-policy.json
$ACCOUNT_ID = aws sts get-caller-identity --query "Account" --output text
aws iam attach-role-policy --role-name "$PREFIX-app-runner-role" --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/$PREFIX-app-runner-policy"

# ECRアクセスポリシーをアタッチ（App Runnerがコンテナイメージを取得するため）
aws iam attach-role-policy --role-name "$PREFIX-app-runner-role" --policy-arn "arn:aws:iam::aws:policy/service-role/AWSAppRunnerServicePolicyForECRAccess"

Write-Host "Created IAM roles and policies"
```

---

## 5. Database Setup

### 5.1 Create RDS Subnet Group

```powershell
# パブリックサブネット用のDBサブネットグループを作成（開発環境用）
# 注意: 本番環境ではプライベートサブネットを使用することを推奨
aws rds create-db-subnet-group --db-subnet-group-name "$PREFIX-db-subnet-group-public" --db-subnet-group-description "Public subnet group for $PREFIX database" --subnet-ids $PUBLIC_SUBNET1_ID $PUBLIC_SUBNET2_ID --tags "Key=Name,Value=$PREFIX-db-subnet-group-public" "Key=Project,Value=$PROJECT_NAME"

Write-Host "Created DB subnet group: $PREFIX-db-subnet-group-public"
```

### 5.2 Configure RDS Security Group

```powershell
# 初期化作業用に一時的にパブリックアクセスを許可（後で制限する）
aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0

Write-Host "Configured RDS security group (temporary public access for initialization)"
```

### 5.3 Create RDS PostgreSQL Instance

```powershell
# RDSインスタンスの作成（パブリックアクセス可能に設定）
aws rds create-db-instance `
    --db-instance-identifier $RDS_INSTANCE_ID `
    --db-instance-class db.t3.micro `
    --engine postgres `
    --engine-version 16.4 `
    --master-username postgres `
    --master-user-password $DB_PASSWORD `
    --allocated-storage 20 `
    --db-subnet-group-name "$PREFIX-db-subnet-group-public" `
    --vpc-security-group-ids $RDS_SG_ID `
    --backup-retention-period 7 `
    --storage-encrypted `
    --publicly-accessible `
    --tags "Key=Name,Value=$PREFIX-database" "Key=Project,Value=$PROJECT_NAME"

Write-Host "RDS instance creation started. This will take several minutes..."

# RDSインスタンスの作成完了を待機
Write-Host "Waiting for RDS instance to be available..."
aws rds wait db-instance-available --db-instance-identifier $RDS_INSTANCE_ID

# RDSエンドポイントの取得
$RDS_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $RDS_INSTANCE_ID --query "DBInstances[0].Endpoint.Address" --output text
Write-Host "RDS Endpoint: $RDS_ENDPOINT"

# 環境変数に保存
$env:RDS_ENDPOINT = $RDS_ENDPOINT
```

### 5.4 Initialize Database

```powershell
# PostgreSQL接続情報の設定
$env:PGHOST = $RDS_ENDPOINT
$env:PGUSER = "postgres"
$env:PGPASSWORD = $DB_PASSWORD
$env:PGDATABASE = "postgres"
$env:PGSSLMODE = "require"

# クライアントエンコーディングをUTF-8に設定（Windows環境で重要）
$env:PGCLIENTENCODING = "UTF8"

# 接続テスト
psql -c "SELECT version();"

# データベースの作成
psql -c "CREATE DATABASE mcp_ux;"

# 初期化スクリプトの実行（UTF-8を明示的に指定）
psql -d mcp_ux -c "SET client_encoding TO 'UTF8';" -f db\init\ja\init.sql

# テーブルの確認
psql -d mcp_ux -c "SET search_path TO mcp_ux; SELECT tablename FROM pg_tables WHERE schemaname = 'mcp_ux' ORDER BY tablename LIMIT 10;"

# データの確認
psql -d mcp_ux -c "SET search_path TO mcp_ux; SELECT COUNT(*) FROM tickets;"

Write-Host "Database initialization completed"
```

### 5.5 Secure RDS Access

```powershell
# パブリックアクセスを削除し、App Runnerからのアクセスのみ許可
aws ec2 revoke-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0

# App Runnerのマネージド VPCからのアクセス許可（実際のApp Runner作成後に設定）
Write-Host "Removed public access to RDS. Will configure App Runner access after service creation."
```

---

## 6. Container Registry Setup

### 6.1 Create Amazon ECR Repository

```powershell
# ECRリポジトリの作成
aws ecr create-repository --repository-name $ECR_REPO_NAME --region $AWS_REGION

# ECRログイン
$ECR_LOGIN_TOKEN = aws ecr get-login-password --region $AWS_REGION
$ECR_LOGIN_TOKEN | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

Write-Host "Created ECR repository: $ECR_REPO_NAME"
```

### 6.2 Build and Push Container Image

```powershell
# APIディレクトリに移動
cd api

# 依存関係のインストール
npm ci

# TypeScriptのビルド
npm run build:ci

# ECRリポジトリURIを構築
$ECR_URI = "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$ECR_REPO_NAME"
Write-Host "ECR URI: $ECR_URI"

# Dockerイメージのビルド
# 注意: Docker使用時は 'docker' を、Podman使用時は 'podman' を使用してください
docker build -t "${ECR_URI}:latest" .
docker tag "${ECR_URI}:latest" "${ECR_URI}:v1.0"

# Dockerビルドでエラーが発生した場合（Permission denied等）はPodmanを使用
# podman build -t "${ECR_URI}:latest" .
# podman tag "${ECR_URI}:latest" "${ECR_URI}:v1.0"

# イメージの確認
docker images | Select-String "api-server"
# Podman使用時: podman images | Select-String "api-server"

# ECRへのプッシュ
docker push "${ECR_URI}:latest"
docker push "${ECR_URI}:v1.0"

# Podman使用時のプッシュでエラーが発生した場合は再ログインが必要
# StatusCode: 403 エラーが発生した場合は以下を実行：
$ECR_LOGIN_TOKEN = aws ecr get-login-password --region $AWS_REGION
$ECR_LOGIN_TOKEN | podman login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"

# Podman使用時のプッシュを再実行
# podman push "${ECR_URI}:latest"
# podman push "${ECR_URI}:v1.0"

# プッシュの確認
aws ecr describe-images --repository-name $ECR_REPO_NAME

# プロジェクトルートに戻る
cd ..

Write-Host "Container image built and pushed to ECR"
```

---

## 7. Deploy Application with App Runner

### 7.1 Create App Runner Configuration

```powershell
# App Runner用の設定ファイルを作成
$APP_RUNNER_CONFIG = @"
{
    "ServiceName": "$APP_RUNNER_SERVICE_NAME",
    "SourceConfiguration": {
        "ImageRepository": {
            "ImageIdentifier": "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/$($ECR_REPO_NAME):latest",
            "ImageConfiguration": {
                "Port": "8080",
                "RuntimeEnvironmentVariables": {
                    "NODE_ENV": "production",
                    "LOG_LEVEL": "info",
                    "PORT": "8080",
                    "DB_HOST": "$RDS_ENDPOINT",
                    "DB_PORT": "5432",
                    "DB_NAME": "mcp_ux",
                    "DB_USER": "postgres",
                    "DB_PASSWORD": "$DB_PASSWORD",
                    "API_KEY": "$API_KEY"
                }
            },
            "ImageRepositoryType": "ECR"
        },
        "AutoDeploymentsEnabled": false,
        "AuthenticationConfiguration": {
            "AccessRoleArn": "arn:aws:iam::$($ACCOUNT_ID):role/$PREFIX-app-runner-role"
        }
    },
    "InstanceConfiguration": {
        "Cpu": "0.25 vCPU",
        "Memory": "0.5 GB",
        "InstanceRoleArn": "arn:aws:iam::$($ACCOUNT_ID):role/$PREFIX-app-runner-role"
    },
    "HealthCheckConfiguration": {
        "Protocol": "HTTP",
        "Path": "/health",
        "Interval": 10,
        "Timeout": 5,
        "HealthyThreshold": 1,
        "UnhealthyThreshold": 5
    }
}
"@

$APP_RUNNER_CONFIG | Out-File -FilePath "aws-deploy\apprunner-config.json" -Encoding UTF8

Write-Host "Created App Runner configuration file"
```

### 7.2 Create App Runner Service

```powershell
# App Runnerサービスの作成
aws apprunner create-service --cli-input-json file://aws-deploy/apprunner-config.json

Write-Host "App Runner service creation started..."

# サービスの作成完了を待機
$SERVICE_ARN = aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" --output text

# 注意: aws apprunner wait service-running コマンドが利用できない場合があります
# その場合は手動でステータスを確認してください：
# aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.Status" --output text
# ステータスが "RUNNING" になるまで数分お待ちください

# サービスURLの取得
$SERVICE_URL = aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceUrl" --output text
Write-Host "App Runner service URL: https://$SERVICE_URL"

# 環境変数に保存
$env:SERVICE_URL = $SERVICE_URL
```

---

## 8. Network Configuration for App Runner

## 8.0 Troubleshooting Secrets Manager Access

App RunnerがSecrets Managerから値を取得できない場合は、以下を確認してください：

```powershell
# RDSへのパブリックアクセスを許可（App Runnerのマネージド環境から接続するため）
aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0

# Secrets ManagerのARNが完全な形式（バージョンID付き）であることを確認
$DB_SECRET_ARN = aws secretsmanager describe-secret --secret-id $SECRET_DB_NAME --query "ARN" --output text
$API_SECRET_ARN = aws secretsmanager describe-secret --secret-id $SECRET_API_NAME --query "ARN" --output text

Write-Host "Complete Secret ARNs:"
Write-Host "DB: $DB_SECRET_ARN"
Write-Host "API: $API_SECRET_ARN"
```


### 8.1 Configure VPC Connector (if needed)

```powershell
# App Runner VPC Connectorの作成（RDSへの接続用）
$VPC_CONNECTOR_ARN = aws apprunner create-vpc-connector --vpc-connector-name "$PREFIX-vpc-connector" --subnets $PRIVATE_SUBNET1_ID $PRIVATE_SUBNET2_ID --security-groups $APP_SG_ID --query "VpcConnector.VpcConnectorArn" --output text

# VPC Connectorの作成完了を待機
aws apprunner wait vpc-connector-created --vpc-connector-arn $VPC_CONNECTOR_ARN

# App RunnerサービスをVPCに関連付け
aws apprunner associate-custom-domain --service-arn $SERVICE_ARN --domain-name $SERVICE_URL

Write-Host "VPC Connector created and associated with App Runner"
```

### 8.2 Update RDS Security Group

```powershell
# App RunnerからRDSへのアクセスを許可
aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --source-group $APP_SG_ID

Write-Host "Updated RDS security group to allow App Runner access"
```

---

## 9. Deployment Verification

### 9.1 Check Deployment Status

```powershell
# App Runnerサービスの状態確認
aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.Status" --output text

# サービスURLの最終確認
$FINAL_SERVICE_URL = aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceUrl" --output text
Write-Host "API Server URL: https://$FINAL_SERVICE_URL"
```

### 9.2 Health Check and API Testing

```powershell
# TLS設定を確保（App Runner HTTPS接続に必要）
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# PowerShellのHTTPクライアント設定を調整
$PSDefaultParameterValues = @{
    'Invoke-WebRequest:TimeoutSec' = 30
    'Invoke-WebRequest:MaximumRedirection' = 0
}

# ヘルスチェック
try {
    $healthResponse = Invoke-WebRequest -Uri "https://$FINAL_SERVICE_URL/health" -Method GET -UseBasicParsing
    Write-Host "Health check successful: $($healthResponse.StatusCode)"
    Write-Host "Response: $($healthResponse.Content)"
} catch {
    Write-Host "Health check failed: $_"
    Write-Host "Note: If PowerShell fails, try using curl instead"
}

# API認証テスト（APIキーなし - 401エラーを期待）
try {
    Invoke-WebRequest -Uri "https://$FINAL_SERVICE_URL/tickets" -Method GET -UseBasicParsing
} catch {
    Write-Host "Expected 401 error: $($_.Exception.Response.StatusCode)"
}

# API認証テスト（APIキーあり）
try {
    $headers = @{ 
        "x-api-key" = $API_KEY
        "User-Agent" = "PowerShell"
    }
    $ticketsResponse = Invoke-WebRequest -Uri "https://$FINAL_SERVICE_URL/tickets" -Method GET -Headers $headers -UseBasicParsing -TimeoutSec 30
    Write-Host "API test successful: $($ticketsResponse.StatusCode)"
    $tickets = $ticketsResponse.Content | ConvertFrom-Json
    Write-Host "Retrieved $($tickets.length) tickets"
    if ($tickets.length -gt 0) {
        Write-Host "First ticket: $($tickets[0].ticketId) - $($tickets[0].summary)"
    }
} catch {
    Write-Host "PowerShell API test failed: $_"
    Write-Host "Alternative: Use curl command below"
    Write-Host "curl -H \"x-api-key: $API_KEY\" \"https://$FINAL_SERVICE_URL/tickets\""
}
```

### 9.3 Check Application Logs

```powershell
# App Runnerのロググループ確認
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner/$APP_RUNNER_SERVICE_NAME"

# サービスIDを取得してアプリケーションログパスを構築
$SERVICE_ID = aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceId" --output text
$APP_LOG_GROUP = "/aws/apprunner/$APP_RUNNER_SERVICE_NAME/$SERVICE_ID/application"

Write-Host "Application Log Group: $APP_LOG_GROUP"

# アプリケーションログストリームを確認
$LATEST_APP_LOG_STREAM = aws logs describe-log-streams --log-group-name $APP_LOG_GROUP --order-by LastEventTime --descending --max-items 1 --query "logStreams[0].logStreamName" --output text

if ($LATEST_APP_LOG_STREAM) {
    Write-Host "Getting latest application logs..."
    aws logs get-log-events --log-group-name $APP_LOG_GROUP --log-stream-name $LATEST_APP_LOG_STREAM --limit 20
} else {
    Write-Host "No application log streams found. Check if the service is running."
}
```

---

## 10. MCP Server and Claude Desktop Integration

### 10.1 Configure MCP Server for AWS API Connection

Update the MCP Server configuration to connect to your AWS deployment:

```powershell
# API URLの確認
Write-Host "API Base URL: https://$FINAL_SERVICE_URL"

# MCP Server用環境設定ファイルの作成
$envContent = @"
# MCP Server Configuration for AWS API

# API Server URL
API_BASE_URL=https://$FINAL_SERVICE_URL

# Environment mode
NODE_ENV=production

# API Key for authentication
API_KEY=$API_KEY

# Logging
LOG_LEVEL=INFO
"@

# ファイルに出力
$envContent | Out-File -FilePath "mcp_server\.env" -Encoding UTF8

# 設定内容の確認
Write-Host "=== mcp_server/.env content ===" -ForegroundColor Cyan
Get-Content mcp_server\.env
```

### 10.2 Create Claude Desktop Configuration File

Generate the configuration file for Claude Desktop to use your MCP Server:

```powershell
# mcp_serverディレクトリの絶対パスを取得
$MCP_SERVER_PATH = Join-Path (Get-Location).Path "mcp_server"
Write-Host "MCP Server path: $MCP_SERVER_PATH"

# Windowsのパス区切り文字をエスケープ（\を\\に変換）
$MCP_SERVER_PATH_ESCAPED = $MCP_SERVER_PATH.Replace('\', '\\')

# API URLの構築
$API_URL = "https://$FINAL_SERVICE_URL"

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
        "API_KEY": "$API_KEY",
        "LOG_LEVEL": "INFO"
      }
    }
  }
}
"@

$configContent | Out-File -FilePath "claude_desktop_config_aws.json" -Encoding UTF8

# 設定内容の確認
Write-Host "=== claude_desktop_config_aws.json content ===" -ForegroundColor Cyan
Get-Content claude_desktop_config_aws.json
```

### 10.3 MCP Server Testing

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
$env:API_BASE_URL = "https://$FINAL_SERVICE_URL"
$env:API_KEY = $API_KEY
$env:LOG_LEVEL = "INFO"

# MCP Serverの起動テスト
python mcp_server/mcp_server.py
```

### 10.4 Claude Desktop Configuration

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
   Copy-Item claude_desktop_config_aws.json "$env:APPDATA\Claude\claude_desktop_config.json"
   ```

3. **Claude Desktopの再起動**
   - Claude Desktopを完全に終了
   - 再起動して設定を反映

### 10.5 Connection Testing

Test the connection in Claude Desktop with prompts like:

```
Show me the ticket list
```

If successful, you'll see ticket data retrieved from your AWS-deployed database.

---

## 11. Monitoring and Logging

### 11.1 CloudWatch Configuration

```powershell
# CloudWatch Logsの設定確認
aws logs describe-log-groups --log-group-name-prefix "/aws/apprunner"

# CloudWatch Alarmの作成（例：高CPU使用率）
aws cloudwatch put-metric-alarm --alarm-name "$PREFIX-high-cpu" --alarm-description "High CPU utilization for App Runner" --metric-name CPUUtilization --namespace AWS/AppRunner --statistic Average --period 300 --threshold 80 --comparison-operator GreaterThanThreshold --evaluation-periods 2
```

### 11.2 Cost Monitoring

```powershell
# AWS Budgetの設定（月額予算）
$BUDGET_CONFIG = @"
{
    "BudgetName": "$PREFIX-monthly-budget",
    "BudgetLimit": {
        "Amount": "50.0",
        "Unit": "USD"
    },
    "TimeUnit": "MONTHLY",
    "TimePeriod": {
        "Start": "2024-01-01T00:00:00.000Z",
        "End": "2087-06-15T00:00:00.000Z"
    },
    "BudgetType": "COST",
    "CostFilters": {
        "TagKey": ["Project"],
        "TagValue": ["$PROJECT_NAME"]
    }
}
"@

$BUDGET_CONFIG | Out-File -FilePath "aws-deploy\budget-config.json" -Encoding UTF8

# 予算の作成
$ACCOUNT_ID = aws sts get-caller-identity --query "Account" --output text
aws budgets create-budget --account-id $ACCOUNT_ID --budget file://aws-deploy/budget-config.json
```

---

## 12. Troubleshooting

### 12.1 Common Issues and Solutions

1. **PowerShell HTTPS接続エラー**
   ```powershell
   # TLS 1.2を有効化
   [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
   
   # 代替手段: curlコマンドを使用
   curl -H "x-api-key: $API_KEY" "https://$SERVICE_URL/tickets"
   ```

2. **App Runnerサービスが起動しない場合**
   ```powershell
   # サービスの詳細情報を確認
   aws apprunner describe-service --service-arn $SERVICE_ARN
   
   # アプリケーションログを確認
   $SERVICE_ID = aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceId" --output text
   $APP_LOG_GROUP = "/aws/apprunner/$APP_RUNNER_SERVICE_NAME/$SERVICE_ID/application"
   aws logs get-log-events --log-group-name $APP_LOG_GROUP --log-stream-name $LATEST_LOG_STREAM --limit 50
   ```

3. **データベース接続エラー**
   ```powershell
   # RDSインスタンスの状態確認
   aws rds describe-db-instances --db-instance-identifier $RDS_INSTANCE_ID --query "DBInstances[0].DBInstanceStatus"
   
   # セキュリティグループの確認
   aws ec2 describe-security-groups --group-ids $RDS_SG_ID
   
   # App RunnerからRDSへのアクセスを許可（一時的なパブリックアクセス）
   aws ec2 authorize-security-group-ingress --group-id $RDS_SG_ID --protocol tcp --port 5432 --cidr 0.0.0.0/0
   ```

4. **Dockerビルドエラー（Permission denied）**
   ```powershell
   # Docker Desktop権限エラーの場合はPodmanを使用
   podman build -t "${ECR_URI}:latest" .
   podman tag "${ECR_URI}:latest" "${ECR_URI}:v1.0"
   ```

5. **ECRプッシュエラー（Podman使用時）**
   ```powershell
   # StatusCode: 403 エラーの場合は再ログインが必要
   $ECR_LOGIN_TOKEN = aws ecr get-login-password --region $AWS_REGION
   $ECR_LOGIN_TOKEN | podman login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com"
   
   # プッシュを再実行
   podman push "${ECR_URI}:latest"
   podman push "${ECR_URI}:v1.0"
   ```

### 12.2 Environment Variables Recovery

PowerShellセッションが失われた場合の環境変数復旧スクリプト:

```powershell
# 基本設定の復旧
$PREFIX = "mcp-ux-dev"
$AWS_REGION = "ap-northeast-1"
$PROJECT_NAME = "MCP-Driven-UX"

# リソース名の再構築
$ECR_REPO_NAME = "$PREFIX/api-server"
$RDS_INSTANCE_ID = "$PREFIX-db"
$SECRET_DB_NAME = "$PREFIX/database"
$SECRET_API_NAME = "$PREFIX/api-key"
$APP_RUNNER_SERVICE_NAME = "$PREFIX-app-runner"

# アカウントIDの取得
$ACCOUNT_ID = aws sts get-caller-identity --query "Account" --output text

# RDSエンドポイントの取得
$RDS_ENDPOINT = aws rds describe-db-instances --db-instance-identifier $RDS_INSTANCE_ID --query "DBInstances[0].Endpoint.Address" --output text

# App RunnerサービスURLの取得
$SERVICE_ARN = aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" --output text
$FINAL_SERVICE_URL = aws apprunner describe-service --service-arn $SERVICE_ARN --query "Service.ServiceUrl" --output text

# シークレットの取得
$API_KEY = aws secretsmanager get-secret-value --secret-id $SECRET_API_NAME --query SecretString --output text | ConvertFrom-Json | Select-Object -ExpandProperty api_key
$DB_PASSWORD = aws secretsmanager get-secret-value --secret-id $SECRET_DB_NAME --query SecretString --output text | ConvertFrom-Json | Select-Object -ExpandProperty password

Write-Host "Environment variables recovered:"
Write-Host "RDS_ENDPOINT: $RDS_ENDPOINT"
Write-Host "SERVICE_URL: $FINAL_SERVICE_URL"
Write-Host "API_KEY: $API_KEY"
```

---

## 13. Cleanup

### 13.1 Delete All Resources

```powershell
# App Runnerサービスの削除
$SERVICE_ARN = aws apprunner list-services --query "ServiceSummaryList[?ServiceName=='$APP_RUNNER_SERVICE_NAME'].ServiceArn" --output text
if ($SERVICE_ARN) {
    aws apprunner delete-service --service-arn $SERVICE_ARN
    Write-Host "App Runnerサービスの削除を開始"
}

# RDSインスタンスの削除
aws rds delete-db-instance --db-instance-identifier $RDS_INSTANCE_ID --skip-final-snapshot --delete-automated-backups

# Secrets Managerシークレットの削除
aws secretsmanager delete-secret --secret-id $SECRET_DB_NAME --force-delete-without-recovery
aws secretsmanager delete-secret --secret-id $SECRET_API_NAME --force-delete-without-recovery

# ECRリポジトリの削除
aws ecr delete-repository --repository-name $ECR_REPO_NAME --force

# IAMリソースの削除
aws iam detach-role-policy --role-name "$PREFIX-app-runner-role" --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/$PREFIX-app-runner-policy"
aws iam delete-policy --policy-arn "arn:aws:iam::${ACCOUNT_ID}:policy/$PREFIX-app-runner-policy"
aws iam delete-role --role-name "$PREFIX-app-runner-role"

# DBサブネットグループの削除
aws rds delete-db-subnet-group --db-subnet-group-name "$PREFIX-db-subnet-group"

# セキュリティグループの削除
aws ec2 delete-security-group --group-id $RDS_SG_ID
aws ec2 delete-security-group --group-id $APP_SG_ID

# VPCリソースの削除
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET1_ID
aws ec2 delete-subnet --subnet-id $PUBLIC_SUBNET2_ID
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET1_ID
aws ec2 delete-subnet --subnet-id $PRIVATE_SUBNET2_ID
aws ec2 delete-route-table --route-table-id $ROUTE_TABLE_ID
aws ec2 detach-internet-gateway --internet-gateway-id $IGW_ID --vpc-id $VPC_ID
aws ec2 delete-internet-gateway --internet-gateway-id $IGW_ID
aws ec2 delete-vpc --vpc-id $VPC_ID

Write-Host "All resources deletion initiated. Please wait for completion."
```

---

## Appendix: Important Information Summary

After deployment, you'll need these key endpoints and information:

- **API Server URL**: `https://{service-url}`
- **Health Check URL**: `https://{service-url}/health`
- **API Key**: Stored in Secrets Manager `$PREFIX/api-key`
- **Database Connection**: `{rds-endpoint}:5432`

---

## Architecture Overview

The deployed solution includes:
- **Amazon App Runner**: Hosts the Node.js API server with automatic scaling
- **Amazon RDS for PostgreSQL**: Managed database service for data storage
- **Amazon ECR**: Container registry for application images
- **AWS Secrets Manager**: Secure storage for API keys and database credentials
- **IAM Roles**: Secure service-to-service authentication
- **VPC**: Network isolation and security
- **MCP Server**: Python-based bridge for Claude Desktop integration

## Security Features
- All secrets stored in AWS Secrets Manager
- IAM roles for secure service authentication
- VPC isolation for database access
- API key-based authentication for external access
- Security groups for network-level protection

---

*This guide uses environment variables for flexible deployment across different environments.*
*Simply change the PREFIX value to deploy to different environments or projects.*