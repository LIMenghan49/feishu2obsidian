import time
import logging
import requests
import config

logger = logging.getLogger(__name__)


class TokenManager:
    """管理 tenant_access_token，自动刷新（有效期 2 小时）。"""

    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id or config.APP_ID
        self.app_secret = app_secret or config.APP_SECRET
        self._token = None
        self._expire_time = 0

    def get_token(self) -> str:
        # 提前 5 分钟刷新，避免请求途中过期
        if time.time() > self._expire_time - 300:
            self._refresh()
        return self._token

    def _refresh(self):
        url = f"{config.BASE_URL}/auth/v3/tenant_access_token/internal"
        resp = requests.post(url, json={
            "app_id": self.app_id,
            "app_secret": self.app_secret,
        })
        resp.raise_for_status()
        data = resp.json()

        if data.get("code") != 0:
            raise RuntimeError(f"获取 token 失败: {data.get('msg')}")

        self._token = data["tenant_access_token"]
        self._expire_time = time.time() + data.get("expire", 7200)
        logger.info("token 已刷新，有效期至 %s",
                     time.strftime("%H:%M:%S", time.localtime(self._expire_time)))

    def auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.get_token()}"}
