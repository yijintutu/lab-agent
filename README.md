# 实验室预约与管理系统

一个基于 Vue 3 与 FastAPI 的实验室管理 Web 应用，提供实验室和设备管理、预约与审核、用户管理，以及可选的 AI 对话和知识库检索能力。

## 项目简介

系统面向实验室使用者和管理员：使用者可以查看实验室、设备并提交预约；管理员可以维护实验室和设备、管理用户及审核预约。AI 助手及知识库索引功能可通过后端配置启用。

## 功能特性

- 用户注册、登录、个人资料和密码管理，采用 JWT 认证。
- 实验室与设备信息查询及管理。
- 实验室预约、预约记录查询、取消和管理员审核。
- 文件上传，并通过 `/uploads` 提供静态访问。
- 可选 AI 对话和知识库索引重建。
- 知识库包含实验室预约规则、开放时间、设备使用和安全规范等 Markdown 文档。

## 技术栈

| 部分     | 技术                                                           |
| -------- | -------------------------------------------------------------- |
| 前端     | Vue 3、Vue Router、Element Plus、Axios、Vite                   |
| 后端     | Python、FastAPI、Uvicorn、Pydantic Settings                    |
| 数据访问 | SQLAlchemy 2、PyMySQL、aiosqlite                               |
| AI / RAG | LangChain、LangGraph、Chroma；可选 Hugging Face 本地 Embedding |

## 环境要求

- Node.js `^22.18.0` 或 `>=24.12.0`（由前端 `package.json` 声明）。
- Python：项目未声明最低版本，需使用与后端依赖兼容的 Python 版本。<!-- TODO: 待补充 -->
- 一个与 `DATABASE_URL` 匹配且可访问的数据库；具体数据库类型、版本及初始化方式需按部署环境配置。

## 快速开始

前端和后端分别在两个终端中启动。

### 1. 配置后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

在 `backend/.env` 中设置必需配置。以下是配置项示意，尖括号内容必须替换为实际值：

```dotenv
DATABASE_URL=<SQLAlchemy 数据库连接 URL>
JWT_SECRET_KEY=<用于签发 JWT 的随机密钥>
```

后端通过 SQLAlchemy `create_engine` 连接 `DATABASE_URL`，并在应用启动时创建缺失的数据表。请先准备数据库及其账号；仓库没有提供数据库初始化数据或迁移脚本。

### 2. 启动后端

在 `backend` 目录、虚拟环境已激活且配置已填写的终端执行：

```powershell
python -m uvicorn app.main:app --reload
```

后端默认监听 `http://127.0.0.1:8000`。FastAPI 接口文档可通过 `http://127.0.0.1:8000/docs` 访问。

### 3. 启动前端

```powershell
cd frontend
npm install
npm run dev
```

打开 Vite 输出的本地地址（默认 `http://localhost:5173`）。开发服务器将 `/api` 和 `/uploads` 请求代理到 `http://127.0.0.1:8000`。

## 配置说明

后端配置从 `backend/.env` 和环境变量读取。除下表注明默认值外，配置项均按代码中的类型读取。

| 配置项                                                                   | 默认值 / 要求                            | 说明                                                    |
| ------------------------------------------------------------------------ | ---------------------------------------- | ------------------------------------------------------- |
| `DATABASE_URL`                                                           | 必填                                     | SQLAlchemy 数据库连接 URL。                             |
| `JWT_SECRET_KEY`                                                         | 必填                                     | JWT 签名密钥。                                          |
| `JWT_ALGORITHM`                                                          | `HS256`                                  | JWT 签名算法。                                          |
| `JWT_EXPIRE_HOURS`                                                       | `24`                                     | JWT 有效期（小时）。                                    |
| `AI_ENABLED`                                                             | `false`                                  | 启用 AI 服务及对话图。启用后还需配置模型及相关服务。    |
| `AI_TOOLS_ENABLED`                                                       | `false`                                  | AI 工具开关。                                           |
| `AI_WRITE_TOOLS_ENABLED`                                                 | `false`                                  | AI 写入类工具开关。                                     |
| `AI_AGENT_TIMEOUT_SECONDS`                                               | `180.0`                                  | AI Agent 超时秒数。                                     |
| `AI_CHECKPOINT_DB`                                                       | `backend/data/agent_checkpoints.sqlite3` | AI 对话检查点 SQLite 文件。                             |
| `LLM_API_KEY`、`LLM_BASE_URL`、`LLM_MODEL`、`LLM_MODEL_PROVIDER`         | 空字符串                                 | LLM 接入配置；具体值取决于所使用的模型服务。            |
| `LLM_TIMEOUT_SECONDS`、`LLM_TEMPERATURE`、`LLM_STREAM_ENABLED`           | `60.0`、`0.2`、`false`                   | LLM 请求超时、温度和流式配置。                          |
| `RAG_EMBEDDING_BACKEND`                                                  | `api`                                    | Embedding 后端选择。                                    |
| `RAG_EMBEDDING_API_KEY`、`RAG_EMBEDDING_BASE_URL`、`RAG_EMBEDDING_MODEL` | 空字符串                                 | API Embedding 配置；使用 API 模式时需按服务商要求填写。 |
| `RAG_LOCAL_EMBEDDING_MODEL`、`RAG_LOCAL_DEVICE`                          | `BAAI/bge-small-zh-v1.5`、`cpu`          | 本地 Embedding 模型和设备。                             |
| `RAG_EMBEDDING_TIMEOUT_SECONDS`                                          | `60.0`                                   | Embedding 请求超时秒数。                                |
| `RAG_CHROMA_DIR`、`RAG_KB_DIR`                                           | `backend/data/chroma`、`backend/data/kb` | Chroma 索引目录和 Markdown 知识库目录。                 |
| `RAG_COLLECTION_PREFIX`                                                  | `lab_kb`                                 | 向量集合名称前缀。                                      |
| `RAG_CHUNK_SIZE`、`RAG_CHUNK_OVERLAP`、`RAG_TOP_K`                       | `600`、`100`、`4`                        | 文本切分和检索参数。                                    |
| `RAG_MIN_RELEVANCE_SCORE`                                                | `0.2`                                    | 检索相关性阈值。                                        |

AI 相关配置默认关闭或为空；启用后请根据实际模型和 Embedding 服务补全对应参数。使用本地 Hugging Face Embedding 时，可额外安装：

```powershell
cd backend
python -m pip install -r requirements-rag-local.txt
```

## API 概览

后端 API 统一使用 `/api` 前缀。除注册、登录及上传接口外，大部分业务接口需要认证；具体权限以接口文档和后端实现为准。

| 功能               | 方法与路径                                                                                                                                                           |
| ------------------ | -------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| 注册、登录         | `POST /api/auth/register`、`POST /api/auth/login`                                                                                                                    |
| 当前用户资料、密码 | `GET /api/user/me`、`PUT /api/user/me`、`PUT /api/user/me/password`                                                                                                  |
| 用户管理（管理员） | `GET /api/user/list`、`POST /api/user`、`PUT /api/user/{user_id}`、`DELETE /api/user/{user_id}`                                                                      |
| 实验室             | `GET /api/lab/list`、`GET /api/lab/{lab_id}`；新增、修改和删除为 `POST /api/lab`、`PUT /api/lab/{lab_id}`、`DELETE /api/lab/{lab_id}`（管理员）                      |
| 设备               | `GET /api/equipment/list`；新增、修改和删除为 `POST /api/equipment`、`PUT /api/equipment/{equipment_id}`、`DELETE /api/equipment/{equipment_id}`（管理员）           |
| 预约               | `POST /api/reservation`、`GET /api/reservation/list`、`PUT /api/reservation/{reservation_id}/cancel`；审核为 `PUT /api/reservation/{reservation_id}/audit`（管理员） |
| 文件上传           | `POST /api/files/upload`                                                                                                                                             |
| AI 对话            | `POST /api/ai/chat`、`POST /api/ai/chat/stream`（AI 启用后可用）                                                                                                     |
| 重建知识库索引     | `POST /api/ai/kb/rebuild`（管理员）                                                                                                                                  |

分页、筛选、请求体和响应格式请以 `/docs` 中的 OpenAPI 文档为准。

## 开发与测试

前端开发服务器支持热更新。生产构建和本地预览命令：

```powershell
cd frontend
npm run build
npm run preview
```

前端格式化命令：

```powershell
npm run format
```

后端目前包含基于 `unittest` 的 AI 流式处理测试；配置好后端依赖和必需环境变量后，在 `backend` 目录运行：

```powershell
python -m unittest discover -s tests
```

## 部署

仓库提供前端生产构建命令 `npm run build` 和后端 Uvicorn 应用入口 `app.main:app`。生产环境的 Web 服务器、进程管理、反向代理、HTTPS、数据库部署及静态资源托管方式未说明。

## 目录结构

```text
.
├── backend/
│   ├── app/
│   │   ├── api/          # HTTP 路由
│   │   ├── common/       # 统一响应与异常处理
│   │   ├── dependencies/ # 认证等依赖
│   │   ├── models/       # SQLAlchemy 数据模型
│   │   ├── schemas/      # 请求与响应模型
│   │   ├── services/     # 业务、AI 与知识库逻辑
│   │   └── utils/        # JWT、密码等工具
│   ├── data/kb/          # Markdown 知识库
│   ├── tests/            # 后端测试和数据脚本
│   ├── requirements.txt
│   └── requirements-rag-local.txt
└── frontend/
    ├── src/
    │   ├── api/          # 后端 API 调用
    │   ├── components/   # Vue 组件
    │   ├── layouts/      # 页面布局
    │   ├── router/       # 前端路由
    │   └── views/        # 页面视图
    ├── package.json
    └── vite.config.js
```

## 常见问题

### 后端启动时报缺少配置

请确认 `backend/.env` 中已填写 `DATABASE_URL` 和 `JWT_SECRET_KEY`，并确认数据库可连接。

### AI 接口提示未启用

`AI_ENABLED` 默认为 `false`。启用 AI 前，还需配置可用的 LLM 与 Embedding 服务参数；本地 Embedding 需安装 `requirements-rag-local.txt` 中的依赖。

### 前端无法连接后端

默认代理目标是 `http://127.0.0.1:8000`。确认后端正在此地址监听；如后端地址变化，请同步调整 `frontend/vite.config.js` 中的代理配置。

## 待补充信息

- 项目的正式名称、背景说明和目标用户。
- 后端支持的 Python 版本及数据库类型、版本、建库/迁移说明。
- 生产环境部署方案及必要的安全配置要求。
- 许可证、贡献指南、维护者或问题反馈渠道。
