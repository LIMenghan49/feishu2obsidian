"""飞书 Docx Block 递归解析为 Markdown。

飞书文档 Block 是树形结构，需要递归处理 children。
API 参考: https://open.feishu.cn/document/server-docs/docs/docs/docx-v1/document-block/list
"""
import logging
import time
import requests
from tenacity import retry, stop_after_attempt, wait_exponential

import config
from auth import TokenManager
from media_downloader import download_image

logger = logging.getLogger(__name__)

# Block type 常量 (飞书 Docx API)
BLOCK_PAGE = 1
BLOCK_TEXT = 2
BLOCK_HEADING1 = 3
BLOCK_HEADING2 = 4
BLOCK_HEADING3 = 5
BLOCK_HEADING4 = 6
BLOCK_HEADING5 = 7
BLOCK_HEADING6 = 8
BLOCK_HEADING7 = 9
BLOCK_HEADING8 = 10
BLOCK_HEADING9 = 11
BLOCK_BULLET = 12
BLOCK_ORDERED = 13
BLOCK_CODE = 14
BLOCK_QUOTE = 15
BLOCK_TODO = 17
BLOCK_DIVIDER = 22
BLOCK_IMAGE = 27
BLOCK_TABLE = 31
BLOCK_TABLE_CELL = 32
BLOCK_QUOTE_CONTAINER = 34
BLOCK_CALLOUT = 44


@retry(stop=stop_after_attempt(config.MAX_RETRIES),
       wait=wait_exponential(multiplier=1, min=1, max=10))
def _api_get(url: str, token_mgr: TokenManager, params: dict = None) -> dict:
    resp = requests.get(url, headers=token_mgr.auth_headers(), params=params)
    resp.raise_for_status()
    data = resp.json()
    if data.get("code") != 0:
        raise RuntimeError(f"API 错误: {data.get('code')} - {data.get('msg')}")
    return data.get("data", {})


def get_doc_blocks(token_mgr: TokenManager, document_id: str) -> list[dict]:
    """获取文档所有 Block（处理分页）。"""
    blocks = []
    page_token = None
    while True:
        params = {"page_size": 500}
        if page_token:
            params["page_token"] = page_token

        url = f"{config.BASE_URL}/docx/v1/documents/{document_id}/blocks"
        data = _api_get(url, token_mgr, params)

        blocks.extend(data.get("items", []))
        page_token = data.get("page_token")
        if not data.get("has_more"):
            break
        time.sleep(config.REQUEST_INTERVAL)

    logger.debug("获取 %d 个 blocks (doc: %s)", len(blocks), document_id)
    return blocks


def blocks_to_markdown(blocks: list[dict], token_mgr: TokenManager,
                       assets_dir: str) -> str:
    """将 Block 列表转为 Markdown 文本。"""
    # 建立 block_id → block 的索引，方便递归查找子 Block
    block_map = {b["block_id"]: b for b in blocks}

    # 根节点是 Page Block，从它的 children 开始解析
    root = blocks[0] if blocks else None
    if not root or root.get("block_type") != BLOCK_PAGE:
        logger.warning("文档无有效根节点")
        return ""

    lines = []
    # 标题自动编号计数器: h1, h2, h3, h4, h5, h6
    heading_counters = [0, 0, 0, 0, 0, 0]
    children_ids = root.get("children", [])
    _parse_children(children_ids, block_map, token_mgr, assets_dir, lines, indent=0,
                    heading_counters=heading_counters)
    # 清理空行：去除连续空行，保留最多1个
    result = "\n".join(lines)
    import re
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result.strip()


def _parse_children(children_ids: list[str], block_map: dict,
                    token_mgr: TokenManager, assets_dir: str,
                    lines: list[str], indent: int,
                    heading_counters: list[int] = None):
    """递归解析子 Block 列表。"""
    if heading_counters is None:
        heading_counters = [0, 0, 0, 0, 0, 0]
    ordered_counter = 0  # 有序列表计数器
    for block_id in children_ids:
        block = block_map.get(block_id)
        if not block:
            continue
        # 有序列表连续计数，其他类型重置
        if block.get("block_type") == BLOCK_ORDERED:
            ordered_counter += 1
        else:
            ordered_counter = 0
        _parse_block(block, block_map, token_mgr, assets_dir, lines, indent,
                     heading_counters=heading_counters,
                     ordered_counter=ordered_counter)


def _parse_block(block: dict, block_map: dict, token_mgr: TokenManager,
                 assets_dir: str, lines: list[str], indent: int,
                 heading_counters: list[int] = None,
                 ordered_counter: int = 0):
    """解析单个 Block，根据类型转为对应 Markdown。"""
    if heading_counters is None:
        heading_counters = [0, 0, 0, 0, 0, 0]
    btype = block.get("block_type")
    children = block.get("children", [])

    # --- 标题 ---
    if BLOCK_HEADING1 <= btype <= BLOCK_HEADING9:
        level = min(btype - BLOCK_HEADING1 + 1, 6)  # MD 最多 6 级
        heading_key = f"heading{btype - BLOCK_HEADING1 + 1}"
        text = _extract_text(block.get(heading_key, {}))
        if text.strip():
            # 自动编号：递增当前级别，重置下级计数
            idx = level - 1
            heading_counters[idx] += 1
            for i in range(idx + 1, 6):
                heading_counters[i] = 0
            # 检测标题是否已有序号（中文数字/阿拉伯数字开头）
            if _has_existing_number(text.strip()):
                lines.append(f"{'#' * level} {text}")
            else:
                # 飞书风格：每级独立编号 1. 2. 3.（不是层级 1.2.1）
                number = heading_counters[idx]
                lines.append(f"{'#' * level} {number}. {text}")

    # --- 正文 ---
    elif btype == BLOCK_TEXT:
        text = _extract_text(block.get("text", {}))
        prefix = "  " * indent
        lines.append(f"{prefix}{text}")
        # 正文 Block 可能有子 Block（嵌套内容）
        if children:
            _parse_children(children, block_map, token_mgr, assets_dir, lines, indent)

    # --- 无序列表 ---
    elif btype == BLOCK_BULLET:
        text = _extract_text(block.get("bullet", {}))
        prefix = "  " * indent
        lines.append(f"{prefix}- {text}")
        if children:
            _parse_children(children, block_map, token_mgr, assets_dir, lines, indent + 1)

    # --- 有序列表 ---
    elif btype == BLOCK_ORDERED:
        text = _extract_text(block.get("ordered", {}))
        prefix = "  " * indent
        num = ordered_counter if ordered_counter > 0 else 1
        lines.append(f"{prefix}{num}. {text}")
        if children:
            _parse_children(children, block_map, token_mgr, assets_dir, lines, indent + 1)

    # --- 待办 ---
    elif btype == BLOCK_TODO:
        todo_data = block.get("todo", {})
        text = _extract_text(todo_data)
        checked = "x" if todo_data.get("style", {}).get("done") else " "
        prefix = "  " * indent
        lines.append(f"{prefix}- [{checked}] {text}")
        if children:
            _parse_children(children, block_map, token_mgr, assets_dir, lines, indent + 1)

    # --- 代码块 ---
    elif btype == BLOCK_CODE:
        code_data = block.get("code", {})
        text = _extract_text(code_data)
        lang = _get_code_language(code_data)
        lines.append(f"```{lang}")
        lines.append(text)
        lines.append("```")

    # --- 引用 ---
    elif btype == BLOCK_QUOTE:
        text = _extract_text(block.get("quote", {}))
        lines.append(f"> {text}")
        if children:
            for cid in children:
                child = block_map.get(cid)
                if child:
                    child_lines = []
                    _parse_block(child, block_map, token_mgr, assets_dir, child_lines, 0)
                    for cl in child_lines:
                        lines.append(f"> {cl}")

    # --- 引用容器 ---
    elif btype == BLOCK_QUOTE_CONTAINER:
        if children:
            for cid in children:
                child = block_map.get(cid)
                if child:
                    child_lines = []
                    _parse_block(child, block_map, token_mgr, assets_dir, child_lines, 0)
                    for cl in child_lines:
                        lines.append(f"> {cl}")

    # --- 分割线 ---
    elif btype == BLOCK_DIVIDER:
        lines.append("---")

    # --- 图片 ---
    elif btype == BLOCK_IMAGE:
        image_data = block.get("image", {})
        file_token = image_data.get("token", "")
        if file_token:
            filename = download_image(token_mgr, file_token, assets_dir)
            if filename:
                lines.append(f"![](./assets/{filename})")
            else:
                lines.append(f"<!-- 图片下载失败: {file_token} -->")

    # --- 表格 ---
    elif btype == BLOCK_TABLE:
        # 表格前必须有空行，否则 Obsidian 不识别
        if lines and lines[-1].strip() != "":
            lines.append("")
        _parse_table(block, block_map, token_mgr, assets_dir, lines)

    # --- 嵌入表格 (sheet block, type=30) ---
    elif btype == 30:
        if lines and lines[-1].strip() != "":
            lines.append("")
        _parse_sheet_block(block, token_mgr, lines)

    # --- Callout ---
    elif btype == BLOCK_CALLOUT:
        if children:
            lines.append("> [!NOTE]")
            for cid in children:
                child = block_map.get(cid)
                if child:
                    child_lines = []
                    _parse_block(child, block_map, token_mgr, assets_dir, child_lines, 0)
                    for cl in child_lines:
                        lines.append(f"> {cl}")

    # --- 未知类型 ---
    else:
        logger.debug("未处理的 block 类型: %d (id: %s)", btype, block.get("block_id"))
        # 仍然尝试递归子节点
        if children:
            _parse_children(children, block_map, token_mgr, assets_dir, lines, indent)


def _parse_sheet_block(block: dict, token_mgr: TokenManager, lines: list[str]):
    """解析嵌入表格 (sheet block, type=30)，通过 Sheets API 读取数据。"""
    sheet_data = block.get("sheet", {})
    token = sheet_data.get("token", "")
    if not token:
        return

    parts = token.rsplit("_", 1)
    spreadsheet_token = parts[0]
    sheet_id = parts[1] if len(parts) > 1 else ""

    try:
        url = f"{config.BASE_URL}/sheets/v2/spreadsheets/{spreadsheet_token}/values/{sheet_id}"
        resp = requests.get(url, headers=token_mgr.auth_headers())
        resp.raise_for_status()
        data = resp.json()
        if data.get("code") != 0:
            logger.warning("Sheet 读取失败: %s", data.get("msg"))
            lines.append(f"<!-- 嵌入表格读取失败: {token} -->")
            return

        rows = data["data"]["valueRange"].get("values", [])
        if not rows:
            return

        # 处理单元格值：可能是 str/int/float/list/None
        def cell_str(val):
            if val is None:
                return ""
            if isinstance(val, list):
                # 飞书 Sheet 富文本格式 [{segmentStyle, text}, ...]
                parts = []
                for v in val:
                    if isinstance(v, dict):
                        parts.append(str(v.get("text", "")))
                    else:
                        parts.append(str(v))
                return "".join(parts).replace("|", "\\|").replace("\n", " ")
            return str(val).replace("|", "\\|").replace("\n", " ")

        max_cols = max(len(r) for r in rows)
        # 表头
        header = rows[0]
        while len(header) < max_cols:
            header.append("")
        lines.append("| " + " | ".join(cell_str(c) for c in header) + " |")
        lines.append("| " + " | ".join(["---"] * max_cols) + " |")
        # 表体
        for row in rows[1:]:
            while len(row) < max_cols:
                row.append("")
            lines.append("| " + " | ".join(cell_str(c) for c in row) + " |")

    except Exception as e:
        logger.warning("Sheet 解析异常: %s - %s", token, e)
        lines.append(f"<!-- 嵌入表格解析失败: {token} -->")


def _has_existing_number(text: str) -> bool:
    """检测标题文字是否已有序号（如"一、" "1." "1、" "第一章" "(1)" "①"等）。"""
    import re
    patterns = [
        r'^[一二三四五六七八九十]+[、.,．）\)]',   # 一、 二、
        r'^第[一二三四五六七八九十\d]+[章节篇部]',   # 第一章 第2节
        r'^\d+[\.\、,）\)]',                       # 1. 1、 1)
        r'^\(\d+\)',                                # (1)
        r'^[①②③④⑤⑥⑦⑧⑨⑩]',                     # ①②③
        r'^[IVXLC]+[\.\、]',                        # I. II.
    ]
    for p in patterns:
        if re.match(p, text):
            return True
    return False


def _parse_table(table_block: dict, block_map: dict, token_mgr: TokenManager,
                 assets_dir: str, lines: list[str]):
    """解析表格 Block 为 Markdown 表格。

    飞书表格结构：table block 直接包含所有 cell block（扁平数组），
    按 column_size 分组为行，没有 row block。
    """
    table_data = table_block.get("table", {})
    prop = table_data.get("property", {})
    col_size = prop.get("column_size", 0)
    cell_ids = table_data.get("cells", [])

    if not col_size or not cell_ids:
        return

    def _cell_text(cell_id):
        """提取单个 cell 的文本内容。"""
        cell_block = block_map.get(cell_id)
        if not cell_block:
            return ""
        cell_lines = []
        for sub_id in cell_block.get("children", []):
            sub_block = block_map.get(sub_id)
            if sub_block:
                sub_lines = []
                _parse_block(sub_block, block_map, token_mgr, assets_dir, sub_lines, 0)
                cell_lines.extend(sub_lines)
        # 单元格内容合并为一行，管道符需要转义
        text = " ".join(line.strip() for line in cell_lines if line.strip())
        return text.replace("|", "\\|")

    # 按列数分组为行
    rows = []
    for i in range(0, len(cell_ids), col_size):
        row = [_cell_text(cid) for cid in cell_ids[i:i + col_size]]
        rows.append(row)

    if not rows:
        return

    # 表头
    lines.append("| " + " | ".join(rows[0]) + " |")
    lines.append("| " + " | ".join(["---"] * col_size) + " |")
    # 表体
    for row in rows[1:]:
        lines.append("| " + " | ".join(row) + " |")
    lines.append("")


def _extract_text(block_content: dict) -> str:
    """从 Block 的 elements 中提取文本，处理富文本样式。"""
    elements = block_content.get("elements", [])
    parts = []
    for elem in elements:
        if "text_run" in elem:
            text_run = elem["text_run"]
            content = text_run.get("content", "")
            style = text_run.get("text_element_style", {})
            content = _apply_text_style(content, style)
            parts.append(content)
        elif "mention_doc" in elem:
            mention = elem["mention_doc"]
            title = mention.get("title", "文档")
            token = mention.get("token", "")
            # 第一遍先用占位符，第二遍替换为 wikilink
            parts.append(f"[[feishu:{token}|{title}]]")
        elif "equation" in elem:
            content = elem["equation"].get("content", "").replace("\n", " ").strip()
            parts.append(f"${content}$")
    return "".join(parts)


def _apply_text_style(text: str, style: dict) -> str:
    """应用富文本样式：加粗、斜体、删除线、行内代码、链接、高亮。"""
    if not text or not style:
        return text

    # 行内代码优先（不再叠加其他样式）
    if style.get("inline_code"):
        return f"`{text}`"

    # 链接
    link = style.get("link", {})
    url = link.get("url", "")

    if style.get("bold"):
        text = f"**{text}**"
    if style.get("italic"):
        text = f"*{text}*"
    if style.get("strikethrough"):
        text = f"~~{text}~~"
    if style.get("underline"):
        text = f"<u>{text}</u>"

    if url:
        # 解码飞书的 URL 编码
        from urllib.parse import unquote
        url = unquote(url)
        text = f"[{text}]({url})"

    return text


def _get_code_language(code_data: dict) -> str:
    """获取代码块语言。"""
    lang_map = {
        1: "plaintext", 2: "abap", 3: "ada", 4: "apache", 5: "apex",
        22: "bash", 40: "c", 41: "c++", 43: "csharp", 44: "css",
        47: "dart", 49: "dockerfile", 57: "go", 58: "graphql",
        61: "html", 68: "java", 69: "javascript", 71: "json",
        75: "kotlin", 78: "lua", 80: "markdown", 85: "matlab",
        95: "php", 97: "plaintext", 99: "python", 103: "ruby",
        105: "rust", 109: "shell", 110: "sql", 113: "swift",
        117: "typescript", 121: "xml", 124: "yaml",
    }
    style = code_data.get("style", {})
    lang_code = style.get("language", 1)
    return lang_map.get(lang_code, "plaintext")
