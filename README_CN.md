# MCP Driven UX 模板

<div align="center">

<p align="center">
  <img src="assets/MCP_Driven_UX_logo.png" width="648"/>
</p>

![MCP Logo](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)
![TypeScript](https://img.shields.io/badge/TypeScript-3.0+-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![Podman](https://img.shields.io/badge/Podman-Compose-892CA0?logo=podman&logoColor=white)
![AWS](https://img.shields.io/badge/AWS-FF9900?logo=amazonaws&logoColor=white)
![Azure](https://img.shields.io/badge/Azure-0078D4?logo=microsoftazure&logoColor=white)
![Google Cloud](https://img.shields.io/badge/Google_Cloud-4285F4?logo=googlecloud&logoColor=white)
![CI/CD Pipeline](https://github.com/Masa1984a/MCP_Driven_UX_Template/workflows/CI%2FCD%20Pipeline/badge.svg)

<p align="center">
  <a href="./README.md"><img alt="README in English" src="https://img.shields.io/badge/English-d9d9d9"></a>
  <a href="./README_JA.md"><img alt="日本語のREADME" src="https://img.shields.io/badge/日本語-d9d9d9"></a>
  <a href="./README_CN.md"><img alt="简体中文版自述文件" src="https://img.shields.io/badge/简体中文-d9d9d9"></a>
  <a href="./README_TW.md"><img alt="繁體中文版README" src="https://img.shields.io/badge/繁體中文-d9d9d9"></a>
  <a href="./README_KR.md"><img alt="README in Korean" src="https://img.shields.io/badge/한국어-d9d9d9"></a>
  <a href="./README_AR.md"><img alt="README بالعربية" src="https://img.shields.io/badge/العربية-d9d9d9"></a>
</p>

**实现下一代用户体验「MCP Driven UX」的工单管理系统模板**

<a href="https://www.youtube.com/watch?v=Q7iKhyOF_OM" target="_blank" rel="noopener noreferrer">
  <img src="https://img.youtube.com/vi/Q7iKhyOF_OM/0.jpg" alt="Introduction: MCP Driven UX Template">
</a>

*YouTube: Introduction: MCP Driven UX Template*

</div>

## 📋 概述

本项目是「MCP Driven UX」的参考实现，提出了从传统的 MVC（Model-View-Controller）架构向与 LLM 的对话式界面的范式转变。

利用 Model Context Protocol（MCP），本项目以工单管理系统为示例，展示了以下技术栈的角色分工和实现方法：

- **MCP Server (Python)**：LLM 与后端 API 的连接
- **业务逻辑 (TypeScript)**：RESTful API 实现
- **数据模型 (PostgreSQL)**：持久化层管理

## 🎯 概念

### 从 MVC 到 MCP Driven UX

当前的 Web 服务和客户端-服务器应用程序主要基于 MVC 模式。然而，随着 LLM 的兴起和像 MCP 这样的标准化，从基于 UI 的服务向对话式（聊天/语音）界面的转变是可以预期的。

本存储库以工单管理系统为例，实现了一个模板来实现这种转变。

### 架构

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

## ✨ 主要功能

- **工单管理**
  - 工单的创建、更新、搜索、详细显示
  - 历史管理和评论功能
  - 状态管理和负责人分配

- **MCP 集成**
  - 从 Claude Desktop 使用自然语言操作工单
  - 主数据的参考和筛选
  - 实时状态确认

- **企业功能**
  - 基于角色的访问控制
  - 审计跟踪和日志管理
  - 多租户支持

## 🛠️ 技术栈

### 后端
- **MCP Server**：Python 3.9+, MCP SDK
- **API Server**：Node.js, TypeScript, Express, PgTyped
- **Database**：PostgreSQL 16

### 基础设施
- **Container**：Docker/Podman
- **Orchestration**：Docker Compose

## 📥 安装方法

### 先决条件

- Docker 或 Podman（推荐）
- docker-compose 或 podman-compose
- Python 3.9 以上（用于 MCP 服务器）
- Node.js 18 以上（用于 API 服务器）
- Claude Desktop（MCP 客户端）

### 设置步骤

1. **克隆存储库**

```bash
git clone https://github.com/Masa1984a/MCP_Driven_UX_Template.git
cd MCP_Driven_UX_Template
```

2. **认证设置**（Podman/Docker）

```bash
# 对于 Podman
podman login docker.io --username <username>

# 对于 Docker（使用 Podman compose 时也需要）
docker login docker.io --username <username>
```

3. **环境变量设置**

```bash
cp .env.sample .env
# 根据需要编辑 .env 文件（如果要将数据改为日文，请更改为 INIT_LANG=ja）
```

4. **启动容器**

```bash
# 对于 Podman
podman compose up -d

# 对于 Docker
docker-compose up -d
```

5. **Python虚拟环境设置**

为MCP服务器设置Python环境：

```bash
cd ./mcp_server
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell
# Bash/Linux/Mac: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. **Claude for Desktop 的设置**

编辑 Claude for Desktop 的配置文件 `claude_desktop_config.json`：

```json
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "项目目录路径",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**注意**：请将 `项目目录路径` 替换为实际的项目路径。在 Windows 的情况下，需要对路径中的反斜杠进行转义。例如：`C:\\Users\\username\\projects\\ticket-system`

### 数据重置

删除现有数据并重新初始化的情况：

```bash
# 包含卷的停止
podman compose down -v

# 重新启动
podman compose up --build -d
```

## 🔍 使用方法

### 从 Claude Desktop 操作

MCP 服务器启动后，可以从 Claude Desktop 使用自然语言操作工单：

```
# 显示工单列表
"显示当前的工单列表"

# 使用特定条件搜索
"本周预定完成的工单有哪些？"

# 创建工单
"创建新工单。用户主文件更新的请求。"

# 更新工单
"将工单 TCK-0002 的状态更改为处理中"
```

### API 端点

API 服务器提供以下端点：

- `GET /tickets` - 获取工单列表（支持筛选和分页）
- `GET /tickets/:id` - 获取工单详细信息
- `POST /tickets` - 创建新工单
- `PUT /tickets/:id` - 更新工单
- `POST /tickets/:id/history` - 添加历史记录
- `GET /tickets/:id/history` - 获取历史记录

主数据：
- `GET /tickets/master/users` - 用户列表
- `GET /tickets/master/accounts` - 账户列表
- `GET /tickets/master/categories` - 类别列表
- `GET /tickets/master/statuses` - 状态列表

## 📊 数据模型

主要的表结构：

```sql
-- 工单表 (tickets)
- id: 工单ID (TCK-XXXX格式)
- reception_date_time: 受理日期时间
- requestor_id/name: 申请人
- account_id/name: 账户（公司）
- category_id/name: 类别
- status_id/name: 状态
- person_in_charge_id/name: 负责人
- scheduled_completion_date: 预定完成日期
```

详细结构请参阅 `/db/init/en/init.sql` 或 `/db/init/ja/init.sql`。

## 🚀 部署

### 生产环境部署

此应用程序可以部署到以下平台（需要验证）：

- **Google Cloud Platform**
  - Cloud Functions v2（源代码上传）
  - Cloud Run（Docker 镜像）
  - Cloud SQL for PostgreSQL

- **AWS**
  - Lambda + API Gateway
  - ECS/Fargate
  - RDS for PostgreSQL

- **Azure**
  - Functions
  - Container Instances
  - Azure Database for PostgreSQL

有关AWS部署，请参阅我们的 [AWS 部署指南](aws-deploy/Guidebook_AWS.md)
有关Google Cloud Platform部署，请参阅我们的 [Google Cloud Platform 部署指南](gcp-deploy/Guidebook_gcp.md)
有关Azure部署，请参阅我们的 [Azure 部署指南](azure-deploy/Guidebook_Azure.md)

## ☁️ AWS 云环境

### 架构概述

MCP Driven UX 模板可以部署到 Amazon Web Services (AWS) 用于生产环境，提供可扩展的云原生架构：

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│   AWS App Runner │
│    (本地PC)      │                  │  (本地Python)    │                │    (API Server)  │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            AWS 云环境                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Secrets Manager │  │  Amazon ECR     │  │   Amazon RDS    │                │
│  │    (密钥)       │  │ (Container Reg) │  │  (PostgreSQL)   │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │   IAM Roles     │  ← 安全的服务间身份验证                                     │
│  │    (安全性)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 当前 AWS 配置

模板设计为使用以下组件进行灵活部署：

#### 核心服务
- **Amazon App Runner**: 托管 Node.js/TypeScript API 服务器，具有自动扩展功能
- **Amazon RDS for PostgreSQL**: 用于持久数据存储的托管数据库服务
- **Amazon ECR**: 应用程序镜像的容器注册表
- **AWS Secrets Manager**: API 密钥和数据库凭证的安全存储
- **IAM Roles**: 无硬编码密钥的服务间身份验证

#### 安全功能
- 所有敏感数据存储在 AWS Secrets Manager 中
- 使用 IAM 角色进行安全服务身份验证
- 基于 API 密钥的外部访问身份验证
- 通过 AWS VPC 和安全组实现网络安全
- 所有通信支持 HTTPS/SSL

#### 可扩展性和管理
- 基于环境变量的多环境部署配置
- 用于简化部署的 PowerShell 自动化脚本
- 通过 CloudWatch 进行集中式日志和监控
- 一致管理的资源命名约定

### 部署指南

有关 AWS 环境的完整分步部署说明，请参阅：
**[AWS 部署指南](aws-deploy/Guidebook_AWS.md)**

该指南涵盖：
- 先决条件和环境设置
- 使用 AWS CLI 自动化资源配置
- 容器镜像构建和部署到 ECR
- MCP Server 与 AWS API 的集成
- 安全配置和最佳实践
- 故障排除和维护

## ☁️ Google Cloud Platform 云环境

### 架构概述

MCP Driven UX 模板可以部署到 Google Cloud Platform (GCP) 用于生产环境，提供可扩展的云原生架构：

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│  Google Cloud    │
│    (本地PC)      │                  │  (本地Python)    │                │      Run         │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            GCP 云环境                                            │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Secret Manager  │  │ Artifact Registry│  │   Cloud SQL     │                │
│  │    (密钥)       │  │ (Container Reg) │  │  (PostgreSQL)   │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │Service Accounts │  ← 安全的服务间身份验证                                     │
│  │    (安全性)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 当前 GCP 配置

模板设计为使用以下组件进行灵活部署：

#### 核心服务
- **Google Cloud Run**: 托管 Node.js/TypeScript API 服务器，具有自动扩展功能
- **Google Cloud SQL for PostgreSQL**: 用于持久数据存储的托管数据库服务
- **Google Artifact Registry**: 应用程序镜像的容器注册表
- **Google Secret Manager**: API 密钥和数据库凭证的安全存储
- **Service Accounts**: 无硬编码密钥的服务间身份验证

#### 安全功能
- 所有敏感数据存储在 Google Secret Manager 中
- 使用 Service Accounts 进行安全服务身份验证
- 基于 API 密钥的外部访问身份验证
- 通过 GCP VPC 和防火墙规则实现网络安全
- 所有通信支持 HTTPS/SSL

#### 可扩展性和管理
- 基于环境变量的多环境部署配置
- 用于简化部署的 gcloud CLI 自动化
- 通过 Cloud Logging 进行集中式日志和监控
- 一致管理的资源命名约定

### 部署指南

有关 GCP 环境的完整分步部署说明，请参阅：
**[Google Cloud Platform 部署指南](gcp-deploy/Guidebook_gcp.md)**

该指南涵盖：
- 先决条件和环境设置
- 使用 gcloud CLI 自动化资源配置
- 容器镜像构建和部署到 Artifact Registry
- MCP Server 与 GCP API 的集成
- 安全配置和最佳实践
- 故障排除和维护

## ☁️ Azure 云环境

### 架构概述

MCP Driven UX 模板可以部署到 Microsoft Azure 用于生产环境，提供可扩展的云原生架构：

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│  Azure Container │
│    (本地PC)      │                  │  (本地Python)    │                │   Instances      │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                            Azure 云环境                                          │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Key Vault     │  │    Container    │  │   PostgreSQL    │                │
│  │    (密钥)       │  │    Registry     │  │  Flexible Server│                │
│  └─────────────────┘  │     (ACR)       │  │    (数据库)      │                │
│                       └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │ Managed Identity│  ← 安全的服务间身份验证                                     │
│  │    (安全性)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### 当前 Azure 配置

模板设计为使用以下组件进行灵活部署：

#### 核心服务
- **Azure Container Instances**: 托管 Node.js/TypeScript API 服务器
- **Azure Database for PostgreSQL**: 用于持久数据存储的 Flexible Server
- **Azure Container Registry (ACR)**: 容器镜像的私有注册表
- **Azure Key Vault**: API 密钥和数据库凭证的安全存储
- **Managed Identity**: 无硬编码密钥的服务间身份验证

#### 安全功能
- 所有敏感数据存储在 Azure Key Vault 中
- 使用 Managed Identity 进行安全服务身份验证
- 基于 API 密钥的外部访问身份验证
- 通过 Azure 内置防火墙规则实现网络安全
- 通过 Application Gateway 支持 HTTPS/SSL（可选）

#### 可扩展性和管理
- 基于环境变量的多环境部署配置
- 用于简化部署的 PowerShell 自动化脚本
- 集中式日志和监控功能
- 一致管理的资源命名约定

### 部署指南

有关 Azure 环境的完整分步部署说明，请参阅：
**[Azure 部署指南](azure-deploy/Guidebook_Azure.md)**

该指南涵盖：
- 先决条件和环境设置
- 自动化资源配置
- 容器镜像构建和部署
- MCP Server 与 Azure API 的集成
- 安全配置和最佳实践
- 故障排除和维护

## 🧩 可扩展性

此模板可以进行以下扩展：

- **额外的 MCP 工具**：文件操作、外部 API 集成等
- **认证和授权**：OAuth 2.0、SAML 支持
- **通知功能**：电子邮件、Slack、Teams 集成
- **报告功能**：PDF 生成、仪表板
- **多语言支持**：i18n 实现

## 🤝 贡献

欢迎提交拉取请求。对于重大更改，请先创建 Issue 进行讨论。

1. Fork 存储库
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 创建拉取请求

## 🔐 安全性

- 在生产环境中适当管理环境变量
- 绝不要提交数据库凭证
- 适当设置 MCP 服务器的访问控制

## 📄 许可证

[MIT License](LICENSE)

## 🙏 致谢

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - Anthropic 的 SWE（软件工程）Agent
- [Codex CLI](https://github.com/openai/codex) - OpenAI 的 SWE（软件工程）Agent
- [Model Context Protocol](https://modelcontextprotocol.io) - Anthropic 的开放标准
- Claude Desktop - MCP 客户端实现
- 所有贡献者

## ⚠️ 商标和品牌声明

虽然本存储库以 MIT 许可证作为 OSS 发布，但以下产品名称、服务名称和标志是各公司的注册商标或商标。本项目未获得商标持有人的官方赞助、附属或认可，并且与商标持有人之间没有资本或合同关系。

| 商标 | 权利人 | 参考品牌指南 |
| ---- | ------ | ------------ |
| Claude™, Anthropic™ | Anthropic PBC | 请遵循品牌指南<sup>※1</sup> |
| OpenAI®, ChatGPT®, Codex® | OpenAI OpCo, LLC | OpenAI Brand Guidelines<sup>※2</sup> |
| GPT | OpenAI（申请中）等 | 即使作为通用术语使用，也建议避免误识别 |
| PostgreSQL® | The PostgreSQL Global Development Group | — |
| Docker® | Docker, Inc. | — |

<sup>※1</sup> Anthropic 在其官方网站上定期更新商标政策。使用时请检查最新指南。  
<sup>※2</sup> 使用 OpenAI 名称/标志时，需要遵循 OpenAI Brand Guidelines。指南可能会更改，因此建议定期审查。

### API/服务使用条款

- 集成生成式 AI 服务（如 **OpenAI API / Claude API**）时，请遵守各公司的[使用条款](https://openai.com/policies/row-terms-of-use)和 AUP。
- 对于商业用途或大量访问，请务必审查有关速率限制、输出的二次使用和个人信息处理的条款。

> **免责声明：**  
> 本项目按「现状」分发，不提供任何形式的担保。  
> 使用第三方服务风险自负，并受其各自条款的约束。

---

## 📝 变更历史

- **2025-06-04**：新增对 Google Cloud Platform 和 AWS 云环境的支持
- **2025-06-03**：新增对 Azure 云环境的支持
- **2025-05-25**：将示例 SQL 数据从 10 条增加到 50 条工单，以便进行更真实的测试和演示
- **2025-05-23**：将 SQL 查询迁移到 PgTyped 以实现类型安全的 SQL 查询
- **2025-05-18**：初始版本发布，包含 MCP 集成、CRUD 操作和多语言支持

---

<div align="center">
用 ❤️ 为人机交互的未来而构建
</div>