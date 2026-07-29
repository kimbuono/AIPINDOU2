"""
爱拼豆 API — 拼豆图纸生成服务
"""

import base64
import logging
import os
import time
import traceback

import json
from typing import Optional

from fastapi import FastAPI, File, Form, Query, UploadFile, HTTPException, Request, Depends, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel

from .processor import process, recommend_size
from .auth import create_user, authenticate, create_token, verify_token, User
from .database import get_conn

# ── 日志 ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aipindou")

app = FastAPI(
    title="爱拼豆 API",
    description="拼豆图纸生成服务 — Bead Art Blueprint Generator",
    version="3.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────
# Explicit origins + no credentials = browser-compliant CORS
_cors_env = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:3000,http://127.0.0.1:3000,https://frontend-hazel-gamma-65.vercel.app,https://frontend-jjiajy66-5340s-projects.vercel.app",
)
ALLOWED_ORIGINS = [o.strip() for o in _cors_env.split(",") if o.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 常量 ────────────────────────────────────────────────────────────────
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB
VALID_SIZES = {16, 29, 32, 48, 58, 64}
VALID_COLORS = {16, 24, 32, 48, 64, 80, 96, 128, 256}
VALID_BRANDS = {"artkal", "perler"}

ERROR_MESSAGES = {
    "invalid_size": "不支持的图纸尺寸 {size}，可选：{valid}",
    "invalid_colors": "不支持的颜色数量 {colors}，可选：{valid}",
    "invalid_brand": "不支持的色卡品牌 '{brand}'，可选：{valid}",
    "invalid_type": "不支持的图片格式：{type}。仅支持 JPG、PNG、WebP",
    "file_too_large": "文件过大，最大支持 10 MB",
    "processing_failed": "图片处理失败：{detail}",
}


# ── Auth dependency ──────────────────────────────────────────────────
security = HTTPBearer(auto_error=False)


def get_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[User]:
    if not credentials:
        return None
    return verify_token(credentials.credentials)


def require_user(user: Optional[User] = Depends(get_current_user)) -> User:
    if user is None:
        raise HTTPException(401, "请先登录")
    return user


# ── Pydantic models ──────────────────────────────────────────────────

class SignupRequest(BaseModel):
    email: str
    username: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


class SaveProjectRequest(BaseModel):
    name: str = "未命名项目"
    grid_size: int = 48
    n_colors: int = 48
    brand: str = "artkal"
    dither: bool = True
    original_image: Optional[str] = None
    blueprint_image: Optional[str] = None
    stats_json: Optional[str] = None
    is_favorite: bool = False
    is_public: bool = False


# ── Routes ──────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "4.0.0", "brands": sorted(VALID_BRANDS)}


# ── Auth routes ─────────────────────────────────────────────────────

@app.post("/api/auth/signup")
async def signup(body: SignupRequest):
    """注册新用户"""
    if len(body.password) < 6:
        raise HTTPException(400, "密码至少需要 6 个字符")
    if "@" not in body.email:
        raise HTTPException(400, "请输入有效的邮箱地址")
    try:
        user = create_user(body.email, body.username, body.password)
        token = create_token(user)
        return {"token": token, "user": {"id": user.id, "email": user.email, "username": user.username}}
    except ValueError as e:
        raise HTTPException(409, str(e))


@app.post("/api/auth/login")
async def login(body: LoginRequest):
    """用户登录"""
    user = authenticate(body.email, body.password)
    if not user:
        raise HTTPException(401, "邮箱或密码错误")
    token = create_token(user)
    return {"token": token, "user": {"id": user.id, "email": user.email, "username": user.username}}


@app.get("/api/auth/me")
async def me(user: User = Depends(require_user)):
    """获取当前用户信息"""
    return {"id": user.id, "email": user.email, "username": user.username}


# ── Project routes ──────────────────────────────────────────────────

@app.get("/api/projects")
async def list_projects(
    user: User = Depends(require_user),
    search: str = Query(""),
    sort: str = Query("updated_at"),
    favorite: Optional[int] = Query(None),
):
    """获取用户的所有项目"""
    conn = get_conn()
    try:
        query = "SELECT * FROM projects WHERE user_id = ?"
        params: list = [user.id]

        if search:
            query += " AND name LIKE ?"
            params.append(f"%{search}%")
        if favorite is not None:
            query += " AND is_favorite = ?"
            params.append(favorite)

        order = "updated_at DESC" if sort == "updated_at" else "created_at DESC"
        query += f" ORDER BY {order}"

        rows = conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.get("/api/projects/{project_id}")
async def get_project(project_id: int, user: User = Depends(require_user)):
    """获取单个项目详情"""
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user.id),
        ).fetchone()
        if not row:
            raise HTTPException(404, "项目不存在")
        return dict(row)
    finally:
        conn.close()


@app.post("/api/projects")
async def create_project(body: SaveProjectRequest, user: User = Depends(require_user)):
    """保存新项目"""
    conn = get_conn()
    try:
        cur = conn.execute(
            """INSERT INTO projects
               (user_id, name, grid_size, n_colors, brand, dither,
                original_image, blueprint_image, stats_json, is_favorite, is_public)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (user.id, body.name, body.grid_size, body.n_colors, body.brand,
             1 if body.dither else 0,
             body.original_image, body.blueprint_image, body.stats_json,
             1 if body.is_favorite else 0, 1 if body.is_public else 0),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (cur.lastrowid,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.put("/api/projects/{project_id}")
async def update_project(
    project_id: int,
    body: SaveProjectRequest,
    user: User = Depends(require_user),
):
    """更新已有项目"""
    conn = get_conn()
    try:
        existing = conn.execute(
            "SELECT id FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user.id),
        ).fetchone()
        if not existing:
            raise HTTPException(404, "项目不存在")

        conn.execute(
            """UPDATE projects SET
               name=?, grid_size=?, n_colors=?, brand=?, dither=?,
               original_image=?, blueprint_image=?, stats_json=?,
               is_favorite=?, is_public=?, updated_at=datetime('now')
               WHERE id=?""",
            (body.name, body.grid_size, body.n_colors, body.brand,
             1 if body.dither else 0,
             body.original_image, body.blueprint_image, body.stats_json,
             1 if body.is_favorite else 0, 1 if body.is_public else 0,
             project_id),
        )
        conn.commit()
        row = conn.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
        return dict(row)
    finally:
        conn.close()


@app.delete("/api/projects/{project_id}")
async def delete_project(project_id: int, user: User = Depends(require_user)):
    """删除项目"""
    conn = get_conn()
    try:
        cur = conn.execute(
            "DELETE FROM projects WHERE id = ? AND user_id = ?",
            (project_id, user.id),
        )
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(404, "项目不存在")
        return {"ok": True}
    finally:
        conn.close()


@app.get("/api/recommend")
async def recommend(w: int = 800, h: int = 600):
    """根据图片尺寸推荐最佳网格大小。"""
    size = recommend_size(w, h)
    return {"grid_size": size, "image_width": w, "image_height": h}


@app.post("/api/generate")
async def generate(
    image: UploadFile = File(...),
    size: int = Form(48),
    colors: int = Form(48),
    brand: str = Form("artkal"),
    dither: bool = Form(True),
    format: str = Query("image"),
):
    """
    上传图片，生成拼豆图纸（V5 CIEDE2000 + Floyd-Steinberg dithering）。

    - **brand**: artkal / perler
    - **dither**: Floyd-Steinberg 误差扩散（默认开启，平滑渐变）
    - **format=image**: 返回 PNG；**format=json**: 返回 JSON + 统计
    """
    # ── 参数校验 ─────────────────────────────────────────────────
    if size not in VALID_SIZES:
        raise HTTPException(
            400,
            ERROR_MESSAGES["invalid_size"].format(
                size=size, valid=", ".join(str(s) for s in sorted(VALID_SIZES))
            ),
        )
    if colors not in VALID_COLORS:
        raise HTTPException(
            400,
            ERROR_MESSAGES["invalid_colors"].format(
                colors=colors, valid=", ".join(str(c) for c in sorted(VALID_COLORS))
            ),
        )
    if brand.lower() not in VALID_BRANDS:
        raise HTTPException(
            400,
            ERROR_MESSAGES["invalid_brand"].format(
                brand=brand, valid=", ".join(sorted(VALID_BRANDS))
            ),
        )

    content_type = image.content_type or ""
    if content_type not in {"image/jpeg", "image/png", "image/webp"}:
        raise HTTPException(
            400,
            ERROR_MESSAGES["invalid_type"].format(type=content_type or "未知"),
        )

    # ── 读取文件 ─────────────────────────────────────────────────
    logger.info(f"收到请求: size={size} colors={colors} brand={brand} format={format}")
    t0 = time.time()
    data = await image.read()
    logger.info(f"文件读取: {len(data):,} bytes ({len(data)/1024/1024:.1f} MB) in {time.time()-t0:.1f}s")

    if len(data) > MAX_FILE_SIZE:
        raise HTTPException(400, ERROR_MESSAGES["file_too_large"])

    # ── 处理 ─────────────────────────────────────────────────────
    try:
        t1 = time.time()
        logger.info(f"开始处理: size={size} colors={colors} brand={brand}")
        png_bytes, stats = process(
            data, grid_size=size, n_colors=colors,
            brand=brand.lower(), dither=dither,
        )
        elapsed = time.time() - t1
        logger.info(
            f"处理完成: {stats['total']}颗 {stats['n_colors']}色 "
            f"PNG {len(png_bytes):,}bytes in {elapsed:.1f}s"
        )
    except Exception as exc:
        tb = traceback.format_exc()
        logger.error(f"处理失败:\n{tb}")
        raise HTTPException(
            500,
            detail=f"图片处理失败: {exc}\n---\n{tb[-500:]}",
        )

    # ── 响应 ─────────────────────────────────────────────────────
    total_time = time.time() - t0
    if format == "json":
        b64 = base64.b64encode(png_bytes).decode("utf-8")
        logger.info(f"JSON 响应: base64 {len(b64):,} chars, total {total_time:.1f}s")
        return {
            "image_base64": b64,
            **stats,
        }

    logger.info(f"PNG 响应: {len(png_bytes):,} bytes, total {total_time:.1f}s")
    return Response(content=png_bytes, media_type="image/png")
