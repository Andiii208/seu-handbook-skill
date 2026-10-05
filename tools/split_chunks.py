#!/usr/bin/env python3
"""Split column-ordered OCR output into per-page files, dedupe Vision repeats,
and slice the handbook into per-regulation text chunks for the cleaning pass.

Input : （工作目录，按实际修改）/v2_*.txt  (files produced by ocr2, "=== pg-NNN.png ===" delimited)
Output: （工作目录，按实际修改）/v2/pages/pg-NNN.txt   deduped per-page text
        （工作目录，按实际修改）/v2/chunks/<docid>.txt  per-regulation raw chunk (noise kept)
"""
import os, re, sys

SRC = ["v2_00_09.txt", "v2_10_59.txt", "v2_60_114.txt"]  # OCR 批次输出
OUT_PAGES = "v2/pages"
OUT_CHUNKS = "v2/chunks"

FOOTER = re.compile(r"^[\s—=＝\-–三川★:：·.]*\d{1,3}[\s—=＝\-–三川★:：·.]*$")

def is_footer(line: str) -> bool:
    s = line.strip()
    if not s or len(s) > 14:
        return False
    return bool(FOOTER.match(s))

def read_pages():
    pages = {}
    for f in SRC:
        cur = None
        for line in open(f, encoding="utf-8"):
            m = re.match(r"^=== pg-(\d+)\.png ===$", line.strip())
            if m:
                n = int(m.group(1))
                if n not in pages:
                    pages[n] = []
                    cur = pages[n]
                else:
                    cur = None  # already captured from an earlier batch
            elif cur is not None:
                cur.append(line.rstrip("\n"))
    return pages

def clean(lines):
    """Strip page footers, then remove Vision's duplicated blocks."""
    lines = [l for l in lines if not is_footer(l)]
    # remove adjacent duplicate blocks (k>=2 consecutive lines repeated right after)
    i = 0
    out = []
    n = len(lines)
    while i < n:
        dropped = False
        for k in range(2, 14):
            if i + 2 * k <= n and lines[i:i+k] == lines[i+k:i+2*k] and any(l.strip() for l in lines[i:i+k]):
                i += k  # skip the duplicated copy, keep one
                dropped = True
                break
        if not dropped:
            out.append(lines[i])
            i += 1
    # collapse >1 consecutive blank lines
    res, blank = [], 0
    for l in out:
        if not l.strip():
            blank += 1
            if blank <= 1:
                res.append(l)
        else:
            blank = 0
            res.append(l)
    return res

# page ranges per regulation: (docid, start_page, end_page, first_line_marker, last_line_marker)
# markers are matched against the joined page text; slice is inclusive.
DOCS = [
    ("00-front-school-intro", 4, 5, None, None),
    ("a-divider", 8, 8, None, None),
    ("01-xueji", 9, 13, None, None),
    ("02-gang-aotai", 14, 15, "学籍管理补充规定", "解释"),
    ("03-minzu", 15, 16, "学籍管理规定", "解释"),
    ("04-tiyu-yundongyuan", 16, 18, "学籍管理规定", "解释"),
    ("05-xuewei", 18, 20, "学士学位授予实施办法", "解释"),
    ("06-fuxiu", 20, 22, "辅修专业", "解释"),
    ("07-zhuanzhuanye", 22, 24, "转专业工作实施办法", "解释"),
    ("08-zhuanxue", 24, 25, "转学管理办法", "解释"),
    ("09-fenliu", 26, 27, "分流工作实施办法", "解释"),
    ("10-tuimian", 27, 29, "免试攻读研究生工作实施办法", "解释"),
    ("11-yanchang", 29, 29, "延长学习年限实施办法", "解释"),
    ("12-youxiusheng", 30, 32, "学习优秀生选拔", "解释"),
    ("13-qiangji", 33, 33, "强基计划学生管理", "解释"),
    ("14-xuefenzhi", 34, 37, "学分制管理办法", "解释"),
    ("15-kaoshi", 37, 38, "考试管理办法", "解释"),
    ("16-tiyu", 39, 39, "体育教学及考核规则", "解释"),
    ("17-bishe", 40, 44, "毕业设计（论文）管理办法", "解释"),
    ("18-zhuoyue", 45, 48, "卓越工程师", "解释"),
    ("19-gongpai", 49, 50, "公派交流学习管理办法", "解释"),
    ("20-xuefen-rending", 51, 52, "课程学分认定管理办法", "解释"),
    ("21-yanxue", 52, 55, "课外研学成绩认定办法", "解释"),
    ("22-shehui-shijian", 56, 58, "社会实践课程学分认定办法", "解释"),
    ("23-jingsai", 58, 59, "学科竞赛管理办法", "解释"),
    ("b-divider", 60, 60, None, None),
    ("24-jiangli", 61, 62, None, None),
    ("25-guojiang", 63, 64, None, None),
    ("26-lizhi", 65, 65, None, None),
    ("27-xiaozhangjiang", 66, 66, None, None),
    ("28-youbi", 67, 67, None, None),
    ("29-xianjin-banji", 68, 68, None, None),
    ("30-sanhao", 69, 69, None, None),
    ("31-zizhu", 70, 71, None, None),
    ("32-kunnan-rending", 72, 73, None, None),
    ("33-zhuxuejin", 74, 75, None, None),
    ("34-qingong", 75, 77, None, None),
    ("35-daikuan", 78, 79, None, None),
    ("36-ruwu", 80, 81, None, None),
    ("37-weiji-chufen", 81, 84, None, None),
    ("38-shensu", 85, 85, None, None),
    ("39-huixiao-kaoshi", 86, 86, None, None),
    ("40-zhengjian", 86, 86, None, None),
    ("41-gongyu", 87, 91, None, None),
    ("42-tushuguan", 92, 92, None, None),
    ("43-chubanwu", 93, 94, None, None),
    ("44-wangluo", 94, 95, None, None),
    ("45-shoufei", 96, 98, None, None),
    ("46-pingjiao", 98, 98, None, None),
    ("47-shiyanshi", 99, 100, None, None),
    ("48-chuguo", 101, 102, None, None),
    ("appendix-moe-41", 103, 110, None, None),
    ("49-fuwu-zhinan", 111, 112, None, None),
]

def main():
    pages = read_pages()
    missing = [n for n in range(1, 115) if n not in pages]
    if missing:
        print("MISSING PAGES:", missing)
        sys.exit(1)
    os.makedirs(OUT_PAGES, exist_ok=True)
    os.makedirs(OUT_CHUNKS, exist_ok=True)
    for n in sorted(pages):
        lines = clean(pages[n])
        with open(f"{OUT_PAGES}/pg-{n:03d}.txt", "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    for docid, p0, p1, m0, m1 in DOCS:
        buf = []
        for n in range(p0, p1 + 1):
            buf.append(f"----- PDF page {n} -----")
            buf.append(open(f"{OUT_PAGES}/pg-{n:03d}.txt", encoding="utf-8").read().rstrip())
        text = "\n".join(buf)
        with open(f"{OUT_CHUNKS}/{docid}.txt", "w", encoding="utf-8") as fh:
            fh.write(text + "\n")
    print("pages:", len(pages), "chunks:", len(DOCS))

if __name__ == "__main__":
    main()
