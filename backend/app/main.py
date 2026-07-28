"""
爱拼豆 API — 拼豆图纸生成服务
"""

import base64
import logging
import os
import time
import traceback

from fastapi import FastAPI, File, Form, Query, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from .processor import process

# ── 日志 ────────────────────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("aipindou")

app = FastAPI(
    title="爱拼豆 API",
    description="拼豆图纸生成服务 — Bead Art Blueprint Generator",
    version="3.0.0",
)

# ── CORS ───────────────────────────────────────────────────────────────
_cors_env = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://127.0.0.1:3000")
if _cors_env.strip() == "*":
    ALLOWED_ORIGINS = ["*"]
else:
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


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "3.0.0", "brands": sorted(VALID_BRANDS)}


@app.post("/api/generate")
async def generate(
    image: UploadFile = File(...),
    size: int = Form(48),
    colors: int = Form(32),
    brand: str = Form("artkal"),
    format: str = Query("image", description="响应格式：image（PNG 图片）或 json（含统计信息）"),
):
    """
    上传图片，生成拼豆图纸。

    - **brand**：色卡品牌（artkal / perler）
    - **format=image**（默认）：返回 PNG 图纸。
    - **format=json**：返回 JSON，包含 base64 图纸 + 调色板 + 数量统计。
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
            data, grid_size=size, n_colors=colors, brand=brand.lower()
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
