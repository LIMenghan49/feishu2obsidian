"""扫描 vault 所有笔记的 frontmatter，输出结构化数据供 index.md 生成"""
import os, re, json
from collections import defaultdict

VAULT = os.path.join(os.path.dirname(__file__), 'output')
SKIP_DIRS = {'.obsidian', '.git', 'raw', '.trash'}

def scan():
    notes = []
    for root, dirs, files in os.walk(VAULT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for f in files:
            if not f.endswith('.md'):
                continue
            path = os.path.join(root, f)
            rel = os.path.relpath(path, VAULT)
            parts = rel.replace('\\', '/').split('/')
            folder = parts[0] if len(parts) > 1 else 'ROOT'
            name = f[:-3]
            try:
                with open(path, 'r', encoding='utf-8') as fh:
                    content = fh.read(3000)
            except:
                continue
            fm = {}
            m = re.match(r'^---\s*\n(.*?)\n---', content, re.DOTALL)
            if m:
                for line in m.group(1).split('\n'):
                    kv = line.split(':', 1)
                    if len(kv) == 2:
                        k = kv[0].strip()
                        v = kv[1].strip().strip('"').strip("'")
                        if k in ('summary','domain','cognitive_level','status','type','space'):
                            fm[k] = v
            notes.append({
                'name': name,
                'folder': folder,
                'domain': fm.get('domain', ''),
                'summary': fm.get('summary', ''),
                'cog': fm.get('cognitive_level', ''),
                'status': fm.get('status', ''),
                'type': fm.get('type', ''),
                'space': fm.get('space', ''),
            })
    return notes

if __name__ == '__main__':
    notes = scan()
    by_domain = defaultdict(list)
    for n in notes:
        d = n['domain'] if n['domain'] else '未分类'
        by_domain[d].append(n)

    print(f"总笔记数: {len(notes)}")
    print()
    for domain in ['AI与技术', '职业发展', '学习系统', '认知心理', '社会金融', '生活与复盘', '未分类']:
        items = by_domain.get(domain, [])
        if not items:
            continue
        print(f"## {domain} ({len(items)}篇)")
        for n in sorted(items, key=lambda x: x['name']):
            s = n['summary'][:70] if n['summary'] else '(缺 summary)'
            cog = n['cog'] if n['cog'] else '?'
            st = n['status'] if n['status'] else '?'
            print(f"- [[{n['name']}]] — {s} ({cog}, {st})")
        print()

    # Stats
    missing_summary = sum(1 for n in notes if not n['summary'])
    missing_domain = sum(1 for n in notes if not n['domain'])
    missing_cog = sum(1 for n in notes if not n['cog'])
    print(f"--- 缺失统计 ---")
    print(f"缺 summary: {missing_summary}/{len(notes)}")
    print(f"缺 domain: {missing_domain}/{len(notes)}")
    print(f"缺 cognitive_level: {missing_cog}/{len(notes)}")
