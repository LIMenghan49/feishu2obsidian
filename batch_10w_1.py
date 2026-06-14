"""十万个为什么 第一批15篇 元数据更新。"""
import os, re, glob

BASE = "c:/Users/LI/Desktop/笔记本/feishu2obsidian/output/十万个为什么"

metadata = {
    "37岁长春会计的婚恋与职业困惑解答（大冰）": {
        "summary": "用婚恋市场错位和职业瓶颈模型分析37岁女性的双重困境，给出务实的择偶和职业策略，可用于人生规划参考。",
        "topics": ["婚恋", "职业困惑", "年龄焦虑", "择偶策略"],
        "keywords": ["婚恋", "会计", "择偶", "职业瓶颈", "大冰"],
        "cognitive_level": "L2_concept",
        "related": ["[[年轻人不愿结婚与焦虑现象的底层逻辑探讨（大冰）]]", "[[好马不吃回头草分析]]", "[[异地恋如何更好的修成正果]]"],
    },
    "50w存款想在成都买房，冰哥联系房产销售帮忙梳理": {
        "summary": "从财务脆弱性和市场时机角度分析年轻夫妻在成都买房的决策逻辑，可用于购房决策参考。",
        "topics": ["买房", "成都", "财务分析", "房地产"],
        "keywords": ["买房", "成都", "50万", "房产", "贷款"],
        "cognitive_level": "L2_concept",
        "related": ["[[国内买房]]", "[[挣钱的本质是什么]]", "[[26.1 金钱心理学]]"],
    },
    "AI人类博士水平的问题解决能力如何体现以及gemini3.0的进步": {
        "summary": "通过GPQA等基准测试量化分析Gemini 3.0的博士级推理能力提升，可用于理解AI能力边界和技术趋势。",
        "topics": ["Gemini", "AI推理", "博士级", "基准测试"],
        "keywords": ["Gemini 3.0", "GPQA", "Deep Think", "推理能力"],
        "cognitive_level": "L2_concept",
        "related": ["[[2.3黄仁勋Cisco访谈]]", "[[对人类来说AI目前最大的缺陷]]", "[[2026智能体]]"],
    },
    "AI冲击下的软件工程师和求职": {
        "summary": "分析AI时代软件工程师核心价值从编码转向系统设计、Debug和担责，可用于技术职业规划。",
        "topics": ["AI冲击", "软件工程师", "职业转型", "核心价值"],
        "keywords": ["AI", "工程师", "编码贬值", "系统设计", "求职"],
        "cognitive_level": "L2_concept",
        "related": ["[[AI大厂与传统学校教育之间残酷的供需断层，以及现代年轻人的职业规划与生存困境]]", "[[求职方向：精准与灵活的平衡]]", "[[高中生进大厂是否只是学历贬值-_背后洞察]]"],
    },
    "AI大厂与传统学校教育之间残酷的供需断层，以及现代年轻人的职业规划与生存困境": {
        "summary": "揭示学校教育与企业需求的结构性错位，分析学生思维如何限制职业发展，可用于破除求职认知盲区。",
        "topics": ["教育错位", "供需断层", "学生思维", "职业规划"],
        "keywords": ["教育", "供需", "学生思维", "企业视角"],
        "cognitive_level": "L2_concept",
        "related": ["[[为什么大学的教育和社会需求错位]]", "[[AI冲击下的软件工程师和求职]]", "[[求职方向：精准与灵活的平衡]]"],
    },
    "Agent人机协作和自动驾驶的共性": {
        "summary": "用自动驾驶分级类比AI Agent协作模式，揭示人机协作从L1到L5的演进逻辑，可用于理解Agent落地应用。",
        "topics": ["Agent", "人机协作", "自动驾驶", "分级体系"],
        "keywords": ["Agent", "自动驾驶", "人机协作", "分级"],
        "cognitive_level": "L3_model",
        "related": ["[[2026智能体]]", "[[Agent思考探索]]", "[[AI产品所要学习的点]]"],
    },
    "Bernanke的环境不确定投资理论": {
        "summary": "用伯南克的不可逆性-不确定性理论解释为什么等待本身是有价值的期权，可用于投资决策和人生选择。",
        "topics": ["投资理论", "不确定性", "期权思维", "伯南克"],
        "keywords": ["Bernanke", "不确定性", "期权", "等待价值", "投资"],
        "cognitive_level": "L2_concept",
        "related": ["[[26.1 金钱心理学]]", "[[理想主义者和现实主义者之间的博弈？]]", "[[26.1 富爸爸穷爸爸]]"],
    },
    "GDP质量与国家发展模式": {
        "summary": "通过GDP构成质量分析不同国家发展模式的本质差异，可用于理解宏观经济和社会运行逻辑。",
        "topics": ["GDP", "经济发展", "国家模式", "宏观经济"],
        "keywords": ["GDP", "发展模式", "经济质量", "消费"],
        "cognitive_level": "L2_concept",
        "related": ["[[中国消费水平与国际对比]]", "[[26.1 金钱心理学]]", "[[韩国的社保问题]]"],
    },
    "INFJ-夹心人": {
        "summary": "用热-冷-热三层结构解析INFJ性格的外在温和与内在防御机制，可用于自我理解和人际关系。",
        "topics": ["INFJ", "性格分析", "防御机制", "人际关系"],
        "keywords": ["INFJ", "夹心人", "Fe", "察言观色", "防御"],
        "cognitive_level": "L2_concept",
        "related": ["[[INFJ适合什么计算机相关的工作？（央国企，数据分析）]]", "[[自我认知与成熟]]", "[[26.2.22 （宏观）摆脱隐身状态]]"],
    },
    "giffgaff英国手机卡": {
        "summary": "英国giffgaff手机卡的申请、激活和低成本保号实操指南，可用于注册海外AI服务。",
        "topics": ["手机卡", "海外服务", "低成本", "实操指南"],
        "keywords": ["giffgaff", "英国", "手机卡", "ChatGPT", "保号"],
        "cognitive_level": "L4_sop",
        "related": ["[[如何让gpt pro值回票钱]]", "[[Claude code指令详解]]"],
    },
    "三观和道德体系": {
        "summary": "系统梳理世界观、人生观、价值观的定义及其与道德体系的关系，可用于认知框架建设。",
        "topics": ["三观", "道德", "价值观", "世界观"],
        "keywords": ["三观", "世界观", "人生观", "价值观", "道德"],
        "cognitive_level": "L2_concept",
        "related": ["[[宽容与人性幽暗]]", "[[自我认知与成熟]]", "[[表象胜过实质（毒）]]"],
    },
    "中国消费水平与国际对比": {
        "summary": "引入新评估维度重新定义中国真实消费水平，揭示购买力平价和生活成本的国际差异，可用于经济认知。",
        "topics": ["消费水平", "国际对比", "购买力", "生活成本"],
        "keywords": ["消费", "购买力", "国际对比", "中国"],
        "cognitive_level": "L2_concept",
        "related": ["[[GDP质量与国家发展模式]]", "[[挣钱的本质是什么]]", "[[韩国的社保问题]]"],
    },
    "中式饭局儿童怎么解闷？": {
        "summary": "针对中式饭局中儿童无聊问题提出创意解决方案，平衡社交礼仪和儿童需求，可用于育儿和社交场景。",
        "topics": ["饭局", "儿童", "社交", "创意解决"],
        "keywords": ["饭局", "儿童", "无聊", "短视频", "解闷"],
        "cognitive_level": "L2_concept",
        "related": ["[[出生的鸿沟（教育，从容）]]", "[[儿童为什么语言学的更快更彻底？]]"],
    },
    "为什么不能长期在家？（大脑活力）": {
        "summary": "从神经科学角度解释长期宅家导致的认知退化、语言能力下降和情绪感知减弱，可用于自我管理。",
        "topics": ["宅家", "大脑活力", "认知退化", "社交"],
        "keywords": ["宅家", "大脑", "认知退化", "语言能力", "社交"],
        "cognitive_level": "L2_concept",
        "related": ["[[海马体恢复计划]]", "[[精力管理就是管理消耗和恢复]]", "[[脱离舒适圈漩涡]]"],
    },
    "为什么反复做自我毁灭的行为？": {
        "summary": "用隐秘心理收益和潜意识自虐机制解释为什么人明知后果仍重复自毁行为，可用于行为模式识别和改变。",
        "topics": ["自毁行为", "心理机制", "潜意识", "成瘾"],
        "keywords": ["自毁", "强迫重复", "心理收益", "成瘾", "熬夜"],
        "cognitive_level": "L2_concept",
        "related": ["[[26.3.20 多巴胺成瘾-ankerai飞行熬大夜]]", "[[脱离舒适圈漩涡]]", "[[隧道视野分析和解决]]"],
    },
}

count = 0
for title, meta in metadata.items():
    matches = glob.glob(os.path.join(BASE, title + "*.md"))
    if not matches:
        # try partial match
        matches = glob.glob(os.path.join(BASE, "*" + title[:10] + "*.md"))
    if not matches:
        print(f"SKIP: {title}")
        continue

    fpath = matches[0]
    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        continue

    old_fm = fm_match.group(1)
    body = content[fm_match.end():]

    new_lines = []
    seen = set()
    for line in old_fm.split("\n"):
        km = re.match(r"^(\w[\w_]*)\s*:", line)
        if km:
            key = km.group(1)
            seen.add(key)
            if key == "domain":
                new_lines.append('domain: "社会金融"')
            elif key == "summary":
                new_lines.append('summary: "' + meta["summary"] + '"')
            elif key == "cognitive_level":
                new_lines.append('cognitive_level: "' + meta["cognitive_level"] + '"')
            elif key == "status":
                new_lines.append('status: "active"')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    if "domain" not in seen:
        new_lines.append('domain: "社会金融"')
    if "summary" not in seen:
        new_lines.append('summary: "' + meta["summary"] + '"')
    if "cognitive_level" not in seen:
        new_lines.append('cognitive_level: "' + meta["cognitive_level"] + '"')
    if "status" not in seen:
        new_lines.append('status: "active"')
    if "topics" not in seen:
        t_str = ", ".join('"' + t + '"' for t in meta["topics"])
        new_lines.append("topics: [" + t_str + "]")
    if "keywords" not in seen:
        k_str = ", ".join('"' + k + '"' for k in meta["keywords"])
        new_lines.append("keywords: [" + k_str + "]")
    if "related" not in seen:
        new_lines.append("related:")
        for r in meta["related"]:
            new_lines.append('  - "' + r + '"')

    new_content = "---\n" + "\n".join(new_lines) + "\n---" + body
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(new_content)
    count += 1

print(f"Done: {count}/15")