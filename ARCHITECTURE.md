# Geoflow 项目架构说明

## 项目概述

Geoflow 是一个类似 VS Code 的编辑器项目，支持两种 GUI 方式：
1. **桌面应用**: Python + PySide6
2. **Web 应用**: FastAPI 后端 + Vue 3 前端 (推荐使用 Bun 作为前端运行时)

项目主要功能：
- 构建和管理工作区
- 数据文件遵循 GeoJSON 标准格式
- 多平台 OAuth 认证
- Monaco 文本编辑器
- 虚拟积分交易系统

## 项目结构

```
/workspace/
├── backend/                    # FastAPI 后端
│   ├── main.py                # 主应用入口
│   ├── auth/                  # 认证模块
│   │   ├── config.py          # 配置和 OAuth 提供者设置
│   │   ├── database.py        # MongoDB 数据库操作
│   │   ├── models.py          # 数据模型
│   │   ├── oauth.py           # OAuth 客户端实现
│   │   ├── routes.py          # 认证和 API 路由
│   │   ├── schemas.py         # Pydantic 数据验证模式
│   │   └── token.py           # JWT 令牌处理
│
├── frontend/                   # Vue 3 前端
│   ├── src/
│   │   ├── components/        # Vue 组件
│   │   │   ├── LoginButton.vue
│   │   │   ├── LoginModal.vue
│   │   │   └── WelcomeModal.vue
│   │   ├── router/            # 路由配置
│   │   │   └── index.js
│   │   ├── stores/            # Pinia 状态管理
│   │   │   └── auth.js
│   │   ├── views/             # 页面视图
│   │   │   ├── Home.vue
│   │   │   ├── Login.vue
│   │   │   └── Register.vue
│   │   ├── App.vue            # 根组件
│   │   ├── main.js            # 入口文件
│   │   └── style.css          # 样式
│   ├── package.json           # 前端依赖配置
│   ├── vite.config.js         # Vite 配置
│   └── index.html
│
├── tests/                      # 测试文件
│   ├── test_smoke.py          # 冒烟测试
│   ├── test_proj.py
│   ├── bench_pyvista_heavy.py
│   ├── bench_threejs_points.html
│   ├── data/                  # 测试数据
│   │   └── seismic.sgy
│   └── scripts/
│       └── generate_segy.py
│
├── venv/                       # Python 虚拟环境
├── requirements.txt            # Python 依赖
├── .env.example               # 环境变量示例
├── run_web.py                 # 同时运行前后端的脚本
├── run_geoflow_web.py         # 单独运行后端
├── run_geoflow.py             # PySide6 桌面应用入口
└── README.md                  # 项目说明
```

## 技术栈

### 后端技术栈
- **Web 框架**: FastAPI 0.136.0
- **数据库**: MongoDB (Motor 3.7.1 异步驱动)
- **认证**: python-jose (JWT), passlib (密码哈希)
- **HTTP 客户端**: httpx, requests
- **ASGI 服务器**: uvicorn 0.44.0
- **数据验证**: pydantic 2.13.2

### 前端技术栈
- **框架**: Vue 3.4
- **构建工具**: Vite 7.3
- **状态管理**: Pinia 2.1
- **路由**: Vue Router 4.2
- **HTTP 客户端**: Axios 1.6
- **编辑器**: Monaco Editor 0.45
- **UI**: FontAwesome, Tailwind CSS 4.2
- **运行时**: Bun (推荐)

## 核心模块说明

### 1. 认证模块 (`backend/auth/`)

#### 支持的 OAuth 提供商
- GitHub
- Microsoft (Azure AD)
- 飞书/Feishu
- 微信
- 支付宝
- 抖音

#### API 端点
- `GET /api/auth/providers` - 获取可用认证提供商
- `GET /api/auth/login/{provider}` - OAuth 登录重定向
- `GET /api/auth/callback/{provider}` - OAuth 回调处理
- `POST /api/auth/register` - 本地用户注册
- `POST /api/auth/login` - 本地用户登录
- `GET /api/auth/me` - 获取当前用户信息
- `POST /api/auth/forgot-password` - 忘记密码

#### 积分交易 API
- `GET /api/auth/points/balance` - 查询余额
- `POST /api/auth/points/buy` - 购买积分
- `POST /api/auth/points/sell` - 出售积分
- `GET /api/auth/points/history` - 交易历史
- `GET /api/auth/points/market` - 市场价格

### 2. 项目管理 API (`backend/main.py`)

- `GET /api/health` - 健康检查
- `GET /api/project` - 获取项目信息
- `POST /api/project/load` - 加载项目
- `POST /api/project/create` - 创建项目
- `GET /api/files/{file_path}` - 读取文件
- `POST /api/files/{file_path}` - 保存文件
- `GET /api/search` - 搜索文件
- `GET /api/git-status` - Git 状态
- `POST /api/git-commit` - Git 提交
- `GET /api/problems` - 代码问题
- `GET /api/settings` - 获取设置
- `POST /api/settings` - 保存设置
- `GET /api/views` - 获取可用视图

### 3. 前端模块

- **认证状态管理**: `frontend/src/stores/auth.js`
- **路由配置**: `frontend/src/router/index.js`
- **登录组件**: `frontend/src/components/LoginButton.vue`, `LoginModal.vue`
- **页面视图**: Login.vue, Register.vue, Home.vue

## 数据流

1. **用户认证流程**:
   - 用户选择 OAuth 提供商或本地注册/登录
   - 后端验证凭据或处理 OAuth 回调
   - 生成 JWT 令牌并返回
   - 前端存储令牌并在后续请求中使用

2. **文件操作流程**:
   - 用户通过编辑器修改文件
   - 前端调用 `/api/files/{file_path}` 保存
   - 后端验证路径安全并写入文件

3. **积分交易流程**:
   - 用户提交买卖请求
   - 后端验证 JWT 令牌
   - 更新用户积分余额
   - 记录交易历史

## 配置说明

### 环境变量
在 `.env` 文件中配置：
```
JWT_SECRET_KEY=your-secret-key
DATABASE_URL=mongodb://localhost:27017/geoflow
GITHUB_CLIENT_ID=your-github-id
GITHUB_CLIENT_SECRET=your-github-secret
# 其他 OAuth 提供商配置...
```

### 数据库
项目使用 MongoDB，支持本地实例或 MongoDB Atlas。

## 部署架构

开发环境：
- 前端: Vite 开发服务器 (默认端口 5173)
- 后端: Uvicorn ASGI 服务器 (默认端口 8000)

生产环境：
- 前端构建为静态文件 (`frontend/dist/`)
- 后端直接提供静态文件服务
