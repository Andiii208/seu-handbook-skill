# 年度更新手册再生产线

学校每年 8—9 月印发新版《大学生手册》，本仓库内容需跟随更新。全流程约半天的机器时间 + 一天的清洗核对时间。以下命令以 macOS 为例（OCR 使用系统自带 Vision 框架，无需安装第三方依赖、离线可用）。

## 0. 准备

**先解决 PDF 来源**：教务处网站不发布《大学生手册》电子版（下载专区各栏目、信息通知均无；搜索引擎能搜到的"手册 PDF"都是学院网站转载的 2017—2019 旧版，不能当现行版用）。新版每年 8—9 月由校长办公室编印、纸质随新生发放，本仓库 2025 版建库 PDF 即来自同学分享。拿不到新版 PDF 时的路径，按优先级：

1. 社区投稿：持新版 PDF 的同学按 `CONTRIBUTING.md` 的 issue 模板提交（本项目 2026-10 起的正式方向）；
2. 教务处学籍管理科 025-52090227（号码见 `references/49-fuwu-zhinan.md`），询问当年版是否对外提供电子版；
3. 分主题增量更新：到教务处"管理规定"栏目（jwc.seu.edu.cn/glgd/list.htm，含教务管理/学籍管理/毕业设计等子栏目）抓当年单项规章，先更新对应 `references/*.md`，并在版本声明中注明"手册未更新、单项规章已更新"。

```bash
mkdir -p ~/seu-hb && cd ~/seu-hb
HB="/path/to/新版大学生手册.pdf"     # 来源见上；2025 版建库 PDF 源自同学分享
mkdir -p pages && pdftoppm -png -r 150 "$HB" pages/pg    # 渲染 150dpi
pdfinfo "$HB"                                              # 确认页数与版式是否变化
```

**先检查版式**：本仓库按“每个 PDF 页 = 手册两个页码横展（左栏偶数手册页、右栏奇数手册页）”处理。
若新版版式变化（单栏、页面尺寸变化、栏宽比变化），需修改 `ocr.swift` 的分栏阈值（`x < 0.5`）和 `split_chunks.py` 的 `DOCS` 页码表。

## 1. OCR

```bash
swiftc -O ocr.swift -o ocr            # 首次编译；macOS 需要 Xcode CLT
# 三批并行跑（glob 注意别跨批重叠）：
./ocr pages/pg-0*.png          > v2_00_09.txt 2>&1 &   # 视实际页数调整
./ocr pages/pg-0[1-5]*.png     > v2_10_59.txt 2>&1 &
./ocr pages/pg-0[6-9]*.png pages/pg-1*.png > v2_60_114.txt 2>&1 &
wait
```

注意：`split_chunks.py` 的读页逻辑是“同页先到先得”，批次 glob 重叠不会重复收录，但建议仍按不重叠划分。

## 2. 切块

```bash
python3 tools/split_chunks.py     # 产出 v2/pages/pg-NNN.txt 与 v2/chunks/<docid>.txt
```

按新版目录修订 `split_chunks.py` 里的 `DOCS` 表（docid、起止 PDF 页、手册页码——新版目录页在 PDF 前两页）。

## 3. 清洗与结构化

按 `tools/cleaning-spec.md` 逐篇清洗成 `references/*.md`。新增/删去的规章同步更新：
- `references/00-index.md`（索引与路由表、交叉引用簇）
- `SKILL.md`（描述词、路由、示例，若结构有变）
- `data/*.md`（所有数值表，逐值与渲染图核对）
- `sources.md`（链接有效性）

## 4. 验收

```bash
# 0. 机械质检（必须全绿）：条号连续性、相对路径解析、data→references 引用、URL 活性
python3 tools/check.py            # 有网络；离线环境加 --skip-net

# 1. 人工跑 tests/golden-qa.md 抽样题目（按发布后的目录结构，而非仓库外副本），通过后记录到回归表
```

修订内容引用格式抽查：任取 10 条，`rg "第.条" references/` 与渲染图比对。

## 5. 版本与发布

- 更新 `SKILL.md` 无版本字段；在 `README.md` 注明手册版本与整理日期。
- 提交信息示例：`docs: 更新至 2026 版手册（2026-08）`。
- 涉及表值变化时，在 release notes 列出变化点，方便用户核对。

## 已知 OCR 现象（2025 版实测）

- 个别页（约卷首页与部分表格页）Vision 会重复输出同一文本块，`split_chunks.py` 的 `clean()` 已处理；若新版仍有残留，检查页脚是否夹在重复块之间。
- 高频误字：竟→竞、韵→的、钓→的、人学→入学、惠有→患有、准子→准予、修谈→修读、上还→上述、域写→填写、体育课罗马数字（口/皿/罒/山→I/II/III/IV/V）。
- 表格是重灾区：**所有数值表必须与渲染图逐值核对**（这是本仓库的质量底线）。
- 部分正文有 OCR 整句丢失（如 17-bishe 第十条（三）、appendix 第五十七条、47-shiyanshi 第十五条），需对照渲染图补全。
