# 爱拼豆 — 拼豆图纸生成器

上传图片，一键生成拼豆图纸。支持多种网格尺寸和颜色数量，免费在线使用。

## 功能

- 上传图片（JPG / PNG / WebP）
- 6 种网格尺寸：16×16、29×29、32×32、48×48、58×58、64×64
- 4 种颜色数量：16 色、24 色、32 色、48 色
- K-means 自适应色彩量化
- 生成包含网格、颜色图例和数量统计的 PNG 图纸
- 响应式设计，桌面端和移动端均可使用
- 全面中文化界面

## 技术栈

| 层级 | 技术 | 部署平台 |
|------|------|----------|
| 前端 | Next.js 16 + TypeScript + Tailwind CSS v4 | Vercel |
| 后端 | FastAPI + Pillow（纯 Python K-means） | Render |
| 容器化 | Docker Compose | 本地 / VPS |

## 本地运行

### 后端

```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev
```

- 前端：http://localhost:3000
- 后端：http://localhost:8000
- 健康检查：http://localhost:8000/api/health

### Docker Compose

```bash
docker compose up -d
```

## 项目结构

```
ai-pin-dou/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI 入口
│   │   └── processor.py         # K-means 量化 + 图纸渲染
│   ├── Dockerfile
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── app/                  # Next.js App Router
│   │   └── components/           # 10 个 UI 组件
│   ├── Dockerfile
│   └── next.config.ts
├── render.yaml                   # Render 部署配置
├── docker-compose.yml
└── README.md
```

## API

### `POST /api/generate`

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `image` | file | 必填 | JPG / PNG / WebP，≤10MB |
| `size` | int | 32 | 16 / 29 / 32 / 48 / 58 / 64 |
| `colors` | int | 24 | 16 / 24 / 32 / 48 |
| `format` | query | `image` | `image` 返回 PNG；`json` 返回 base64+统计 |

### `GET /api/health` → `{"status":"ok","version":"2.0.0"}`

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `NEXT_PUBLIC_API_URL` | 后端 API 地址 | `http://localhost:8000` |
| `CORS_ORIGINS` | 允许的跨域来源 | `http://localhost:3000`（设为 `*` 允许全部） |

## License

MIT
