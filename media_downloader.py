import os
import logging
import requests
from auth import TokenManager
import config

logger = logging.getLogger(__name__)


def download_image(token_mgr: TokenManager, file_token: str, assets_dir: str) -> str | None:
    """下载飞书图片到本地 assets 目录，返回相对路径。"""
    os.makedirs(assets_dir, exist_ok=True)

    url = f"{config.BASE_URL}/drive/v1/medias/{file_token}/download"
    try:
        resp = requests.get(url, headers=token_mgr.auth_headers(), stream=True)
        resp.raise_for_status()
    except requests.RequestException as e:
        logger.error("图片下载失败: %s (%s)", file_token, e)
        return None

    # 从 Content-Disposition 或 Content-Type 推断扩展名
    content_type = resp.headers.get("Content-Type", "")
    ext = _guess_ext(content_type, file_token)
    filename = f"{file_token}{ext}"
    filepath = os.path.join(assets_dir, filename)

    with open(filepath, "wb") as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)

    logger.debug("图片已保存: %s", filepath)
    return filename


def _guess_ext(content_type: str, fallback: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/gif": ".gif",
        "image/webp": ".webp",
        "image/svg+xml": ".svg",
    }
    for mime, ext in mapping.items():
        if mime in content_type:
            return ext
    return ".png"  # 默认
