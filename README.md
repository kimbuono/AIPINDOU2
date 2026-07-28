# 爱拼豆 — 拼豆图纸生成器

上传图片，一键生成拼豆图纸。支持多种网格尺寸和颜色数量，免费在线使用。

## 功能

- 上传图片（JPG / PNG / WebP）
- 自适应颜色量化
- 6 种网格尺寸：16×16、29×29、32×32、48×48、58×58、64×64
- 4 种颜色数量：16 色、24 色、32 色、48 色
- 生成包含网格、颜色图例和数量统计的 PNG 图纸
- 响应式设计，支持桌面端和移动端

## 技术栈

| 层级 | 技术 |
|------|------|
| 前端 | Next.js 16 + TypeScript + Tailwind CSS v4 |
| 后端 | FastAPI + Pillow（纯 Python K-means 色彩量化） |
| 部署 | Docker Compose（Python 3.12 / Node 20 Alpine） |

## 快速开始

### 方式一：Docker Compose（推荐）

```bash
docker compose up -d
```

- 前端：http://localhost:3000
- 后端 API：http://localhost:8000
- 健康检查：http://localhost:8000/api/health

### 方式二：本地运行

**后端**

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

**前端**

```bash
cd frontend
cp .env.local.example .env.local   # 或直接编辑 .env.local
npm install
npm run dev
```

前端默认运行在 http://localhost:3000，会代理 API 请求到 http://localhost:8000。

### 生产构建

```bash
cd frontend
npm run build
npm start
```

## 项目结构

```
ai-pin-dou/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py          # FastAPI 应用入口
│   │   └── processor.py     # 图像处理核心逻辑
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   └── app/
│   │       ├── globals.css
│   │       ├── layout.tsx
│   │       └── page.tsx     # 主页面（上传、预览、生成、下载）
│   ├── Dockerfile
│   ├── next.config.ts
│   ├── package.json
│   └── .env.local
├── docker-compose.yml
└── README.md
```

## API

### `POST /api/generate`

生成拼豆图纸。

**请求**

`multipart/form-data`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image` | file | (必填) | 图片文件（JPG/PNG/WebP，≤10MB） |
| `size` | int | 32 | 网格尺寸：16、29、32、48、58、64 |
| `colors` | int | 24 | 颜色数量：16、24、32、48 |

**响应**

- `200` — PNG 图纸图片
- `400` — 参数错误
- `500` — 处理失败

### `GET /api/health`

健康检查 → `{"status": "ok"}`

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000` |
| `CORS_ORIGINS` | 允许的跨域来源（逗号分隔） | `http://localhost:3000` |

## License

MIT
