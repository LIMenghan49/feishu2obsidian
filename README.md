# feishu2obsidian — 飞书知识库 → Markdown 批量导出工具

> 把飞书知识库完整搬进 Obsidian：保留图片、保留表格、保留链接、保留公式、保留目录结构。一行命令，全自动完成。

**14 个空间、261 篇飞书文档 → 312 篇 Obsidian Markdown。图片 153 张全部下载，格式零损坏，12 篇纯图片文档 OCR 恢复。**

## 为什么用这个

飞书官方只支持单篇导出 Word/PDF，知识库批量迁移只能自己来。这套脚本做了几件官方做不到的事：

- **保留图片** — 图片 token 有时效，解析时立即下载到本地 `assets/`，不会丢
- **保留链接** — 飞书内部文档链接全部转换为 Obsidian `[[wikilink]]`，可点击可反向链接
- **保留表格** — 普通表格 + 嵌入 Sheet 两种格式都无损转为 Markdown 表格
- **保留公式** — LaTeX 公式完整迁移，处理了换行断裂等坑
- **保留目录结构** — 飞书节点树映射为文件夹层级，原汁原味
- **纯图片文档 OCR** — 只有图片没有文字的文档，自动 OCR 转文字，不浪费任何内容
- **断点续传** — 中断后从上次位置继续，几百篇不用从头跑
- **自动编号** — 飞书标题序号自动保持，中文序号（一、/ 第一章 / ①）智能跳过不重复编号

## 实战数据

| 指标 | 数值 |
|------|------|
| 知识空间 | 14 个（13 个成功，1 个权限不足跳过） |
| 文档总数 | 261 篇 |
| 产出 Markdown | 312 篇 |
| 下载图片 | 153 张 |
| 格式问题 | 0 |
| 迁移失败 | 0 |

## 格式转换对照

| 飞书 | Obsidian | 保真度 |
|------|----------|--------|
| 标题 H1-H9 | `#` ~ `######`（H7-H9 压为 H6） | 基本无损 |
| 加粗 / 斜体 / 删除线 / 行内代码 | `** **` `* *` `~~` `` ` `` | 无损 |
| 代码块 | ` ```lang ``` ` | 无损 |
| 有序 / 无序 / 任务列表 | `1.` `-` `- [ ]` | 无损 |
| 引用 / 分割线 | `>` `---` | 无损 |
| 超链接 | `[文字](url)` | 无损 |
| 图片 | `![](./assets/xx.png)` 近距存放 | 无损 |
| 表格（普通 + 嵌入 Sheet） | Markdown 表格 | 无损 |
| 内部链接 / @提及 | `[[wikilink]]` | 无损 |
| LaTeX 公式 | `$...$` | 无损 |
| 高亮 | `==高亮==` | 需 Obsidian 插件 |
| 文字颜色 | `<font color="">` HTML 兜底 | 有损 |
| 评论 / 思维导图 / 画板 / 投票 | — | 无法迁移 |

## 快速开始

### 1. 创建飞书应用

[飞书开放平台](https://open.feishu.cn) → 创建企业自建应用 → 添加权限：

- `wiki:wiki:readonly`
- `docx:document:readonly`
- `drive:drive:readonly`

发布版本并通过管理员审核。

### 2. 配置

```bash
git clone https://github.com/LIMenghan49/feishu2obsidian.git
cd feishu2obsidian
cp .env.example .env
# 编辑 .env，填入 FEISHU_APP_ID 和 FEISHU_APP_SECRET
pip install -r requirements.txt
```

### 3. 运行

```bash
python main.py
```

首次运行自动弹出浏览器完成 OAuth 用户授权，后续用 refresh_token 自动续期，无需反复登录。

## 它怎么工作的

```
两遍扫描策略：

第一遍：遍历 + 转换 + 建映射
  递归遍历所有节点 → Block JSON 递归解析为 Markdown
  → 同步下载图片到本地 assets/ → 记录 obj_token → 文件路径映射表

第二遍：链接替换
  遍历所有 .md 文件 → 用映射表将飞书内部链接替换为 [[wikilink]]
```

## 已踩平的坑（在这套代码里都不是坑）

- 标题 key 不是 `heading` 而是 `heading1`~`heading9`，需动态拼
- 表格没有 row block，是扁平 cell 数组，必须按 `column_size` 分组
- 嵌入表格（Sheet）和普通表格是两套 API，Sheet 单元格值是富文本数组
- 有序列表不能写死 `1.`，需追踪计数器，连续递增、打断重置
- 标题自动编号需检测中文序号（一、/ 第一章 / 1. / ①）避免重复
- 图片 token 过期前必须下载，不能攒批
- 个人知识库必须用 OAuth 用户授权，`tenant_access_token` 读不到
- 公式 content 可能含换行，需替换为空格否则 LaTeX 断裂
- Windows 文件名需过滤 `\ / : * ? " < > |`
- API 限流 5~50 QPS，已做指数退避重试

## 文件说明

| 文件 | 职责 |
|------|------|
| `main.py` | 主流程，编排两遍扫描 |
| `oauth.py` | OAuth 用户授权 + token 自动刷新 |
| `wiki_crawler.py` | 递归遍历知识空间节点树 |
| `doc_parser.py` | Block JSON → Markdown（递归，核心） |
| `media_downloader.py` | 图片/附件即时下载 |
| `link_converter.py` | 内部链接 → `[[wikilink]]` |
| `progress.py` | 断点续传，JSON 进度持久化 |
| `validator.py` | 迁移后自动校验，生成报告 |
| `scan_vault.py` | 扫描 vault frontmatter 元数据 |
| `config.py` | 非敏感配置集中管理 |
| `auth.py` | 应用身份 TokenManager（备用） |

## License

MIT
