"""飞书知识库 → Obsidian 迁移主流程。

用法: python main.py [--space SPACE_ID] [--output OUTPUT_DIR] [--dry-run]
"""
import os
import sys
import time
import logging
import argparse
from datetime import datetime

import config
from auth import TokenManager
from oauth import UserTokenManager
from progress import Progress
from wiki_crawler import get_wiki_spaces, get_all_nodes, resolve_name_conflicts
from doc_parser import get_doc_blocks, blocks_to_markdown
from media_downloader import download_image
from link_converter import convert_all_links
from validator import validate


def setup_logging():
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format="%(asctime)s %(levelname)-5s [%(name)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(config.LOG_FILE, encoding="utf-8"),
        ],
    )


def make_frontmatter(node: dict) -> str:
    """生成 YAML frontmatter 用于溯源。"""
    obj_token = node.get("obj_token", "")
    title = node.get("title", "")
    now = datetime.now().isoformat(timespec="seconds")
    return (
        f"---\n"
        f'source: "https://feishu.cn/wiki/{obj_token}"\n'
        f'feishu_token: "{obj_token}"\n'
        f'migrated_at: "{now}"\n'
        f'original_title: "{title}"\n'
        f"---\n\n"
    )


def save_markdown(content: str, node: dict, output_dir: str) -> str:
    """保存 Markdown 到文件，返回文件路径。"""
    node_path = node["_path"]
    # 判断是否有子节点 — 有的话作为文件夹，文档保存为 index.md 或同名 .md
    file_path = os.path.join(output_dir, f"{node_path}.md")
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    frontmatter = make_frontmatter(node)
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(frontmatter)
        f.write(content)

    return file_path


def process_node(node: dict, token_mgr: TokenManager, output_dir: str) -> str | None:
    """处理单个节点，返回保存的文件路径。"""
    obj_type = node.get("obj_type", "")
    obj_token = node.get("obj_token", "")
    title = node.get("title", "无标题")

    if obj_type in config.SKIP_TYPES:
        logging.getLogger(__name__).info("跳过不支持的类型: %s (%s)", title, obj_type)
        return None

    node_path = node["_path"]
    assets_dir = os.path.join(output_dir, os.path.dirname(node_path), "assets")

    if obj_type in ("docx", "doc"):
        try:
            blocks = get_doc_blocks(token_mgr, obj_token)
            markdown = blocks_to_markdown(blocks, token_mgr, assets_dir)
        except Exception as e:
            if obj_type == "doc":
                logging.getLogger(__name__).warning(
                    "旧版 Doc 解析失败，跳过: %s (%s)", title, e)
                return None
            raise
    elif obj_type == "sheet":
        # Sheet 类型暂时生成占位 MD，提示手动处理
        markdown = (
            f"# {title}\n\n"
            f"> 此文档为飞书电子表格，暂不支持自动迁移。\n"
            f"> 原始链接: https://feishu.cn/sheets/{obj_token}\n"
        )
    elif obj_type == "file":
        # 纯文件，下载到 assets
        os.makedirs(assets_dir, exist_ok=True)
        filename = download_image(token_mgr, obj_token, assets_dir)
        markdown = f"# {title}\n\n附件: ![{title}](./assets/{filename})\n" if filename else ""
    else:
        # 未知类型，生成占位
        markdown = f"# {title}\n\n> 未支持的文档类型: `{obj_type}`\n"

    if not markdown:
        return None

    return save_markdown(markdown, node, output_dir)


def main():
    parser = argparse.ArgumentParser(description="飞书知识库迁移到 Obsidian")
    parser.add_argument("--output", default=config.OUTPUT_DIR, help="输出目录")
    parser.add_argument("--space", nargs="*", help="指定知识空间 ID (默认全部)")
    parser.add_argument("--dry-run", action="store_true", help="仅列出节点，不下载")
    args = parser.parse_args()

    setup_logging()
    logger = logging.getLogger("main")
    logger.info("===== 飞书知识库迁移开始 =====")

    if not config.APP_ID or not config.APP_SECRET:
        logger.error("请在 .env 中配置 FEISHU_APP_ID 和 FEISHU_APP_SECRET")
        sys.exit(1)

    output_dir = args.output
    os.makedirs(output_dir, exist_ok=True)

    # 使用 OAuth 用户身份（可访问个人知识库）
    token_mgr = UserTokenManager()
    progress = Progress()

    # 覆盖空间过滤
    if args.space:
        config.SPACE_IDS = args.space

    # ===== 第一遍：遍历 + 转换 + 建映射 =====
    logger.info("第一遍：遍历知识库并转换文档...")
    all_nodes = []
    spaces = get_wiki_spaces(token_mgr)

    for space in spaces:
        space_name = space.get("name", space["space_id"])
        logger.info("处理空间: %s", space_name)

        nodes = get_all_nodes(token_mgr, space["space_id"])
        # 给所有节点路径加上空间名前缀
        for node in nodes:
            node["_path"] = os.path.join(space_name, node["_path"])
        all_nodes.extend(nodes)

    # 处理同名冲突
    token_to_path = resolve_name_conflicts(all_nodes)
    logger.info("共 %d 个节点待处理", len(all_nodes))

    if args.dry_run:
        for node in all_nodes:
            print(f"  [{node.get('obj_type', '?')}] {node['_path']}")
        logger.info("dry-run 模式，不执行迁移")
        return

    # 逐个处理
    for i, node in enumerate(all_nodes, 1):
        obj_token = node.get("obj_token", "")
        title = node.get("title", "")

        if progress.is_done(obj_token):
            continue

        logger.info("[%d/%d] %s", i, len(all_nodes), title)

        try:
            file_path = process_node(node, token_mgr, output_dir)
            if file_path:
                progress.mark_done(obj_token, title, file_path)
        except Exception as e:
            logger.error("处理失败: %s - %s", title, e)
            progress.mark_failed(obj_token, title, str(e))

        time.sleep(config.REQUEST_INTERVAL)

    logger.info("第一遍完成。%s", progress.summary())

    # ===== 第二遍：替换内部链接 =====
    logger.info("第二遍：替换内部链接为 [[wikilink]]...")
    convert_all_links(output_dir, token_to_path)

    # ===== 校验 =====
    logger.info("正在校验迁移结果...")
    report = validate(output_dir, len(all_nodes), progress)
    report_path = os.path.join(output_dir, "migration_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    logger.info("迁移报告已保存: %s", report_path)

    logger.info("===== 迁移完成 =====")
    print(f"\n{progress.summary()}")
    print(f"报告: {report_path}")


if __name__ == "__main__":
    main()
