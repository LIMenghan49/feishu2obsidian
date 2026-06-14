import os
from dotenv import load_dotenv

load_dotenv()

# 飞书应用凭证
APP_ID = os.getenv("FEISHU_APP_ID")
APP_SECRET = os.getenv("FEISHU_APP_SECRET")

# 输出目录
OUTPUT_DIR = "./output"

# 可选：只迁移指定的知识空间 (留空则迁移全部)
SPACE_IDS = []

# 跳过的节点类型
SKIP_TYPES = ["mindnote", "board"]

# 限流参数
REQUEST_INTERVAL = 0.2  # 秒，每次 API 请求间隔
MAX_RETRIES = 3

# 日志
LOG_LEVEL = "INFO"
LOG_FILE = "migration.log"

# 飞书 API 基础地址
BASE_URL = "https://open.feishu.cn/open-apis"
