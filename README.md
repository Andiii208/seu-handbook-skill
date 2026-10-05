# seu-handbook-skill

把《东南大学大学生手册》变成一个可以装进本地 Agent 的 Skill：不用翻书、不用问同学，直接问 Agent"这事按规定怎么办"，答案带**条款引用**。

- 内容来源：2025 年《东南大学大学生手册》（东南大学校长办公室编，2025 年 8 月）
- 覆盖范围：48 个校级规章全文 +《普通高等学校学生管理规定》（教育部令第 41 号）+ 服务指南（部门电话/网址）+ 10 张高频数值速查表
- 性质：**学生自发的整理汇编，非官方发布**。条文权利归东南大学；执行以学校正式文件和当年通知为准

## 这个 Skill 能回答什么

| 类型 | 例子 |
|---|---|
| 查规定 | "一学期旷课多少学时会开除学籍？""宿舍门禁几点关门？""对处分不服多久内申诉？" |
| 算分值 | "5 人团队 SRTP 省级良好加多少研学分？""省二竞赛（C 类）加几分？""3 人合作发 SCI 第一作者拿多少？" |
| 判资格 | "绩点 3.0 能评三好吗？""排 15% 能报国奖吗？""转过一次专业还能再转吗？" |
| 办事情 | "办休学找谁、带什么表？""勤工助学多少钱一小时？""交流学分什么时候申请认定？" |
| 找渠道 | "图书馆电话多少？""竞赛目录在哪查？""今年推免名额多少？"（只有手册没写的，都会引导到官方渠道，不编造） |

## 安装

本 Skill 采用通用的 Agent Skill 目录结构（`SKILL.md` + 资源目录），可被主流本地 Agent 加载。

**方式一：克隆到 Agent 的 skills 目录**

```bash
# Claude Code
git clone https://github.com/Andiii208/seu-handbook-skill.git ~/.claude/skills/seu-handbook

# ZCode（用户级）
git clone https://github.com/Andiii208/seu-handbook-skill.git ~/.zcode/skills/seu-handbook

# 其他 Agent：放入其 skills 目录即可；找不到目录时可把整个文件夹放进项目，让 Agent 读 SKILL.md
```

**方式二：放在项目里**

```bash
git clone https://github.com/Andiii208/seu-handbook-skill.git ./.seu-handbook-skill
```

然后在对话里让 Agent"读取 `./.seu-handbook-skill/SKILL.md` 并按其指引回答"。

安装后在支持自动触发（description 匹配）的 Agent 中，直接提问即可；不支持的 Agent，说一句"用 seu-handbook skill"或让它先读 SKILL.md。

## 使用示例

```
问：我 5 个人组队做了个省级 SRTP 项目，结题是"良好"，能加多少研学分？
答：项目总分值 = 基本分 + 附加分。基本分（良好、≥3 人）= 6+0.5×(5−3) = 7 分；
    附加分（省级、≥3 人）= 4+1.0×(5−3) = 6 分；合计 13 分。
    依据：《东南大学本科生课外研学成绩认定办法》第四条（手册 088 页）。
    注意：校级途径累计不超过 4 分；本办法自 2025 级开始执行。
    以上依据为 2025 版《东南大学大学生手册》，具体执行以学校和主管部门当年文件为准。
```

## 目录结构

```
├── SKILL.md               # Skill 入口：触发描述、检索路由、回答规范
├── references/            # 手册全文（按规章拆分，51 个文件）
│   ├── 00-index.md        #   总索引：快速路由表 + 规章索引 + 交叉引用簇
│   ├── 01-xueji.md …      #   48 个校级规章（含 frontmatter：页码/执行年级/引用关系）
│   ├── appendix-moe-41.md #   教育部令第 41 号
│   ├── 49-fuwu-zhinan.md  #   服务指南（部门电话/网址）
│   └── 00-front-school-intro.md
├── data/                  # 高频数值速查表（10 张）
│   ├── gpa-table.md  research-scores.md  social-practice.md  competitions.md
│   ├── scholarships.md  honors.md  discipline.md  academic-progress.md
│   └── dorm-and-life.md
├── sources.md             # 官方信息源清单（"当年才变"的信息去哪儿查）
├── tools/                 # 维护者用：OCR 与年度再生产线
└── tests/golden-qa.md     # 验收用金标准题
```

## 可靠性说明

- 手册原版为无文字层图片 PDF，本仓库文本由 OCR（macOS Vision，离线）识别后逐篇清洗，**所有数值表与渲染图逐值人工核对**（清单见 `tools/verify-checklist.md`）。
- 每个规章文件头部记录了手册页码、执行年级、解释单位，便于回溯原书。
- 回答规范强制"引用条款 + 找不到就说找不到 + 动态信息给官方渠道"，降低 Agent 编造风险。
- 仍可能有错漏：发现错误请提 Issue（见 CONTRIBUTING），我们会核对原书后修订。

## 版权与免责

- 规章文本整理自东南大学印发的《大学生手册》，权利归东南大学及原作者；本仓库仅作学习、检索、引用之用的整理汇编，不用于商业传播。
- 本仓库非官方发布，不代表学校立场；一切规定以学校正式文件、当年通知和各学院细则为准。

## 许可

- 代码与工具：MIT
- 手册派生文本：[CC BY-NC-SA 4.0](https://creativecommons.org/licenses/by-nc-sa/4.0/deed.zh)（署名—非商业性使用—相同方式共享）

## 参与

勘误、补充、新版本跟进见 [CONTRIBUTING.md](CONTRIBUTING.md)。欢迎各学院同学补充学院细则等手册外信息的**索引**（注意版权，只放链接与摘要）。
