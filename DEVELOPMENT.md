# Geoflow 开发指引

## 环境准备

### 必需软件
- **Python 3.8+**
- **MongoDB 5.0+** (或 MongoDB Atlas 账号)
- **Bun 1.0+** (推荐用于前端) 或 **Node.js 18+**

### 可选软件
- **PySide6** (用于桌面应用开发)

## 快速开始

### 1. 克隆并进入项目
```bash
cd /workspace
```

### 2. 配置环境变量
复制环境变量示例文件：
```bash
cp .env.example .env
```

编辑 `.env` 文件，配置必需的变量：
```env
JWT_SECRET_KEY=your-super-secret-key-change-in-production-32-chars-min
DATABASE_URL=mongodb://localhost:27017/geoflow
# 如需 OAuth 登录，配置相应的客户端 ID 和密钥
```

### 3. 安装后端依赖
```bash
# 使用项目已有的虚拟环境
source venv/bin/activate
# 或创建新的虚拟环境
python -m venv venv
source venv/bin/activate

# 安装依赖
pip install -r requirements.txt
```

### 4. 安装前端依赖
```bash
cd frontend
bun install
# 或使用 npm
# npm install
```

### 5. 启动服务

#### 方式一：同时启动前后端 (推荐)
```bash
cd /workspace
python run_web.py
```

#### 方式二：分别启动
**启动后端**：
```bash
cd /workspace
python run_geoflow_web.py
# 或直接使用 uvicorn
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

**启动前端** (新开终端)：
```bash
cd /workspace/frontend
bun run dev
# 或使用 npm
# npm run dev
```

### 6. 访问应用
- 后端 API 文档: http://localhost:8000/docs
- 前端开发服务器: http://localhost:5173

## 开发指南

### 后端开发

#### 添加新 API 端点
在 `backend/main.py` 或 `backend/auth/routes.py` 中添加：

```python
@app.get("/api/your-endpoint")
async def your_endpoint():
    return {"message": "Hello"}
```

#### 数据库操作
参考 `backend/auth/database.py` 中的异步 MongoDB 操作：

```python
from backend.auth.database import get_user_by_id, create_user

# 查询用户
user = await get_user_by_id(user_id)

# 创建用户
new_user = await create_user(user_data)
```

### 前端开发

#### 添加新页面
1. 在 `frontend/src/views/` 中创建新的 Vue 组件
2. 在 `frontend/src/router/index.js` 中添加路由

#### 使用认证状态
```javascript
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// 检查登录状态
if (authStore.isAuthenticated) {
    // 用户已登录
}

// 获取用户信息
const user = authStore.user
```

#### 调用 API
```javascript
import axios from 'axios'

const api = axios.create({
    baseURL: 'http://localhost:8000/api'
})

// 添加认证令牌
api.interceptors.request.use(config => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// 调用 API
const response = await api.get('/auth/me')
```

## 测试

### 运行现有测试
```bash
pytest tests/test_smoke.py
```

### 添加新测试
在 `tests/` 目录下创建新的测试文件，使用 pytest 框架。

## 常见问题

### MongoDB 连接失败
- 确认 MongoDB 服务已启动
- 检查 `.env` 中的 `DATABASE_URL` 是否正确
- 确认 IP 白名单配置 (MongoDB Atlas)

### 前端无法连接后端
- 确认后端已在 8000 端口启动
- 检查 CORS 配置 (已允许所有来源用于开发)
- 检查 API 基础 URL 配置

### 依赖安装问题
```bash
# 重新安装 Python 依赖
pip install --upgrade -r requirements.txt

# 重新安装前端依赖
cd frontend
rm -rf node_modules bun.lock
bun install
```

## 项目脚本说明

- `run_web.py` - 同时启动前后端开发服务器
- `run_geoflow_web.py` - 仅启动后端
- `run_geoflow.py` - 启动 PySide6 桌面应用

## 生产构建

### 构建前端
```bash
cd frontend
bun run build
# 或 npm run build
```

构建产物将生成在 `frontend/dist/` 目录，后端会自动提供静态文件服务。
