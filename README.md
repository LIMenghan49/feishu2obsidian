# feishu2obsidian

飞书知识库 → Obsidian Markdown 批量迁移工具。

14 个知识空间、261 篇文档，通过飞书开放 API 自动转换为 Obsidian vault，0 格式问题。

## 核心流程

```mermaid
graph LR
    A["飞书知识库"] --> B["OAuth 用户授权"]
    B --> C["递归遍历节点树"]
    C --> D["Block JSON → Markdown"]
    D --> E["下载图片/附件"]
    E --> F["内部链接 → [[wikilink]]"]
    F --> G["Obsidian Vault"]
```

## 文件说明

| 文件 | 作用 |
|------|------|
| `main.py` | 主流程入口，两遍扫描（转换→链接替换） |
| `oauth.py` | OAuth 用户授权 + token 缓存刷新 |
| `auth.py` | 应用身份 TokenManager（备用） |
| `wiki_crawler.py` | 递归遍历知识空间节点树 |
| `doc_parser.py` | Block JSON 递归解析 → Markdown |
| `media_downloader.py` | 图片/附件下载 |
| `link_converter.py` | 内部链接 → Obsidian `[[wikilink]]` |
| `progress.py` | 断点续传，JSON 进度文件 |
| `validator.py` | 迁移结果校验 + 报告生成 |
| `config.py` | 非敏感配置 |
| `scan_vault.py` | 扫描 vault frontmatter 元数据 |

## 快速开始

### 1. 创建飞书应用

飞书开放平台 → 创建企业自建应用 → 添加权限：
- `wiki:wiki:readonly`
- `docx:document:readonly`
- `drive:drive:readonly`

### 2. 配置

```bash
cp .env.example .env
# 编辑 .env，填入 FEISHU_APP_ID 和 FEISHU_APP_SECRET
pip install -r requirements.txt
```

### 3. 运行

```bash
python main.py
```

首次运行自动弹出浏览器完成 OAuth 授权，后续用 refresh_token 自动续期。

## 格式支持

| 飞书 | Obsidian | 状态 |
|------|----------|------|
| 标题 H1-H6 | `#` ~ `######` | 无损 |
| 加粗/斜体/删除线/行内代码 | `**/**` `/ * */` `~~` `` ` ``` | 无损 |
| 代码块 | ` ```lang ``` ` | 无损 |
| 有序/无序/任务列表 | `1.` `-` `- [ ]` | 无损 |
| 引用/分割线 | `>` `---` | 无损 |
| 表格 | Markdown 表格 | 无损 |
| 图片 | `![](./assets/xx.png)` | 无损 |
| 内部链接 | `[[wikilink]]` | 无损 |
| 公式 | `$LaTeX$` | 无损 |
| 高亮 | `==高亮==` | 需插件 |
| 文字颜色 | HTML `<font>` 兜底 | 有损 |
| 评论/思维导图/画板 | 无法迁移 | 丢失 |

## 已知限制

- API 频率限制 5~50 QPS，已做指数退避重试
- 飞书旧版 Doc 需新版 Docx API 兼容读取
- 图片 token 有时效，解析时立即下载
- Windows 文件名过滤特殊字符 `\ / : * ? " < > |`
- 个人知识库需 OAuth 用户授权（非 tenant_access_token）

## License

MIT
