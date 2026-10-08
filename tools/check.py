#!/usr/bin/env python3
"""发布前质检。用法：python3 tools/check.py [--skip-net]

检查项：
  1. 条号连续性：references/ 各规章文件 **第X条** 从 1 连续到最大条号，无重复；
     00-index/00-front-school-intro/18-zhuoyue/49-fuwu-zhinan 无条号属正常（白名单）。
  2. 末条完整性：references/ 各规章的末条应为"负责解释/自…施行"条款。末条不是，
     通常是尾条被整条删掉了——第 1 项只查 1..max 内部缺号，尾条被删后 max 变小、
     内部仍连续，查不出来。
  3. 路径解析：所有文件中反引号包裹的相对路径（../ 或 ./ 开头）必须能解析到真实文件。
  4. 引用有效性：data/ 里以 "NN-短名 第X条" 形式引用的规章文件与条号必须存在。
  5. 引用内容一致：data/ 表格行正文中的数值必须能在所引条款原文中找到。第 4 项只验证
     "第X条存在"；本项验证"这行的数值确实出自所引条款"——依据列漏列条款、数值抄错，
     都在这里暴露。行内含 <!-- 数值另有出处 --> 时跳过。
  6. URL 活性：sources.md、references/49-fuwu-zhinan.md、data/*.md 中的 http(s) 链接
     状态码异常时报告（--skip-net 跳过）；已在正文标注"实测不通/打不开/无法连接"的链接视为已知失效，只复核不报错。
  7. 知识包同步：pack/seu-handbook.md 与 SKILL.md/data/sources/00-index 内容一致
     （不一致说明改了源忘了重新生成）。

已知边界（不要据此认为"全绿=内容正确"）：
  - 第 1、2 项管"条号齐全"，管不了**条内漏字漏句**。变异测试已验证：删掉末条、
    依据列漏列条款都能被抓到；但把第二十八条里的"和安全教育要求"删掉这类
    不含数值的条内删减，本工具查不出，仍须人工对照手册原书。
  - 第 5 项只核对"数值是否在所引条款"，**不判断数值用得对不对、位置对不对**。
    变异测试已验证：绩点 3.8→3.9、SCI 12→14 能被抓到；但把 SRTP 良好档的
    系数 0.5 改成 0.6（0.6 在同一条款的竞赛倍数里也存在）会漏过。要查"这一格
    对应原文哪一句"，仍须人工。
  - 条号本身是否与手册一致（多号/少号/错号），需要 tools/rebuild.md 的年度更新流程
    对着原书核对。
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

# references/ 各规章文件现有的条号集合（引用未指明条号时兜底用）
REF_STEMS = {}
for _p in glob.glob(os.path.join(ROOT, "references", "*.md")):
    _t = open(_p, encoding="utf-8").read()
    REF_STEMS[os.path.basename(_p)[:-3]] = {
        v for v in (c2i(m) for m in
                    re.findall(r"\*\*第([一二三四五六七八九十百零〇两]+)条\*\*", _t)) if v}

def rel(p):
    return os.path.relpath(p, ROOT)

STEM_RE = re.compile(r"(\d{2}-[a-z-]+|appendix-[a-z]+-\d+)")
CLAUSE_RE = re.compile(
    r"第([一二三四五六七八九十百零〇两]+)"
    r"(?:[、,，]\s*([一二三四五六七八九十百零〇两]+))*"
    r"(?:\s*至\s*([一二三四五六七八九十百零〇两]+))?条")

def expand_clauses(seg):
    """把 "第X条"/"第X、Y、Z条"/"第X至Y条" 展开成条号数字集合。"""
    out = set()
    for m in CLAUSE_RE.finditer(seg):
        for g in re.findall(r"[一二三四五六七八九十百零〇两]+", m.group(0)):
            v = c2i(g)
            if v:
                out.add(v)
        if m.group(3):
            first, last = c2i(m.group(1)), c2i(m.group(3))
            if first and last:
                out.update(range(first, last + 1))
    return out

def clause_text(path, nums):
    """取指定条号的正文（从 **第X条** 到下一条之前）。"""
    txt = open(path, encoding="utf-8").read()
    hits = [(m.start(), c2i(m.group(1))) for m in
            re.finditer(r"\*\*第([一二三四五六七八九十百零〇两]+)条\*\*", txt)]
    hits = [(p, n) for p, n in hits if n]
    pieces = []
    for i, (pos, n) in enumerate(hits):
        if n not in nums:
            continue
        end = hits[i + 1][0] if i + 1 < len(hits) else len(txt)
        pieces.append(txt[pos:end])
    return "".join(pieces)

# 表格行里必然出现的编号/年份，不代表正文数值
NUM_DENY = {"0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "100",
            "2003", "2019", "2020", "2023", "2025", "2026"}
TAIL_OK = re.compile(r"负责解释|授权[^。]{0,20}解释"
                     r"|(?:自|從|从)[^。]{0,20}(?:施行|执行|实施|印发之日|公布之日)")
# 带查询串的 URL（如 shields.io 徽章 ?style=flat-square）也要整条取到，
# 否则查的是被截断的地址，稳定的链接会被误报为失效
URL_RE = r"https?://[a-zA-Z0-9./_%?=&:+~-]+"

def check_tail_article():
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "references/*.md"))):
        base = os.path.basename(f)
        if base in NO_ARTICLE_FILES:
            continue
        txt = open(f, encoding="utf-8").read()
        hits = [(m.start(), c2i(m.group(1))) for m in
                re.finditer(r"\*\*第([一二三四五六七八九十百零〇两]+)条\*\*", txt)]
        hits = [(p, n) for p, n in hits if n]
        if not hits:
            continue
        pos, n = hits[-1]
        if not TAIL_OK.search(txt[pos:]):
            print(f"[末条] {base}: 末条为第{n}条，但内容不是解释/施行条款，"
                  f"疑似尾条被整条删除——请对照手册原书核对"); bad += 1
    return bad

def check_citation_content():
    """表格行正文中的数值必须能在所引条款原文中找到。

    依据来源有两级：行内自己的"依据"列优先；行内没有时，继承该表格上方
    最近的"依据：…"小节级说明。行内含 <!-- 数值另有出处 --> 可跳过。
    """
    bad = 0
    for f in sorted(glob.glob(os.path.join(ROOT, "data/*.md"))):
        r = rel(f)
        section = set()
        for lineno, line in enumerate(open(f, encoding="utf-8"), 1):
            if line.lstrip().startswith("#"):
                section = set()
            elif "依据" in line and not line.lstrip().startswith("|"):
                section = cites_in(line)
            if not line.lstrip().startswith("|"):
                continue
            if "数值另有出处" in line:
                continue
            cites = cites_in(line) or section
            if not cites:
                continue
            body = re.sub(r"`[^`]*`", " ", STEM_RE.sub(" ", line))
            # 文号（教育部令第41号、校通知〔2008〕161号）不是正文数值
            body = re.sub(r"第?\s*\d+\s*号令", " ", body)
            body = re.sub(r"[〔\[［][^〕\]］]*[〕\]］]\s*\d*\s*号", " ", body)
            for num in sorted({n for n in re.findall(r"\d+(?:\.\d+)?", body)
                               if n not in NUM_DENY}):
                if not any(num in clause_text(
                        os.path.join(ROOT, "references", s + ".md"), {c})
                        for s, c in cites):
                    where = ",".join(f"{s}({len([1 for st, _ in cites if st == s])}条)"
                                     for s in sorted({s for s, _ in cites}))
                    print(f"[引用内容] {r}:{lineno}: 数值 {num} 未出现在所引条款 "
                          f"{where} 中——依据列漏列条款或数值有误")
                    bad += 1
    return bad

def cites_in(text):
    """从一段文字里取出 (规章文件, 条号) 引用集合。

    每个文件名只认它自己到下一个文件名之间的那段文字，避免把后一个规章的
    条号算到前一个头上；该段没有指明条号时，取该文件全部条号兜底。
    """
    cites = set()
    hits = list(STEM_RE.finditer(text))
    for i, m in enumerate(hits):
        stem = m.group(1)
        if stem in NO_ARTICLE_FILES or stem not in REF_STEMS:
            continue
        end = hits[i + 1].start() if i + 1 < len(hits) else len(text)
        nums = expand_clauses(text[m.end():end])
        for n in (nums or REF_STEMS[stem]):
            cites.add((stem, n))
    return cites

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
                    known_bad.update(re.findall(URL_RE, line))
    urls = set()
    for pat in ("sources.md", "README.md", "SKILL.md",
                "references/49-fuwu-zhinan.md", "data/*.md"):
        for f in glob.glob(os.path.join(ROOT, pat)):
            urls.update(re.findall(URL_RE, open(f, encoding="utf-8").read()))
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

def check_pack():
    sys.path.insert(0, os.path.join(ROOT, "tools"))
    import make_pack
    pack = os.path.join(ROOT, "pack", "seu-handbook.md")
    if not os.path.exists(pack):
        print("[知识包] pack/seu-handbook.md 不存在，请运行 python3 tools/make_pack.py")
        return 1
    if open(pack, encoding="utf-8").read() != make_pack.build()[0]:
        print("[知识包] pack/seu-handbook.md 与源文件不同步，请重新运行 python3 tools/make_pack.py")
        return 1
    return 0


def check_coverage():
    """统计 tests/golden-qa.md 的规章覆盖。只数表格行里的 NN-短名。

    散文里出现的规章名（如"零覆盖清单"）不计入，否则统计自我循环。
    这是信息项，不计入退出码。
    """
    txt = open(os.path.join(ROOT, "tests/golden-qa.md"), encoding="utf-8").read()
    cited = set(STEM_RE.findall("\n".join(
        l for l in txt.splitlines() if l.lstrip().startswith("|"))))
    school = {os.path.basename(p)[:-3] for p in
              glob.glob(os.path.join(ROOT, "references/[0-9][0-9]-*.md"))
              if not os.path.basename(p).startswith("00-")}
    missing = sorted(school - cited)
    extra = sorted(cited - school)
    print(f"[覆盖] 48 个校级规章中 golden-qa 引用 {len(school) - len(missing)} 个，"
          f"零覆盖 {len(missing)} 个：{'、'.join(missing) or '无'}")
    if extra:
        print(f"[覆盖] golden-qa 引用了不存在的规章文件：{'、'.join(extra)}")
        return 1
    return 0


def main():
    skip_net = "--skip-net" in sys.argv
    only_cov = "--cov" in sys.argv
    if only_cov:
        return check_coverage()
    results = {"条号连续性": check_articles(),
               "末条完整性": check_tail_article(),
               "路径解析": check_paths(),
               "引用有效性": check_citations(),
               "引用内容一致": check_citation_content(),
               "知识包同步": check_pack()}
    if not skip_net:
        results["URL 活性"] = check_urls()
    if "--with-cov" in sys.argv:
        results["金标准覆盖"] = check_coverage()
    for k, v in results.items():
        print(f"{'✗' if v else '✓'} {k}: {v} 个问题")
    return 1 if any(results.values()) else 0

if __name__ == "__main__":
    sys.exit(main())
