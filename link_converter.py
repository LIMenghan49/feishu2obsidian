"""第二遍扫描：将飞书内部链接替换为 Obsidian [[wikilink]]。"""
import os
import re
import logging

logger = logging.getLogger(__name__)

# 匹配飞书知识库/文档链接
# https://xxx.feishu.cn/wiki/TOKEN 或 /docx/TOKEN
FEISHU_LINK_RE = re.compile(
    r'\[([^\]]*)\]\(https?://[^)]*(?:feishu\.cn|larksuite\.com)/(?:wiki|docx|docs)/([a-zA-Z0-9]+)[^)]*\)'
)

# 匹配第一遍扫描中留下的 mention 占位符
# [[feishu:TOKEN|标题]]
MENTION_RE = re.compile(r'\[\[feishu:([a-zA-Z0-9]+)\|([^\]]*)\]\]')


def convert_links_in_file(filepath: str, token_to_path: dict[str, str]):
    """读取 MD 文件，替换内部链接为 wikilink，原地写回。"""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    original = content
    content = _replace_feishu_links(content, token_to_path)
    content = _replace_mention_links(content, token_to_path)

    if content != original:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)
        logger.debug("链接已替换: %s", filepath)


def _replace_feishu_links(content: str, token_to_path: dict[str, str]) -> str:
    """替换 [文字](https://xxx.feishu.cn/wiki/TOKEN) → [[文档名]]。"""
    def replacer(match):
        display_text = match.group(1)
        token = match.group(2)
        path = token_to_path.get(token)
        if path:
            doc_name = os.path.basename(path)
            if display_text and display_text != doc_name:
                return f"[[{doc_name}|{display_text}]]"
            return f"[[{doc_name}]]"
        # token 不在映射表中，保留原始链接
        return match.group(0)

    return FEISHU_LINK_RE.sub(replacer, content)


def _replace_mention_links(content: str, token_to_path: dict[str, str]) -> str:
    """替换 [[feishu:TOKEN|标题]] → [[文档名]]。"""
    def replacer(match):
        token = match.group(1)
        title = match.group(2)
        path = token_to_path.get(token)
        if path:
            doc_name = os.path.basename(path)
            return f"[[{doc_name}]]"
        # 找不到映射，保留标题作为链接
        return f"[[{title}]]"

    return MENTION_RE.sub(replacer, content)


def convert_all_links(output_dir: str, token_to_path: dict[str, str]):
    """遍历输出目录下所有 .md 文件，执行链接替换。"""
    count = 0
    for root, _, files in os.walk(output_dir):
        for fname in files:
            if fname.endswith(".md"):
                filepath = os.path.join(root, fname)
                convert_links_in_file(filepath, token_to_path)
                count += 1
    logger.info("链接替换完成，共处理 %d 个文件", count)
