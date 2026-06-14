"""OAuth 用户授权流程：本地启动 HTTP 服务器接收回调，获取 user_access_token。"""
import json
import os
import time
import logging
import webbrowser
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

import config

logger = logging.getLogger(__name__)

TOKEN_CACHE = "user_token.json"
REDIRECT_URI = "http://localhost:9876/callback"

_auth_code = None


class _CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global _auth_code
        query = parse_qs(urlparse(self.path).query)
        _auth_code = query.get("code", [None])[0]

        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        if _auth_code:
            self.wfile.write("授权成功！可以关闭此页面。".encode("utf-8"))
        else:
            self.wfile.write("授权失败，未获取到 code。".encode("utf-8"))

    def log_message(self, format, *args):
        pass  # 静默日志


def get_user_token() -> str:
    """获取 user_access_token，优先从缓存读取，过期则刷新或重新授权。"""
    cached = _load_cache()
    if cached:
        # 检查是否过期
        if time.time() < cached.get("expire_time", 0) - 300:
            return cached["access_token"]
        # 尝试用 refresh_token 刷新
        if cached.get("refresh_token"):
            token = _refresh_token(cached["refresh_token"])
            if token:
                return token

    # 需要重新授权
    return _authorize()


def _authorize() -> str:
    """打开浏览器让用户授权，获取 user_access_token。"""
    global _auth_code
    _auth_code = None

    auth_url = (
        f"https://open.feishu.cn/open-apis/authen/v1/authorize"
        f"?app_id={config.APP_ID}"
        f"&redirect_uri={REDIRECT_URI}"
        f"&scope=wiki:wiki:readonly docx:document:readonly drive:drive:readonly drive:drive.metadata:readonly"
    )

    server = HTTPServer(("localhost", 9876), _CallbackHandler)
    server.timeout = 120

    logger.info("正在打开浏览器进行授权...")
    print("\n请在浏览器中完成飞书登录授权...\n")
    webbrowser.open(auth_url)

    # 等待回调
    while _auth_code is None:
        server.handle_request()

    server.server_close()
    logger.info("收到授权码，正在换取 token...")

    # 用 code 换 user_access_token
    url = f"{config.BASE_URL}/authen/v1/oidc/access_token"
    # 需要 app_access_token
    app_token = _get_app_access_token()
    resp = requests.post(url, headers={"Authorization": f"Bearer {app_token}"},
                         json={"grant_type": "authorization_code", "code": _auth_code})
    data = resp.json()

    if data.get("code") != 0:
        raise RuntimeError(f"换取 token 失败: {data.get('msg')}")

    token_data = data["data"]
    _save_cache(token_data)
    logger.info("用户授权成功")
    return token_data["access_token"]


def _refresh_token(refresh_token: str) -> str | None:
    """用 refresh_token 刷新 user_access_token。"""
    url = f"{config.BASE_URL}/authen/v1/oidc/refresh_access_token"
    app_token = _get_app_access_token()
    resp = requests.post(url, headers={"Authorization": f"Bearer {app_token}"},
                         json={"grant_type": "refresh_token",
                               "refresh_token": refresh_token})
    data = resp.json()
    if data.get("code") != 0:
        logger.warning("refresh token 失败: %s", data.get("msg"))
        return None

    token_data = data["data"]
    _save_cache(token_data)
    logger.info("token 已刷新")
    return token_data["access_token"]


def _get_app_access_token() -> str:
    """获取 app_access_token（用于换取 user token）。"""
    url = f"{config.BASE_URL}/auth/v3/app_access_token/internal"
    resp = requests.post(url, json={
        "app_id": config.APP_ID,
        "app_secret": config.APP_SECRET,
    })
    return resp.json()["app_access_token"]


def _save_cache(token_data: dict):
    expire_in = token_data.get("expires_in", 7200)
    token_data["expire_time"] = time.time() + expire_in
    with open(TOKEN_CACHE, "w", encoding="utf-8") as f:
        json.dump(token_data, f, ensure_ascii=False, indent=2)


def _load_cache() -> dict | None:
    if not os.path.exists(TOKEN_CACHE):
        return None
    with open(TOKEN_CACHE, "r", encoding="utf-8") as f:
        return json.load(f)


def user_auth_headers() -> dict:
    return {"Authorization": f"Bearer {get_user_token()}"}


class UserTokenManager:
    """与 TokenManager 接口兼容，但使用 user_access_token。"""

    def get_token(self) -> str:
        return get_user_token()

    def auth_headers(self) -> dict:
        return user_auth_headers()
