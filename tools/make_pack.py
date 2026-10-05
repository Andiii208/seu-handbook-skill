#!/usr/bin/env python3
"""生成单文件知识包 pack/seu-handbook.md（供网页/App 类 Agent 上传使用）。

内容 = SKILL.md（回答规范）+ references/00-index.md（检索索引）
       + data/*.md（9 张数值速查表）+ sources.md（官方渠道清单）。
references/ 下 52 个规章条文原文不进包：体积大且只在一部分问题中用到，
需要时由 Agent 按文件联网到仓库 references/ 调取。

用法：python3 tools/make_pack.py
发布前由 tools/check.py 校验包内文件与源同步（不一致时 check 会红）。
"""
import os
import glob
import datetime

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "pack", "seu-handbook.md")

PARTS = [
    ("SKILL.md", "Skill 回答规范"),
    ("references/00-index.md", "检索索引与路由"),
    ("sources.md", "官方渠道清单"),
] + [(p, "数值速查表 · " + os.path.basename(p)[:-3])
     for p in sorted(glob.glob(os.path.join(ROOT, "data/*.md")))]

HEADER = """# 东南大学大学生手册 · Skill 知识包（单文件版）

> 本文件由 `tools/make_pack.py` 自动生成，请勿手工编辑。
> 版本：内容截至 2025 年 8 月版《东南大学大学生手册》（整理汇编，非官方发布）。
>
> **怎么用**：把本文件上传给支持文件的 Agent，然后直接提问，例如
> “我绩点 3.2，能评三好学生吗？”“5 人团队省级 SRTP 结题良好能加多少研学分？”
> Agent 应按下方“Skill 回答规范”作答并引用条款。
>
> **内容边界**：本包含回答规范、检索索引、9 张数值速查表、官方渠道清单；
> 52 个规章的条文原文不在包内。需要条文原文时，请让 Agent 联网到
> GitHub 仓库 `Andiii208/seu-handbook-skill` 的 `references/` 目录，
> 按下方索引中的文件名（如 `14-xuefenzhi.md`）调取对应文件。

"""


def _strip_frontmatter(text):
    """去掉 YAML frontmatter（pack 面向网页 Agent，frontmatter 无用）。"""
    if text.startswith("---"):
        end = text.find("\n---", 3)
        if end != -1:
            return text[end + 4:].lstrip("\n")
    return text


def build():
    parts = [HEADER]
    for path, label in PARTS:
        body = _strip_frontmatter(open(os.path.join(ROOT, path),
                                       encoding="utf-8").read().strip())
        parts.append(f"\n\n<!-- ===== {path} · {label} ===== -->\n\n{body}\n")
    return "".join(parts), PARTS


def main():
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    content, parts = build()
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"已生成 {os.path.relpath(OUT, ROOT)}（{len(content.encode('utf-8'))/1024:.0f}KB，"
          f"{len(parts)} 个文件拼接）")


if __name__ == "__main__":
    main()
