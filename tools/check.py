#!/usr/bin/env python3
"""发布前质检。用法：python3 tools/check.py [--skip-net]

检查项：
  1. 条号连续性：references/ 各规章文件 **第X条** 从 1 连续到最大条号，无重复；
     00-index/00-front-school-intro/18-zhuoyue/49-fuwu-zhinan 无条号属正常（白名单）。
  2. 路径解析：所有文件中反引号包裹的相对路径（../ 或 ./ 开头）必须能解析到真实文件。
  3. 引用有效性：data/ 里以 "NN-短名 第X条" 形式引用的规章文件与条号必须存在。
  4. URL 活性：sources.md、references/49-fuwu-zhinan.md、data/*.md 中的 http(s) 链接
     状态码异常时报告（--skip-net 跳过）；已在正文标注"实测不通/打不开/无法连接"的链接视为已知失效，只复核不报错。
"""
import os
import re
import sys
import glob
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NO_ARTICLE_FILES = {"00-index.md", "00-front-school-intro.md",
                    "18-zhuoyue.md", "49-fuwu-zhinan.md"}
# 行内示意性路径（README 中举例的安装位置），不参与解析检查
ILLUSTRATIVE = {"./.seu-handbook-skill/SKILL.md"}
# 计划类工作文件（不随仓库发布），不参与检查
PLAN_WORKING = re.compile(r"PLAN-v\d+\.md$")

CN = {"零": 0, "〇": 0, "一": 1, "二": 2, "两": 2, "三": 3, "四": 4,
      "五": 5, "六": 6, "七": 7, "八": 8, "九": 9}

def c2i(s):
    if s == "十":
        return 10
    if len(s) == 1:
        return CN.get(s)
    if len(s) == 2 and s[0] == "十":
        return 10 + CN[s[1]]
    if len(s) == 2 and s[1] == "十":
        return CN[s[0]] * 10
    if len(s) == 3:
        return CN[s[0]] * 10 + CN[s[2]]
    return None

def rel(p):
    return os.path.relpath(p, ROOT)

def check_articles():
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "references/*.md"))):
        base = os.path.basename(f)
        txt = open(f, encoding="utf-8").read()
        nums = [v for v in (c2i(m) for m in
                re.findall(r"\*\*第([一二三四五六七八九十百零〇两]+)条\*\*", txt)) if v]
        if not nums:
            if base not in NO_ARTICLE_FILES:
                print(f"[条号] {base}: 未发现条号，且不在白名单"); bad += 1
            continue
        missing = [n for n in range(1, max(nums) + 1) if n not in nums]
        dup = sorted({n for n in nums if nums.count(n) > 1})
        if missing or dup:
            print(f"[条号] {base}: 缺={missing} 重复={dup}"); bad += 1
    return bad

def check_paths():
    bad = 0
    for f in glob.glob(os.path.join(ROOT, "**/*.md"), recursive=True):
        r = rel(f)
        if r.startswith(os.path.join(".zcode") + os.sep) or PLAN_WORKING.search(r):
            continue
        txt = open(f, encoding="utf-8").read()
        for link in re.findall(r"`(\.\.?/[^`]+)`", txt):
            if link in ILLUSTRATIVE or "/" not in link.strip("./"):
                continue
            if not os.path.exists(os.path.normpath(os.path.join(os.path.dirname(f), link))):
                print(f"[路径] {r}: `{link}` 解析不到文件"); bad += 1
    return bad

def check_citations():
    refs = {os.path.basename(p)[:-3] for p in
            glob.glob(os.path.join(ROOT, "references/*.md"))}
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data/*.md"))):
        txt = open(f, encoding="utf-8").read()
        byfile = {}
        for name, art in re.findall(r"(\d{2}-[a-z-]+)\s*第([一二三四五六七八九十百零〇两]+)条", txt):
            byfile.setdefault(name, set()).add(art)
        for stem, arts in byfile.items():
            if stem not in refs:
                print(f"[引用] {rel(f)}: 引用了不存在的文件 {stem}"); bad += 1
                continue
            have = set(re.findall(r"\*\*第([一二三四五六七八九十百零〇两]+)条\*\*",
                                  open(os.path.join(ROOT, "references", stem + ".md"),
                                       encoding="utf-8").read()))
            for a in arts:
                if a not in have:
                    print(f"[引用] {rel(f)}: 引用 {stem} 第{a}条，目标文件无此条号"); bad += 1
    return bad

def check_urls():
    # 行内已标注"实测不通/打不开/无法连接"的 URL 视为已知失效，只复核不报新错
    known_bad = set()
    for pat in ("sources.md", "README.md", "SKILL.md",
                "references/49-fuwu-zhinan.md", "data/*.md"):
        for f in glob.glob(os.path.join(ROOT, pat)):
            for line in open(f, encoding="utf-8"):
                if re.search(r"实测(不通|打不开|无法连接)", line):
                    known_bad.update(re.findall(r"https?://[a-zA-Z0-9./_-]+", line))
    urls = set()
    for pat in ("sources.md", "README.md", "SKILL.md",
                "references/49-fuwu-zhinan.md", "data/*.md"):
        for f in glob.glob(os.path.join(ROOT, pat)):
            urls.update(re.findall(r"https?://[a-zA-Z0-9./_-]+",
                                   open(f, encoding="utf-8").read()))
    bad = 0
    for u in sorted(urls):
        try:
            code = subprocess.run(
                ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code}",
                 "-L", "--max-time", "15", "-A", "Mozilla/5.0", u],
                capture_output=True, text=True, timeout=30).stdout.strip()
        except subprocess.TimeoutExpired:
            code = "000"
        if u in known_bad:
            print(f"[URL] {u} → {code}（已标注为已知失效，核实是否恢复）")
            continue
        if code not in ("200", "301", "302"):
            print(f"[URL] {u} → {code}（新失效，需标注或更新）"); bad += 1
    return bad

def main():
    skip_net = "--skip-net" in sys.argv
    results = {"条号连续性": check_articles(),
               "路径解析": check_paths(),
               "引用有效性": check_citations()}
    if not skip_net:
        results["URL 活性"] = check_urls()
    for k, v in results.items():
        print(f"{'✗' if v else '✓'} {k}: {v} 个问题")
    return 1 if any(results.values()) else 0

if __name__ == "__main__":
    sys.exit(main())
