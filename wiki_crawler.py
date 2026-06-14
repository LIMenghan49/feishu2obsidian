"""递归遍历飞书知识库节点树。"""
import os
import re
import logging
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from auth import TokenManager

logger = logging.getLogger(__name__)

# Windows 文件名非法字符
INVALID_CHARS = re.compile(r'[\\/:*?"<>|]')


@retry(stop=stop_after_attempt(config.MAX_RETRIES),
       wait=wait_exponential(multiplier=1, min=1, max=10))
def _api_get(url: str, token_mgr: TokenManager, params: dict = None) -> dict:
    resp = requests.get(url, headers=token_mgr.auth_headers(), params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"API 错误: {data.get('code')} - {data.get('msg')}")
    return data.get("data", {})


def get_wiki_spaces(token_mgr: TokenManager) -> list[dict]:
    """获取所有知识空间列表。"""
    spaces = []
    page_token = None
    while True:
        params = {"page_size": 50}
        if page_token:
            params["page_token"] = page_token

        url = f"{config.BASE_URL}/wiki/v2/spaces"
        data = _api_get(url, token_mgr, params)

        spaces.extend(data.get("items", []))
        page_token = data.get("page_token")
        if not data.get("has_more"):
            break
        time.sleep(config.REQUEST_INTERVAL)

    # 如果配置了指定空间，过滤
    if config.SPACE_IDS:
        spaces = [s for s in spaces if s["space_id"] in config.SPACE_IDS]

    logger.info("获取到 %d 个知识空间", len(spaces))
    return spaces


def get_all_nodes(token_mgr: TokenManager, space_id: str) -> list[dict]:
    """递归获取知识空间下所有节点，扁平化返回，并附带目录路径。"""
    nodes = []
    _crawl_nodes(token_mgr, space_id, parent_token=None, parent_path="", nodes=nodes)
    logger.info("空间 %s 共 %d 个节点", space_id, len(nodes))
    return nodes


def _crawl_nodes(token_mgr: TokenManager, space_id: str,
                 parent_token: str | None, parent_path: str,
                 nodes: list[dict]):
    """递归获取子节点。"""
    page_token = None
    while True:
        params = {"page_size": 50}
        if page_token:
            params["page_token"] = page_token
        if parent_token:
            params["parent_node_token"] = parent_token

        url = f"{config.BASE_URL}/wiki/v2/spaces/{space_id}/nodes"
        data = _api_get(url, token_mgr, params)

        for node in data.get("items", []):
            title = sanitize_filename(node.get("title", "无标题"))
            node_path = os.path.join(parent_path, title) if parent_path else title

            node["_path"] = node_path
            node["_title"] = title
            nodes.append(node)

            # 如果有子节点，递归
            if node.get("has_child"):
                _crawl_nodes(token_mgr, space_id,
                             parent_token=node["node_token"],
                             parent_path=node_path, nodes=nodes)

        page_token = data.get("page_token")
        if not data.get("has_more"):
            break
        time.sleep(config.REQUEST_INTERVAL)


def sanitize_filename(name: str) -> str:
    """过滤 Windows 非法文件名字符。"""
    name = INVALID_CHARS.sub("_", name)
    name = name.strip(". ")  # 不能以点或空格结尾
    return name or "无标题"


def resolve_name_conflicts(nodes: list[dict]) -> dict[str, str]:
    """处理同名文件冲突，返回 obj_token → 最终路径 的映射。"""
    seen = {}  # path → count
    token_to_path = {}

    for node in nodes:
        base_path = node["_path"]
        path = base_path
        count = seen.get(base_path, 0)
        if count > 0:
            path = f"{base_path}_{count + 1}"
        seen[base_path] = count + 1

        node["_path"] = path
        obj_token = node.get("obj_token", node.get("node_token", ""))
        token_to_path[obj_token] = path

    return token_to_path
