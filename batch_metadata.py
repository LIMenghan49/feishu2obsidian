"""批量更新30篇高价值笔记的frontmatter元数据。"""
import os
import re

BASE = "c:/Users/LI/Desktop/笔记本/feishu2obsidian/output"

metadata = {
    "AI/2.3黄仁勋Cisco访谈.md": {"domain": "AI与技术", "summary": "从黄仁勋访谈中提炼AI时代的产品判断、技术趋势和长期主义思维，可用于AI产品方向选择和职业决策。", "topics": ["AI趋势", "GPU", "产品判断", "长期主义"], "keywords": ["黄仁勋", "NVIDIA", "Cisco", "AI基础设施"], "cognitive_level": "L2_concept", "related": ["[[AI产品所要学习的点]]", "[[2026智能体]]", "[[求职方向：精准与灵活的平衡]]"]},
    "AI/2026智能体.md": {"domain": "AI与技术", "summary": "梳理2026年智能体(Agent)技术发展现状、分级体系和应用场景，可用于AI产品方向判断和技术学习。", "topics": ["智能体", "Agent", "AI产品", "L2任务级"], "keywords": ["Agent", "智能体分级", "Claude Code", "sub-agent"], "cognitive_level": "L2_concept", "related": ["[[Agent思考探索]]", "[[Claude code指令详解]]", "[[AI产品所要学习的点]]"]},
    "AI/AI产品所要学习的点.md": {"domain": "AI与技术", "summary": "整理AI产品经理需要掌握的核心能力和学习方向，可用于职业规划和技能树建设。", "topics": ["AI产品", "能力模型", "职业规划"], "keywords": ["产品经理", "AI应用", "技能树"], "cognitive_level": "L3_model", "related": ["[[什么样的AI产品值得去]]", "[[2.3黄仁勋Cisco访谈]]", "[[求职方向：精准与灵活的平衡]]"]},
    "AI/Claude code指令详解.md": {"domain": "AI与技术", "summary": "详解Claude Code的核心指令和使用技巧，可用于提升AI辅助编程效率。", "topics": ["Claude Code", "AI编程", "工具使用"], "keywords": ["Claude", "指令", "CLI", "编程助手"], "cognitive_level": "L4_sop", "related": ["[[配置n8nAI资讯工具]]", "[[2026智能体]]", "[[AI产品所要学习的点]]"]},
    "AI/配置n8nAI资讯工具.md": {"domain": "AI与技术", "summary": "记录n8n自动化工具配置AI资讯采集流程的步骤，可用于信息源自动化建设。", "topics": ["n8n", "自动化", "AI资讯", "工作流"], "keywords": ["n8n", "自动化", "资讯采集", "workflow"], "cognitive_level": "L4_sop", "related": ["[[AI信息源建设]]", "[[Claude code指令详解]]", "[[2026智能体]]"]},
    "我该怎么做/AI+费曼学习法三步.md": {"domain": "学习系统", "summary": "用AI辅助费曼学习法的三步流程来加速知识内化和检验理解深度，可用于任何新知识学习。", "topics": ["费曼学习法", "AI辅助学习", "知识内化"], "keywords": ["费曼", "教别人", "AI学习", "理解检验"], "cognitive_level": "L4_sop", "related": ["[[如何高效的学习]]", "[[NotebookLM 48小时入门一个领域]]"]},
    "我该怎么做/如何高效的学习.md": {"domain": "学习系统", "summary": "整理高效学习的核心方法论和实操策略，可用于建立个人学习系统。", "topics": ["学习方法", "效率", "知识管理"], "keywords": ["学习效率", "方法论", "记忆", "复习"], "cognitive_level": "L3_model", "related": ["[[AI+费曼学习法三步]]", "[[精力管理就是管理消耗和恢复]]", "[[自学也要心流哟]]"]},
    "我该怎么做/精力管理就是管理消耗和恢复.md": {"domain": "学习系统", "summary": "用消耗-恢复模型解释精力管理的本质，通过睡眠、运动、任务切分恢复学习精力，可用于日常状态优化。", "topics": ["精力管理", "恢复", "状态优化", "睡眠"], "keywords": ["精力", "消耗", "恢复", "运动", "睡眠"], "cognitive_level": "L3_model", "related": ["[[海马体恢复计划]]", "[[脱离舒适圈漩涡]]", "[[隧道视野分析和解决]]"]},
    "我该怎么做/脱离舒适圈漩涡.md": {"domain": "认知心理", "summary": "分析舒适圈形成机制和脱离策略，用渐进暴露和小胜利打破惯性循环，可用于行为改变。", "topics": ["舒适圈", "行为改变", "渐进暴露"], "keywords": ["舒适圈", "惯性", "突破", "行动力"], "cognitive_level": "L3_model", "related": ["[[如何用\"胜利者效应\"解决习得性无助？]]", "[[精力管理就是管理消耗和恢复]]", "[[克服恐惧]]"]},
    "我该怎么做/隧道视野分析和解决.md": {"domain": "认知心理", "summary": "用隧道视野模型解释为什么压力下人会过度聚焦而忽略全局，给出跳出隧道的具体方法，可用于决策和情绪管理。", "topics": ["隧道视野", "认知偏差", "决策", "压力"], "keywords": ["隧道视野", "压力", "全局思维", "认知偏差"], "cognitive_level": "L3_model", "related": ["[[精力管理就是管理消耗和恢复]]", "[[情绪管理与成功]]"]},
    "我该怎么做/情绪管理与成功.md": {"domain": "认知心理", "summary": "分析情绪对决策和行动力的影响机制，给出情绪调节的实操方法，可用于日常情绪管理和自我成长。", "topics": ["情绪管理", "自我调节", "成功", "心理"], "keywords": ["情绪", "调节", "决策", "行动力"], "cognitive_level": "L2_concept", "related": ["[[隧道视野分析和解决]]", "[[26.3.20 多巴胺成瘾-ankerai飞行熬大夜]]"]},
    "我该怎么做/如何用\"胜利者效应\"解决习得性无助？.md": {"domain": "认知心理", "summary": "用胜利者效应打破习得性无助的恶性循环，通过小胜利恢复自信和行动力，可用于行为改变。", "topics": ["习得性无助", "胜利者效应", "自信", "行动力"], "keywords": ["习得性无助", "小胜利", "自信", "行动"], "cognitive_level": "L3_model", "related": ["[[脱离舒适圈漩涡]]", "[[海马体恢复计划]]", "[[精力管理就是管理消耗和恢复]]"]},
    "我该怎么做/海马体恢复计划.md": {"domain": "认知心理", "summary": "基于神经科学设计海马体功能恢复方案，通过运动、睡眠和认知训练改善记忆和学习能力，可用于长期认知提升。", "topics": ["海马体", "记忆", "神经科学", "认知恢复"], "keywords": ["海马体", "记忆力", "运动", "睡眠", "神经可塑性"], "cognitive_level": "L4_sop", "related": ["[[精力管理就是管理消耗和恢复]]", "[[贫困如何影响海马体]]"]},
    "我该怎么做/个人成长与心理突破的7大核心法则：改善人生的心态转变.md": {"domain": "认知心理", "summary": "总结7个心态转变法则来突破自我限制和心理障碍，可用于自我成长和行为改变。", "topics": ["心态转变", "自我成长", "心理突破"], "keywords": ["心态", "成长", "突破", "法则"], "cognitive_level": "L2_concept", "related": ["[[脱离舒适圈漩涡]]", "[[对自己人生负责]]", "[[克服恐惧]]"]},
    "我该怎么做/像公司一样管理自己的人生.md": {"domain": "学习系统", "summary": "用企业管理思维来管理个人生活和成长，包括战略、OKR、复盘，可用于建立个人管理系统。", "topics": ["自我管理", "OKR", "复盘", "系统思维"], "keywords": ["管理", "OKR", "复盘", "战略", "人生"], "cognitive_level": "L3_model", "related": ["[[早起掌控感SOP]]", "[[精力管理就是管理消耗和恢复]]", "[[如何高效的学习]]"]},
    "工作这一块/求职方向：精准与灵活的平衡.md": {"domain": "职业发展", "summary": "分析求职中精准定位和灵活应变的平衡策略，帮助在多个方向中做出理性选择，可用于求职决策。", "topics": ["求职策略", "职业定位", "决策"], "keywords": ["求职", "方向", "定位", "灵活"], "cognitive_level": "L3_model", "related": ["[[INFJ适合什么计算机相关的工作？（央国企，数据分析）]]", "[[1.17 公司和岗位方向梳理]]", "[[找公司SOP]]"]},
    "工作这一块/INFJ适合什么计算机相关的工作？（央国企，数据分析）.md": {"domain": "职业发展", "summary": "从INFJ性格特质出发分析适合的计算机岗位方向，聚焦央国企和数据分析，可用于职业规划。", "topics": ["INFJ", "职业规划", "央国企", "数据分析"], "keywords": ["INFJ", "性格", "央国企", "数据分析"], "cognitive_level": "L3_model", "related": ["[[求职方向：精准与灵活的平衡]]", "[[数据分析和AI产品应该做什么]]", "[[（秋招经验贴）成都央国企计算机]]"]},
    "工作这一块/数据分析和AI产品应该做什么.md": {"domain": "职业发展", "summary": "梳理数据分析和AI产品两个方向的核心能力要求和学习路径，可用于技能树建设和求职准备。", "topics": ["数据分析", "AI产品", "能力要求", "学习路径"], "keywords": ["数据分析", "AI产品", "技能", "学习"], "cognitive_level": "L3_model", "related": ["[[AI产品所要学习的点]]", "[[INFJ适合什么计算机相关的工作？（央国企，数据分析）]]", "[[跨境硬件商业分析(BA)实习全复盘与作品集]]"]},
    "工作这一块/找公司SOP.md": {"domain": "职业发展", "summary": "标准化的找公司信息收集和筛选流程，可直接复用于求职准备。", "topics": ["求职", "SOP", "公司筛选"], "keywords": ["找公司", "SOP", "信息收集"], "cognitive_level": "L4_sop", "related": ["[[求职方向：精准与灵活的平衡]]", "[[企业信息收集]]", "[[面试SOP]]"]},
    "工作这一块/（秋招经验贴）双非本+QS100求职上岸经验与复盘.md": {"domain": "职业发展", "summary": "双非本科+QS100硕士的秋招全流程复盘，含策略、踩坑和上岸经验，可用于求职参考。", "topics": ["秋招", "求职复盘", "经验分享"], "keywords": ["秋招", "双非", "QS100", "上岸"], "cognitive_level": "L2_concept", "related": ["[[（秋招经验贴）成都央国企计算机]]", "[[（秋招经验贴）港三金融科技硕成都秋招复盘]]", "[[求职方向：精准与灵活的平衡]]"]},
    "工作这一块/（秋招经验贴）成都央国企计算机.md": {"domain": "职业发展", "summary": "成都央国企计算机岗秋招经验复盘，含岗位分析、面试要点和避坑指南，可用于央国企求职准备。", "topics": ["秋招", "央国企", "成都", "计算机"], "keywords": ["央国企", "成都", "秋招", "面试"], "cognitive_level": "L2_concept", "related": ["[[INFJ适合什么计算机相关的工作？（央国企，数据分析）]]", "[[国央企秋招误区]]"]},
    "悦孚思实习资料/跨境硬件商业分析(BA)实习全复盘与作品集.md": {"domain": "职业发展", "summary": "跨境电商BA实习全流程复盘，涵盖VOC分析、竞品研究、数据看板等，可直接用于简历和面试表达。", "topics": ["BA实习", "跨境电商", "项目复盘", "作品集"], "keywords": ["BA", "跨境电商", "VOC", "竞品", "数据看板"], "cognitive_level": "L5_output", "related": ["[[椅子评论分析]]", "[[LLM电商评论洞察与分析系统]]", "[[数据分析和AI产品应该做什么]]"]},
    "悦孚思实习资料/椅子评论分析.md": {"domain": "职业发展", "summary": "基于用户评论数据提炼人体工学椅的痛点排名和需求洞察，可用于面试中的数据分析项目表达。", "topics": ["评论分析", "VOC", "用户需求"], "keywords": ["评论", "椅子", "痛点", "VOC"], "cognitive_level": "L3_model", "related": ["[[跨境硬件商业分析(BA)实习全复盘与作品集]]", "[[LLM电商评论洞察与分析系统]]"]},
    "悦孚思实习资料/LLM电商评论洞察与分析系统.md": {"domain": "AI与技术", "summary": "用LLM构建电商评论自动化洞察系统，实现VOC分析和需求提取，可用于AI+数据分析项目展示。", "topics": ["LLM", "电商评论", "VOC", "自动化"], "keywords": ["LLM", "评论分析", "情感分析", "NLP"], "cognitive_level": "L4_sop", "related": ["[[椅子评论分析]]", "[[跨境硬件商业分析(BA)实习全复盘与作品集]]"]},
    "自我剖析/26.3.20 多巴胺成瘾-ankerai飞行熬大夜.md": {"domain": "认知心理", "summary": "剖析多巴胺成瘾机制导致的熬夜和注意力失控问题，可用于自我行为模式识别和改善。", "topics": ["多巴胺", "成瘾", "注意力", "熬夜"], "keywords": ["多巴胺", "成瘾", "熬夜", "自控力"], "cognitive_level": "L2_concept", "related": ["[[脱离舒适圈漩涡]]", "[[精力管理就是管理消耗和恢复]]", "[[情绪管理与成功]]"]},
    "自我剖析/26.4 山姆维权.md": {"domain": "认知心理", "summary": "通过山姆超市维权事件剖析权威顺从和自我价值感不足等心理障碍，可用于识别社交中的心理壁垒。", "topics": ["维权", "权威顺从", "自我价值感"], "keywords": ["维权", "山姆", "顺从", "自我价值"], "cognitive_level": "L2_concept", "related": ["[[2.4 经典球场上遇到指责摆烂哥]]", "[[26.3.8 斤斤计较]]", "[[26.2.22 （宏观）摆脱隐身状态]]"]},
    "自我剖析/26.2.22 （宏观）摆脱隐身状态.md": {"domain": "认知心理", "summary": "从宏观视角分析社交中隐身状态的成因和摆脱策略，可用于提升社交存在感和自信。", "topics": ["隐身状态", "社交", "自信", "存在感"], "keywords": ["隐身", "社交", "存在感", "自信"], "cognitive_level": "L2_concept", "related": ["[[26.4 山姆维权]]", "[[2.4 经典球场上遇到指责摆烂哥]]", "[[自我认知与成熟]]"]},
    "书籍影视记录/26.1 金钱心理学.md": {"domain": "社会金融", "summary": "从行为金融视角解释财富积累中行为和风险偏好比收益率更重要，可用于投资决策和金钱观建设。", "topics": ["金钱心理", "投资", "风险", "行为金融"], "keywords": ["金钱心理学", "Morgan Housel", "投资", "风险"], "cognitive_level": "L2_concept", "related": ["[[26.1 富爸爸穷爸爸]]", "[[26.1白银市场的暴涨逻辑（Gamma Squeeze）&国内LOF搬砖]]"]},
    "书籍影视记录/26.1 富爸爸穷爸爸.md": {"domain": "社会金融", "summary": "用资产/负债思维和现金流象限解释财富自由的底层逻辑，可用于个人理财观建设。", "topics": ["财务自由", "资产负债", "现金流"], "keywords": ["富爸爸", "穷爸爸", "资产", "负债"], "cognitive_level": "L2_concept", "related": ["[[26.1 金钱心理学]]", "[[保险公司，以及理财保险]]", "[[挣钱的本质是什么]]"]},
    "交易员李孟韩/26.1白银市场的暴涨逻辑（Gamma Squeeze）&国内LOF搬砖.md": {"domain": "社会金融", "summary": "分析白银市场Gamma Squeeze暴涨机制和国内LOF搬砖套利策略，可用于投资逻辑理解。", "topics": ["白银", "Gamma Squeeze", "LOF", "套利"], "keywords": ["白银", "Gamma Squeeze", "LOF", "搬砖"], "cognitive_level": "L2_concept", "related": ["[[26.1 金钱心理学]]", "[[26.1 富爸爸穷爸爸]]"]},
}

count = 0
for relpath, meta in metadata.items():
    fpath = os.path.join(BASE, relpath)
    if not os.path.exists(fpath):
        print(f"SKIP: {relpath}")
        continue

    with open(fpath, "r", encoding="utf-8") as f:
        content = f.read()

    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    if not fm_match:
        print(f"NO FM: {relpath}")
        continue

    old_fm = fm_match.group(1)
    body = content[fm_match.end():]

    # Parse existing key-value pairs
    new_lines = []
    seen_keys = set()
    for line in old_fm.split("\n"):
        key_m = re.match(r"^(\w[\w_]*)\s*:", line)
        if key_m:
            key = key_m.group(1)
            seen_keys.add(key)
            if key == "domain":
                new_lines.append(f'domain: "{meta["domain"]}"')
            elif key == "summary":
                new_lines.append(f'summary: "{meta["summary"]}"')
            elif key == "cognitive_level":
                new_lines.append(f'cognitive_level: "{meta["cognitive_level"]}"')
            elif key == "status":
                new_lines.append('status: "active"')
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    # Add missing fields
    if "domain" not in seen_keys:
        new_lines.append(f'domain: "{meta["domain"]}"')
    if "summary" not in seen_keys:
        new_lines.append(f'summary: "{meta["summary"]}"')
    if "cognitive_level" not in seen_keys:
        new_lines.append(f'cognitive_level: "{meta["cognitive_level"]}"')
    if "status" not in seen_keys:
        new_lines.append('status: "active"')
    if "topics" not in seen_keys:
        topics_str = ", ".join(f'"{t}"' for t in meta["topics"])
        new_lines.append(f"topics: [{topics_str}]")
    if "keywords" not in seen_keys:
        kw_str = ", ".join(f'"{k}"' for k in meta["keywords"])
        new_lines.append(f"keywords: [{kw_str}]")
    if "related" not in seen_keys:
        new_lines.append("related:")
        for r in meta["related"]:
            new_lines.append(f'  - "{r}"')

    new_fm = "\n".join(new_lines)
    new_content = f"---\n{new_fm}\n---{body}"

    with open(fpath, "w", encoding="utf-8") as f:
        f.write(new_content)
    count += 1

print(f"Done: {count}/30")