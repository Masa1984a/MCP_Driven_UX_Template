<div dir="rtl">

# قالب MCP Driven UX

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

**قالب نظام إدارة التذاكر لتحقيق تجربة المستخدم من الجيل التالي "MCP Driven UX"**

<a href="https://www.youtube.com/watch?v=Q7iKhyOF_OM" target="_blank" rel="noopener noreferrer">
  <img src="https://img.youtube.com/vi/Q7iKhyOF_OM/0.jpg" alt="Introduction: MCP Driven UX Template">
</a>

*YouTube: Introduction: MCP Driven UX Template*

</div>

## 📋 نظرة عامة

هذا المشروع هو تطبيق مرجعي لـ "MCP Driven UX" الذي يقترح تحولاً نموذجياً من معمارية MVC (Model-View-Controller) التقليدية إلى واجهات تفاعلية مع نماذج اللغة الكبيرة (LLMs).

باستخدام بروتوكول سياق النموذج (MCP)، يعرض هذا المشروع تقسيم الأدوار وطرق التنفيذ للمكدس التقني التالي باستخدام نظام إدارة التذاكر كعينة:

- **خادم MCP (Python)**: التكامل بين LLM و API الخلفية
- **منطق الأعمال (TypeScript)**: تنفيذ RESTful API
- **نموذج البيانات (PostgreSQL)**: إدارة طبقة الاستمرارية

## 🎯 المفهوم

### من MVC إلى MCP Driven UX

تعتمد خدمات الويب الحالية والتطبيقات من نوع العميل-الخادم بشكل أساسي على نمط MVC. ومع ذلك، مع صعود نماذج اللغة الكبيرة والمعايير مثل MCP، من المتوقع الانتقال من الخدمات القائمة على واجهة المستخدم إلى الواجهات التفاعلية (الدردشة/الصوت).

ينفذ هذا المستودع نظام إدارة التذاكر كقالب مثال لتحقيق هذا التحول.

### البنية

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

## ✨ الميزات الرئيسية

- **إدارة التذاكر**
  - إنشاء وتحديث والبحث وعرض تفاصيل التذاكر
  - إدارة السجل ووظيفة التعليقات
  - إدارة الحالة وتخصيص المسؤول

- **تكامل MCP**
  - عمليات التذاكر باللغة الطبيعية من Claude Desktop
  - مرجع البيانات الرئيسية والتصفية
  - تأكيد الحالة في الوقت الفعلي

- **ميزات المؤسسة**
  - التحكم في الوصول القائم على الأدوار
  - سجل التدقيق وإدارة السجلات
  - دعم متعدد المستأجرين

## 🛠️ المكدس التقني

### الخلفية
- **خادم MCP**: Python 3.9+، MCP SDK
- **خادم API**: Node.js، TypeScript، Express، PgTyped
- **قاعدة البيانات**: PostgreSQL 16

### البنية التحتية
- **الحاوية**: Docker/Podman
- **التنسيق**: Docker Compose

## 📥 التثبيت

### المتطلبات الأساسية

- Docker أو Podman (موصى به)
- docker-compose أو podman-compose
- Python 3.9+ (لخادم MCP)
- Node.js 18+ (لخادم API)
- Claude Desktop (عميل MCP)

### خطوات الإعداد

1. **استنساخ المستودع**

```bash
git clone https://github.com/Masa1984a/MCP_Driven_UX_Template.git
cd MCP_Driven_UX_Template
```

2. **إعداد المصادقة** (Podman/Docker)

```bash
# لـ Podman
podman login docker.io --username <username>

# لـ Docker (مطلوب أيضًا عند استخدام compose مع Podman)
docker login docker.io --username <username>
```

3. **إعداد متغيرات البيئة**

```bash
cp .env.sample .env
# تحرير ملف .env حسب الحاجة (لتغيير البيانات إلى اليابانية، غيّر إلى INIT_LANG=ja)
```

4. **بدء الحاويات**

```bash
# لـ Podman
podman compose up -d

# لـ Docker
docker-compose up -d
```

5. **إعداد بيئة Python الافتراضية**

قم بإعداد بيئة Python لخادم MCP:

```bash
cd ./mcp_server
python -m venv .venv
.venv\Scripts\Activate.ps1  # لـ Windows PowerShell
# لـ Bash/Linux/Mac: source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

6. **تكوين Claude for Desktop**

حرر ملف تكوين Claude for Desktop `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "TicketManagementSystem": {
      "command": "uv",
      "args": [
        "--directory", "مسار دليل المشروع",
        "run",
        "mcp_server.py"
      ]
    }
  }
}
```

**ملاحظة**: استبدل `مسار دليل المشروع` بمسار مشروعك الفعلي. في Windows، يجب تخطي الخطوط المائلة العكسية في المسار. مثال: `C:\\Users\\username\\projects\\ticket-system`

### إعادة تعيين البيانات

لحذف البيانات الموجودة وإعادة التهيئة:

```bash
# الإيقاف مع الحجوم
podman compose down -v

# إعادة التشغيل
podman compose up --build -d
```

## 🔍 الاستخدام

### العمليات من Claude Desktop

بمجرد تشغيل خادم MCP، يمكنك تشغيل التذاكر باللغة الطبيعية من Claude Desktop:

```
# عرض قائمة التذاكر
"أظهر قائمة التذاكر الحالية"

# البحث بشروط محددة  
"ما هي التذاكر المقرر إنجازها هذا الأسبوع؟"

# إنشاء تذكرة
"أنشئ تذكرة جديدة. طلب تحديث البيانات الرئيسية للمستخدم."

# تحديث تذكرة
"غيّر حالة التذكرة TCK-0002 إلى قيد التنفيذ"
```

### نقاط النهاية API

يوفر خادم API نقاط النهاية التالية:

- `GET /tickets` - الحصول على قائمة التذاكر (مع التصفية والترقيم)
- `GET /tickets/:id` - الحصول على تفاصيل التذكرة
- `POST /tickets` - إنشاء تذكرة جديدة
- `PUT /tickets/:id` - تحديث التذكرة
- `POST /tickets/:id/history` - إضافة السجل
- `GET /tickets/:id/history` - الحصول على السجل

البيانات الرئيسية:
- `GET /tickets/master/users` - قائمة المستخدمين
- `GET /tickets/master/accounts` - قائمة الحسابات
- `GET /tickets/master/categories` - قائمة الفئات
- `GET /tickets/master/statuses` - قائمة الحالات

## 📊 نموذج البيانات

هيكل الجدول الرئيسي:

```sql
-- جدول التذاكر (tickets)
- id: معرف التذكرة (تنسيق TCK-XXXX)
- reception_date_time: تاريخ ووقت الاستلام
- requestor_id/name: مقدم الطلب
- account_id/name: الحساب (الشركة)
- category_id/name: الفئة
- status_id/name: الحالة
- person_in_charge_id/name: الشخص المسؤول
- scheduled_completion_date: تاريخ الإنجاز المقرر
```

للحصول على البنية التفصيلية، راجع `/db/init/en/init.sql` أو `/db/init/ja/init.sql`.

## 🚀 النشر

### النشر في الإنتاج

يمكن نشر هذا التطبيق على المنصات التالية (يتطلب التحقق):

- **Google Cloud Platform**
  - Cloud Functions v2 (تحميل المصدر)
  - Cloud Run (صورة Docker)
  - Cloud SQL for PostgreSQL

- **AWS**
  - Lambda + API Gateway
  - ECS/Fargate
  - RDS for PostgreSQL

- **Azure**
  - Functions
  - Container Instances
  - Azure Database for PostgreSQL

للنشر على AWS، راجع [دليل النشر على AWS](aws-deploy/Guidebook_AWS.md)
للنشر على Google Cloud Platform، راجع [دليل النشر على Google Cloud Platform](gcp-deploy/Guidebook_gcp.md)
للنشر على Azure، راجع [دليل النشر على Azure](azure-deploy/Guidebook_Azure.md)

## ☁️ بيئة AWS السحابية

### نظرة عامة على البنية

يمكن نشر قالب MCP Driven UX على Amazon Web Services (AWS) للاستخدام الإنتاجي، مما يوفر بنية سحابية أصلية قابلة للتطوير:

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│   AWS App Runner │
│   (جهاز محلي)    │                  │ (Python محلي)   │                │    (API Server)  │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           بيئة AWS السحابية                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Secrets Manager │  │  Amazon ECR     │  │   Amazon RDS    │                │
│  │   (الأسرار)     │  │ (Container Reg) │  │  (PostgreSQL)   │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │   IAM Roles     │  ← مصادقة آمنة بين الخدمات                                  │
│  │    (الأمان)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### تكوين AWS الحالي

تم تصميم القالب للنشر المرن مع المكونات التالية:

#### الخدمات الأساسية
- **Amazon App Runner**: يستضيف خادم API بـ Node.js/TypeScript مع التوسع التلقائي
- **Amazon RDS for PostgreSQL**: خدمة قاعدة البيانات المُدارة لتخزين البيانات الدائم
- **Amazon ECR**: سجل الحاويات لصور التطبيقات
- **AWS Secrets Manager**: تخزين آمن لمفاتيح API وبيانات اعتماد قاعدة البيانات
- **IAM Roles**: مصادقة بين الخدمات بدون أسرار مشفرة بقوة

#### ميزات الأمان
- جميع البيانات الحساسة مخزنة في AWS Secrets Manager
- أدوار IAM للمصادقة الآمنة للخدمات
- مصادقة قائمة على مفتاح API للوصول الخارجي
- أمان الشبكة من خلال AWS VPC ومجموعات الأمان
- دعم HTTPS/SSL لجميع الاتصالات

#### قابلية التطوير والإدارة
- تكوين قائم على متغيرات البيئة لنشر متعدد البيئات
- نصوص PowerShell للأتمتة لنشر مبسط
- قدرات تسجيل ومراقبة مركزية عبر CloudWatch
- اتفاقيات تسمية الموارد للإدارة المتسقة

### دليل النشر

للحصول على تعليمات النشر التفصيلية خطوة بخطوة لبيئة AWS، راجع:
**[دليل النشر على AWS](aws-deploy/Guidebook_AWS.md)**

يغطي الدليل:
- المتطلبات الأساسية وإعداد البيئة
- توفير الموارد المؤتمت باستخدام AWS CLI
- بناء ونشر صور الحاويات إلى ECR
- تكامل MCP Server مع AWS API
- تكوين الأمان وأفضل الممارسات
- استكشاف الأخطاء وإصلاحها والصيانة

## ☁️ بيئة Google Cloud Platform السحابية

### نظرة عامة على البنية

يمكن نشر قالب MCP Driven UX على Google Cloud Platform (GCP) للاستخدام الإنتاجي، مما يوفر بنية سحابية أصلية قابلة للتطوير:

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│  Google Cloud    │
│   (جهاز محلي)    │                  │ (Python محلي)   │                │      Run         │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           بيئة GCP السحابية                                      │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │ Secret Manager  │  │ Artifact Registry│  │   Cloud SQL     │                │
│  │   (الأسرار)     │  │ (Container Reg) │  │  (PostgreSQL)   │                │
│  └─────────────────┘  └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │Service Accounts │  ← مصادقة آمنة بين الخدمات                                  │
│  │    (الأمان)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### تكوين GCP الحالي

تم تصميم القالب للنشر المرن مع المكونات التالية:

#### الخدمات الأساسية
- **Google Cloud Run**: يستضيف خادم API بـ Node.js/TypeScript مع التوسع التلقائي
- **Google Cloud SQL for PostgreSQL**: خدمة قاعدة البيانات المُدارة لتخزين البيانات الدائم
- **Google Artifact Registry**: سجل الحاويات لصور التطبيقات
- **Google Secret Manager**: تخزين آمن لمفاتيح API وبيانات اعتماد قاعدة البيانات
- **Service Accounts**: مصادقة بين الخدمات بدون أسرار مشفرة بقوة

#### ميزات الأمان
- جميع البيانات الحساسة مخزنة في Google Secret Manager
- حسابات الخدمة للمصادقة الآمنة للخدمات
- مصادقة قائمة على مفتاح API للوصول الخارجي
- أمان الشبكة من خلال GCP VPC وقواعد الجدار الناري
- دعم HTTPS/SSL لجميع الاتصالات

#### قابلية التطوير والإدارة
- تكوين قائم على متغيرات البيئة لنشر متعدد البيئات
- أتمتة gcloud CLI للنشر المبسط
- قدرات تسجيل ومراقبة مركزية عبر Cloud Logging
- اتفاقيات تسمية الموارد للإدارة المتسقة

### دليل النشر

للحصول على تعليمات النشر التفصيلية خطوة بخطوة لبيئة GCP، راجع:
**[دليل النشر على Google Cloud Platform](gcp-deploy/Guidebook_gcp.md)**

يغطي الدليل:
- المتطلبات الأساسية وإعداد البيئة
- توفير الموارد المؤتمت باستخدام gcloud CLI
- بناء ونشر صور الحاويات إلى Artifact Registry
- تكامل MCP Server مع GCP API
- تكوين الأمان وأفضل الممارسات
- استكشاف الأخطاء وإصلاحها والصيانة

## ☁️ بيئة Azure السحابية

### نظرة عامة على البنية

يمكن نشر قالب MCP Driven UX على Microsoft Azure للاستخدام الإنتاجي، مما يوفر بنية سحابية أصلية قابلة للتطوير:

```
┌─────────────────┐    MCP(STDIO)    ┌─────────────────┐    HTTP/API    ┌──────────────────┐
│  Claude Desktop │◄────────────────►│   MCP Server    │◄──────────────►│  Azure Container │
│   (جهاز محلي)    │                  │ (Python محلي)   │                │   Instances      │
└─────────────────┘                  └─────────────────┘                └─────────┬────────┘
                                                                                   │
                                                                                   ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│                           بيئة Azure السحابية                                    │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐                │
│  │   Key Vault     │  │    Container    │  │   PostgreSQL    │                │
│  │   (الأسرار)     │  │    Registry     │  │  Flexible Server│                │
│  └─────────────────┘  │     (ACR)       │  │  (قاعدة البيانات) │                │
│                       └─────────────────┘  └─────────────────┘                │
│                                                                                │
│  ┌─────────────────┐                                                           │
│  │ Managed Identity│  ← مصادقة آمنة بين الخدمات                                  │
│  │    (الأمان)      │                                                           │
│  └─────────────────┘                                                           │
└──────────────────────────────────────────────────────────────────────────────────┘
```

### تكوين Azure الحالي

تم تصميم القالب للنشر المرن مع المكونات التالية:

#### الخدمات الأساسية
- **Azure Container Instances**: يستضيف خادم API بـ Node.js/TypeScript
- **Azure Database for PostgreSQL**: Flexible Server لتخزين البيانات الدائم
- **Azure Container Registry (ACR)**: سجل خاص لصور الحاويات
- **Azure Key Vault**: تخزين آمن لمفاتيح API وبيانات اعتماد قاعدة البيانات
- **Managed Identity**: مصادقة بين الخدمات بدون أسرار مشفرة بقوة

#### ميزات الأمان
- جميع البيانات الحساسة مخزنة في Azure Key Vault
- Managed Identity للمصادقة الآمنة للخدمات
- مصادقة قائمة على مفتاح API للوصول الخارجي
- أمان الشبكة من خلال قواعد الجدار الناري المدمجة في Azure
- دعم HTTPS/SSL عبر Application Gateway (اختياري)

#### قابلية التطوير والإدارة
- تكوين قائم على متغيرات البيئة لنشر متعدد البيئات
- نصوص PowerShell للأتمتة لنشر مبسط
- قدرات تسجيل ومراقبة مركزية
- اتفاقيات تسمية الموارد للإدارة المتسقة

### دليل النشر

للحصول على تعليمات النشر التفصيلية خطوة بخطوة لبيئة Azure، راجع:
**[دليل النشر على Azure](azure-deploy/Guidebook_Azure.md)**

يغطي الدليل:
- المتطلبات الأساسية وإعداد البيئة
- توفير الموارد المؤتمت
- بناء ونشر صور الحاويات
- تكامل MCP Server مع Azure API
- تكوين الأمان وأفضل الممارسات
- استكشاف الأخطاء وإصلاحها والصيانة

## 🧩 القابلية للتوسع

يمكن توسيع هذا القالب بـ:

- **أدوات MCP إضافية**: عمليات الملفات، تكامل API الخارجي، إلخ.
- **المصادقة/التفويض**: دعم OAuth 2.0، SAML
- **ميزات الإشعارات**: تكامل البريد الإلكتروني، Slack، Teams
- **ميزات التقارير**: إنشاء PDF، لوحات القيادة
- **دعم متعدد اللغات**: تنفيذ i18n

## 🤝 المساهمة

نرحب بطلبات السحب. للتغييرات الكبيرة، يرجى إنشاء مسألة أولاً للمناقشة.

1. Fork المستودع
2. إنشاء فرع الميزة (`git checkout -b feature/AmazingFeature`)
3. تثبيت التغييرات (`git commit -m 'Add some AmazingFeature'`)
4. دفع إلى الفرع (`git push origin feature/AmazingFeature`)
5. إنشاء طلب سحب

## 🔐 الأمان

- إدارة متغيرات البيئة بشكل صحيح في الإنتاج
- عدم تثبيت بيانات اعتماد قاعدة البيانات أبدًا
- تكوين التحكم في الوصول إلى خادم MCP بشكل مناسب

## 📄 الترخيص

[MIT License](LICENSE)

## 🙏 شكر وتقدير

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code/overview) - وكيل هندسة البرمجيات (SWE) من Anthropic
- [Codex CLI](https://github.com/openai/codex) - وكيل هندسة البرمجيات (SWE) من OpenAI
- [Model Context Protocol](https://modelcontextprotocol.io) - معيار مفتوح من Anthropic
- Claude Desktop - تنفيذ عميل MCP
- جميع المساهمين

## ⚠️ إشعار العلامات التجارية

بينما يتم توزيع هذا المستودع كـ OSS بموجب ترخيص MIT، فإن أسماء المنتجات وأسماء الخدمات والشعارات التالية هي علامات تجارية مسجلة أو علامات تجارية لشركاتها. لا يحصل هذا المشروع على رعاية رسمية أو انتساب أو موافقة من أصحاب العلامات التجارية، ولا توجد علاقة رأسمالية أو تعاقدية معهم.

| العلامة التجارية | صاحب الحقوق | دليل العلامة التجارية المرجعي |
| --------------- | ----------- | ----------------------------- |
| Claude™, Anthropic™ | Anthropic PBC | يرجى اتباع إرشادات العلامة التجارية<sup>※1</sup> |
| OpenAI®, ChatGPT®, Codex® | OpenAI OpCo, LLC | OpenAI Brand Guidelines<sup>※2</sup> |
| GPT | OpenAI (معلق) وآخرون | يوصى بتجنب سوء التعرف حتى عند استخدامه كمصطلح عام |
| PostgreSQL® | The PostgreSQL Global Development Group | — |
| Docker® | Docker, Inc. | — |

<sup>※1</sup> تحدث Anthropic سياسات العلامة التجارية دورياً على موقعها الرسمي. يرجى التحقق من أحدث الإرشادات عند الاستخدام.  
<sup>※2</sup> عند استخدام أسماء/شعارات OpenAI، يجب اتباع OpenAI Brand Guidelines. قد تتغير الإرشادات، لذا يوصى بالمراجعة الدورية.

### شروط استخدام API/الخدمة

- عند دمج خدمات الذكاء الاصطناعي التوليدي مثل **OpenAI API / Claude API**، يجب الامتثال لـ [شروط الاستخدام](https://openai.com/policies/row-terms-of-use) و AUP لكل شركة.
- للاستخدام التجاري أو الوصول الكبير، تأكد من مراجعة الشروط المتعلقة بحدود المعدل والاستخدام الثانوي للمخرجات ومعالجة المعلومات الشخصية.

> **إخلاء المسؤولية:**  
> يتم توزيع هذا المشروع "كما هو"، دون ضمان من أي نوع.  
> استخدام خدمات الطرف الثالث على مسؤوليتك الخاصة ويخضع لشروطها المعنية.

---

## 📝 سجل التغييرات

- **2025-06-04**: إضافة دعم بيئتي Google Cloud Platform و AWS السحابيتين
- **2025-06-03**: إضافة دعم بيئة Azure السحابية
- **2025-05-25**: زيادة بيانات SQL العينة من 10 إلى 50 تذكرة للاختبار والعرض الأكثر واقعية
- **2025-05-23**: تم ترحيل استعلامات SQL إلى PgTyped لتحقيق استعلامات SQL آمنة النوع
- **2025-05-18**: الإصدار الأولي مع تكامل MCP وعمليات CRUD ودعم متعدد اللغات

---

<div align="center">
بُني بـ ❤️ لمستقبل التفاعل بين الإنسان والذكاء الاصطناعي
</div>

</div>