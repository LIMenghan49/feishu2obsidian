import os, re, glob

BASE = "c:/Users/LI/Desktop/笔记本/feishu2obsidian/output"

fixes = [
    (glob.glob(os.path.join(BASE, "我该怎么做", "*胜利者*")), {
        "domain": "认知心理",
        "summary": "用胜利者效应打破习得性无助的恶性循环，通过小胜利恢复自信和行动力，可用于行为改变。",
        "topics": ["习得性无助", "胜利者效应", "自信", "行动力"],
        "keywords": ["习得性无助", "小胜利", "自信"],
        "cognitive_level": "L3_model",
    }),
    (glob.glob(os.path.join(BASE, "悦孚思实习资料", "*跨境硬件*")), {
        "domain": "职业发展",
        "summary": "跨境电商BA实习全流程复盘，涵盖VOC分析、竞品研究、数据看板等，可直接用于简历和面试表达。",
        "topics": ["BA实习", "跨境电商", "项目复盘", "作品集"],
        "keywords": ["BA", "跨境电商", "VOC", "竞品"],
        "cognitive_level": "L5_output",
    }),
]

for matches, meta in fixes:
    for fpath in matches:
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
                    new_lines.append('domain: "' + meta["domain"] + '"')
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
            new_lines.append('domain: "' + meta["domain"] + '"')
        if "summary" not in seen:
            new_lines.append('summary: "' + meta["summary"] + '"')
        if "cognitive_level" not in seen:
            new_lines.append('cognitive_level: "' + meta["cognitive_level"] + '"')
        if "topics" not in seen:
            t_str = ", ".join('"' + t + '"' for t in meta["topics"])
            new_lines.append("topics: [" + t_str + "]")
        if "keywords" not in seen:
            k_str = ", ".join('"' + k + '"' for k in meta["keywords"])
            new_lines.append("keywords: [" + k_str + "]")
        new_content = "---\n" + "\n".join(new_lines) + "\n---" + body
        with open(fpath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("OK:", os.path.basename(fpath))