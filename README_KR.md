# MCP Driven UX 템플릿

<div align="center">

<p align="center">
  <img src="assets/MCP_Driven_UX_logo.png" width="648"/>
</p>

![MCP Logo](https://img.shields.io/badge/MCP-Model_Context_Protocol-purple)
![TypeScript](https://img.shields.io/badge/TypeScript-3.0+-blue)
![Python](https://img.shields.io/badge/Python-3.9+-green)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED)
![CI/CD Pipeline](https://github.com/Masa1984a/MCP_Driven_UX_Template/workflows/CI%2FCD%20Pipeline/badge.svg)

<p align="center">
  <a href="./README.md"><img alt="README in English" src="https://img.shields.io/badge/English-d9d9d9"></a>
  <a href="./README_JA.md"><img alt="日本語のREADME" src="https://img.shields.io/badge/日本語-d9d9d9"></a>
  <a href="./README_CN.md"><img alt="简体中文版自述文件" src="https://img.shields.io/badge/简体中文-d9d9d9"></a>
  <a href="./README_TW.md"><img alt="繁體中文版README" src="https://img.shields.io/badge/繁體中文-d9d9d9"></a>
  <a href="./README_KR.md"><img alt="README in Korean" src="https://img.shields.io/badge/한국어-d9d9d9"></a>
  <a href="./README_AR.md"><img alt="README بالعربية" src="https://img.shields.io/badge/العربية-d9d9d9"></a>
</p>

**차세대 사용자 경험 「MCP Driven UX」를 실현하는 티켓 관리 시스템 템플릿**

<a href="https://www.youtube.com/watch?v=Q7iKhyOF_OM" target="_blank" rel="noopener noreferrer">
  <img src="https://img.youtube.com/vi/Q7iKhyOF_OM/0.jpg" alt="Introduction: MCP Driven UX Template">
</a>

*YouTube: Introduction: MCP Driven UX Template*

</div>

## 📋 개요

이 프로젝트는 전통적인 MVC(Model-View-Controller) 아키텍처에서 LLM과의 대화형 인터페이스로의 패러다임 전환을 제안하는 「MCP Driven UX」의 참조 구현입니다.

Model Context Protocol(MCP)을 활용하여, 티켓 관리 시스템을 샘플로 다음 기술 스택의 역할 분담과 구현 방법을 보여줍니다:

- **MCP Server (Python)**: LLM과 백엔드 API의 연계
- **비즈니스 로직 (TypeScript)**: RESTful API 구현
- **데이터 모델 (PostgreSQL)**: 영속화 계층 관리

## 🎯 컨셉

### MVC에서 MCP Driven UX로

현재의 웹 서비스와 클라이언트-서버 애플리케이션은 주로 MVC 패턴을 기반으로 합니다. 그러나 LLM의 등장과 MCP와 같은 표준화로 인해 UI 기반 서비스에서 대화형(채팅/음성) 인터페이스로의 전환이 예상됩니다.

이 리포지토리는 그 전환을 실현하기 위한 템플릿으로서 티켓 관리 시스템을 예제로 구현하고 있습니다.

### 아키텍처

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

## ✨ 주요 기능

- **티켓 관리**
  - 티켓 생성, 업데이트, 검색, 상세 표시
  - 이력 관리 및 댓글 기능
  - 상태 관리 및 담당자 할당

- **MCP 통합**
  - Claude Desktop에서의 자연어를 통한 티켓 조작
  - 마스터 데이터 참조 및 필터링
  - 실시간 상태 확인

- **엔터프라이즈 기능**
  - 역할 기반 접근 제어
  - 감사 추적 및 로그 관리
  - 멀티테넌트 지원

## 🛠️ 기술 스택

### 백엔드
- **MCP Server**: Python 3.9+, MCP SDK
- **API Server**: Node.js, TypeScript, Express, PgTyped
- **Database**: PostgreSQL 16

### 인프라
- **Container**: Docker/Podman
- **Orchestration**: Docker Compose

## 📥 설치 방법

### 사전 요구사항

- Docker 또는 Podman (권장)
- docker-compose 또는 podman-compose
- Python 3.9 이상 (MCP 서버용)
- Node.js 18 이상 (API 서버용)
- Claude Desktop (MCP 클라이언트)

### 설정 단계

1. **리포지토리 클론**

```bash
git clone https://github.com/Masa1984a/MCP_Driven_UX_Template.git
cd MCP_Driven_UX_Template
```

2. **인증 설정** (Podman/Docker)

```bash
# Podman의 경우
podman login docker.io --username <username>

# Docker의 경우 (Podman으로 compose 할 때도 필요)
docker login docker.io --username <username>
```

3. **환경 변수 설정**

```bash
cp .env.sample .env
# 필요에 따라 .env 파일을 편집 (데이터를 일본어로 변경하려면 INIT_LANG=ja로 변경하세요)
```

4. **컨테이너 시작**

```bash
# Podman의 경우
podman compose up -d

# Docker의 경우
docker-compose up -d
```

5. **Python 가상 환경 설정**

MCP 서버를 위한 Python 환경을 설정합니다:

```bash
cd ./mcp_server
python -m venv .venv
.venv\Scripts\Activate.ps1  # Windows PowerShell인 경우
# Bash/Linux/Mac인 경우: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. **Claude for Desktop 설정**

Claude for Desktop 설정 파일 `claude_desktop_config.json`을 편집:

```json
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "프로젝트 디렉토리 경로",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**주의**: `프로젝트 디렉토리 경로`를 실제 프로젝트 경로로 바꿔주세요. Windows의 경우 경로의 백슬래시를 이스케이프해야 합니다. 예: `C:\\Users\\username\\projects\\ticket-system`

### 데이터 리셋

기존 데이터를 삭제하고 재초기화하는 경우:

```bash
# 볼륨을 포함하여 중지
podman compose down -v

# 재시작
podman compose up --build -d
```

## 🔍 사용 방법

### Claude Desktop에서의 조작

MCP 서버가 시작되면 Claude Desktop에서 다음과 같은 자연어로 티켓을 조작할 수 있습니다:

```
# 티켓 목록 표시
"현재 티켓 목록을 보여줘"

# 특정 조건으로 검색
"이번 주 완료 예정인 티켓은?"

# 티켓 생성
"새 티켓을 만들어줘. 사용자 마스터 업데이트 요청."

# 티켓 업데이트
"티켓 TCK-0002의 상태를 처리 중으로 변경"
```

### API 엔드포인트

API 서버는 다음 엔드포인트를 제공합니다:

- `GET /tickets` - 티켓 목록 조회 (필터링 및 페이지네이션 지원)
- `GET /tickets/:id` - 티켓 상세 조회
- `POST /tickets` - 새 티켓 생성
- `PUT /tickets/:id` - 티켓 업데이트
- `POST /tickets/:id/history` - 이력 추가
- `GET /tickets/:id/history` - 이력 조회

마스터 데이터:
- `GET /tickets/master/users` - 사용자 목록
- `GET /tickets/master/accounts` - 계정 목록
- `GET /tickets/master/categories` - 카테고리 목록
- `GET /tickets/master/statuses` - 상태 목록

## 📊 데이터 모델

주요 테이블 구조:

```sql
-- 티켓 테이블 (tickets)
- id: 티켓 ID (TCK-XXXX 형식)
- reception_date_time: 접수 일시
- requestor_id/name: 요청자
- account_id/name: 계정 (회사)
- category_id/name: 카테고리
- status_id/name: 상태
- person_in_charge_id/name: 담당자
- scheduled_completion_date: 완료 예정일
```

자세한 구조는 `/db/init/en/init.sql` 또는 `/db/init/ja/init.sql`을 참조하세요.

## 🚀 배포

### 프로덕션 환경 배포

이 애플리케이션은 다음 플랫폼에 배포 가능합니다 (검증 필요):

- **Google Cloud Platform**
  - Cloud Functions v2 (소스 업로드)
  - Cloud Run (Docker 이미지)
  - Cloud SQL for PostgreSQL

- **AWS**
  - Lambda + API Gateway
  - ECS/Fargate
  - RDS for PostgreSQL

- **Azure**
  - Functions
  - Container Instances
  - Azure Database for PostgreSQL

## 🧩 확장성

이 템플릿은 다음과 같은 확장이 가능합니다:

- **추가 MCP 도구**: 파일 조작, 외부 API 연동 등
- **인증/인가**: OAuth 2.0, SAML 지원
- **알림 기능**: 이메일, Slack, Teams 연동
- **보고서 기능**: PDF 생성, 대시보드
- **다국어 지원**: i18n 구현

## 🤝 기여

풀 리퀘스트는 환영합니다. 큰 변경사항의 경우 먼저 이슈를 생성하여 논의해 주세요.

1. 리포지토리 포크
2. 기능 브랜치 생성 (`git checkout -b feature/AmazingFeature`)
3. 변경사항 커밋 (`git commit -m 'Add some AmazingFeature'`)
4. 브랜치에 푸시 (`git push origin feature/AmazingFeature`)
5. 풀 리퀘스트 생성

## 🔐 보안

- 프로덕션 환경에서는 환경 변수를 적절히 관리하세요
- 데이터베이스 인증 정보는 절대 커밋하지 마세요
- MCP 서버의 접근 제어를 적절히 설정하세요

## 📄 라이선스

[MIT License](LICENSE)

## 🙏 감사의 말

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - Anthropic의 SWE(Software Engineering) Agent
- [Codex CLI](https://github.com/openai/codex) - OpenAI의 SWE(Software Engineering) Agent
- [Model Context Protocol](https://modelcontextprotocol.io) - Anthropic의 오픈 스탠다드
- Claude Desktop - MCP 클라이언트 구현
- 모든 기여자 여러분

## ⚠️ 상표 및 브랜드에 관한 주의사항

본 리포지토리는 OSS로서 MIT License로 공개되어 있지만, 아래의 제품명·서비스명·로고는 각 회사의 등록상표 또는 상표입니다. 프로젝트는 각 회사의 공식적인 후원·제휴·승인을 받지 않았으며, 상표권자와의 자본·계약 관계는 없습니다.

| 상표 | 권리자 | 참고 브랜드 가이드라인 |
| ---- | ------ | ---------------------- |
| Claude™, Anthropic™ | Anthropic PBC | 브랜드 가이드라인을 따라 이용해 주세요<sup>※1</sup> |
| OpenAI®, ChatGPT®, Codex® | OpenAI OpCo, LLC | OpenAI Brand Guidelines<sup>※2</sup> |
| GPT | OpenAI (신청 중) 외 | 일반 명사로 사용하는 경우에도 오인을 피하는 표기를 권장 |
| PostgreSQL® | The PostgreSQL Global Development Group | — |
| Docker® | Docker, Inc. | — |

<sup>※1</sup> Anthropic은 공식 사이트에서 상표 정책을 수시로 업데이트하고 있습니다. 이용 시 최신 지침을 확인해 주세요.  
<sup>※2</sup> OpenAI의 명칭·로고를 사용할 때는 OpenAI Brand Guidelines를 따라야 합니다. 가이드라인은 변경될 수 있으므로 정기적인 확인을 권장합니다.

### API·서비스 이용약관

- **OpenAI API / Claude API** 등의 생성 AI 서비스를 통합하는 경우 각 회사의 [Terms of Use](https://openai.com/policies/row-terms-of-use) 및 AUP를 준수해 주세요.
- 상업적 이용이나 대량 액세스가 예상되는 경우는 레이트 제한·출력의 2차 이용 조건·개인정보 취급에 관한 조항을 반드시 확인해 주세요.

> **Disclaimer:**  
> This project is distributed "AS IS", without warranty of any kind.  
> Use of third-party services is at your own risk and subject to their respective terms.

---

## 📝 변경 이력

- **2025-05-25**: 샘플 SQL 데이터를 10개에서 50개 티켓으로 증가시켜 보다 현실적인 테스트와 시연을 가능하게 함
- **2025-05-23**: SQL 쿼리를 PgTyped로 마이그레이션하여 타입 안전 SQL 쿼리 구현
- **2025-05-18**: MCP 통합, CRUD 작업 및 다국어 지원을 포함한 초기 릴리스

---

<div align="center">
인간-AI 상호작용의 미래를 위해 ❤️로 구축되었습니다
</div>