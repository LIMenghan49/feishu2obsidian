"""迁移结果校验，生成 migration_report.md。"""
import os
import re
import logging

logger = logging.getLogger(__name__)

IMAGE_REF_RE = re.compile(r'!\[.*?\]\((\./assets/[^)]+)\)')
WIKILINK_RE = re.compile(r'\[\[([^|\]]+)(?:\|[^\]]+)?\]\]')


def validate(output_dir: str, total_nodes: int, progress) -> str:
    """校验迁移结果，返回报告 Markdown 文本。"""
    md_files = []
    image_files = set()

    for root, _, files in os.walk(output_dir):
        for fname in files:
            fpath = os.path.join(root, fname)
            if fname.endswith(".md"):
                md_files.append(fpath)
            else:
                # 记录所有非 md 文件（图片/附件）
                image_files.add(fpath)

    # 检查图片引用完整性
    broken_images = []
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        md_dir = os.path.dirname(md_path)
        for match in IMAGE_REF_RE.finditer(content):
            ref_path = match.group(1)
            abs_path = os.path.normpath(os.path.join(md_dir, ref_path))
            if not os.path.exists(abs_path):
                broken_images.append((md_path, ref_path))

    # 检查 wikilink 有效性
    all_md_names = {os.path.splitext(os.path.basename(f))[0] for f in md_files}
    broken_links = []
    for md_path in md_files:
        with open(md_path, "r", encoding="utf-8") as f:
            content = f.read()
        for match in WIKILINK_RE.finditer(content):
            link_target = match.group(1)
            if link_target not in all_md_names:
                broken_links.append((md_path, link_target))

    # 统计
    completed = len(progress.completed)
    failed = len(progress.failed)
    skipped = total_nodes - completed - failed
    total_images = len(image_files)

    # 生成报告
    lines = [
        "# 迁移报告\n",
        "## 统计摘要\n",
        f"| 项目 | 数量 |",
        f"|------|------|",
        f"| 知识库节点总数 | {total_nodes} |",
        f"| 成功迁移 | {completed} |",
        f"| 失败 | {failed} |",
        f"| 跳过 | {skipped} |",
        f"| 生成 .md 文件 | {len(md_files)} |",
        f"| 下载图片/附件 | {total_images} |",
        f"| 失效图片引用 | {len(broken_images)} |",
        f"| 失效 wikilink | {len(broken_links)} |",
        "",
    ]

    if progress.failed:
        lines.append("## 失败清单\n")
        lines.append("| 文档标题 | 错误信息 | 重试次数 |")
        lines.append("|---------|---------|---------|")
        for token, info in progress.failed.items():
            title = info.get("title", token)
            error = info.get("error", "未知")
            retries = info.get("retries", 0)
            lines.append(f"| {title} | {error} | {retries} |")
        lines.append("")

    if broken_images:
        lines.append("## 失效图片引用\n")
        for md_path, ref in broken_images[:50]:  # 最多列 50 个
            rel = os.path.relpath(md_path, output_dir)
            lines.append(f"- `{rel}` → `{ref}`")
        lines.append("")

    if broken_links:
        lines.append("## 失效 wikilink\n")
        for md_path, target in broken_links[:50]:
            rel = os.path.relpath(md_path, output_dir)
            lines.append(f"- `{rel}` → `[[{target}]]`")
        lines.append("")

    report = "\n".join(lines)
    logger.info("校验完成: %d 成功, %d 失败, %d 失效图片, %d 失效链接",
                completed, failed, len(broken_images), len(broken_links))
    return report
