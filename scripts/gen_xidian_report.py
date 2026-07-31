# -*- coding: utf-8 -*-
"""生成"西电盛敏团队（含刘俊宇）研究方向与潜力分析"Word 报告。

数据来源：西电官网/教师主页、Google Scholar、IEEE Xplore、arXiv、Engineering 院刊等公开信息，
检索日期 2026-07-30。生成后输出到桌面。
"""
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn
from docx.oxml import OxmlElement

CN_FONT = "微软雅黑"
EN_FONT = "Times New Roman"
ACCENT = RGBColor(0x1F, 0x4E, 0x79)


def set_run(run, size=10.5, bold=False, color=None, cn=CN_FONT, en=EN_FONT):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = en
    run._element.rPr.rFonts.set(qn("w:eastAsia"), cn)
    if color is not None:
        run.font.color.rgb = color
    return run


def add_para(doc, text, size=10.5, bold=False, color=None, align=None,
             space_after=6, space_before=0, indent=0, style=None):
    p = doc.add_paragraph(style=style)
    if align is not None:
        p.alignment = align
    pf = p.paragraph_format
    pf.space_after = Pt(space_after)
    pf.space_before = Pt(space_before)
    pf.line_spacing = 1.25
    if indent:
        pf.left_indent = Cm(indent)
    set_run(p.add_run(text), size=size, bold=bold, color=color)
    return p


def add_heading(doc, text, level=1):
    sizes = {1: 15, 2: 12.5, 3: 11}
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.space_before = Pt(14 if level == 1 else 10)
    pf.space_after = Pt(6)
    set_run(p.add_run(text), size=sizes[level], bold=True, color=ACCENT)
    if level == 1:
        pbdr = OxmlElement("w:pBdr")
        bottom = OxmlElement("w:bottom")
        bottom.set(qn("w:val"), "single")
        bottom.set(qn("w:sz"), "8")
        bottom.set(qn("w:color"), "1F4E79")
        pbdr.append(bottom)
        p._p.get_or_add_pPr().append(pbdr)
    return p


def add_bullet(doc, text, size=10.5, indent=0.4, bold_head=None):
    p = doc.add_paragraph()
    pf = p.paragraph_format
    pf.left_indent = Cm(indent + 0.4)
    pf.first_line_indent = Cm(-0.4)
    pf.space_after = Pt(3)
    pf.line_spacing = 1.25
    set_run(p.add_run("• "), size=size)
    if bold_head:
        set_run(p.add_run(bold_head), size=size, bold=True)
    set_run(p.add_run(text), size=size)
    return p


def add_table(doc, headers, rows, widths=None, size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    hdr = t.rows[0].cells
    for i, h in enumerate(headers):
        hdr[i].text = ""
        p = hdr[i].paragraphs[0]
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.paragraph_format.space_after = Pt(2)
        set_run(p.add_run(h), size=size, bold=True)
        shd = OxmlElement("w:shd")
        shd.set(qn("w:fill"), "DCE6F1")
        hdr[i]._tc.get_or_add_tcPr().append(shd)
    for row in rows:
        cells = t.add_row().cells
        for i, val in enumerate(row):
            cells[i].text = ""
            p = cells[i].paragraphs[0]
            p.paragraph_format.space_after = Pt(2)
            p.paragraph_format.line_spacing = 1.1
            set_run(p.add_run(str(val)), size=size)
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    doc.add_paragraph().paragraph_format.space_after = Pt(2)
    return t


doc = Document()
sec = doc.sections[0]
sec.left_margin = sec.right_margin = Cm(2.4)
sec.top_margin = sec.bottom_margin = Cm(2.2)
normal = doc.styles["Normal"]
normal.font.name = EN_FONT
normal.font.size = Pt(10.5)
normal.element.rPr.rFonts.set(qn("w:eastAsia"), CN_FONT)

# ============ 封面 ============
add_para(doc, "西安电子科技大学 通信工程学院", size=13, bold=True,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_before=48, space_after=4)
add_para(doc, "盛敏团队（含刘俊宇老师）研究方向与发展潜力分析",
         size=20, bold=True, color=ACCENT, align=WD_ALIGN_PARAGRAPH.CENTER, space_after=10)
add_para(doc, "—— 聚焦 2023–2026 年近三年成果 ——", size=11.5,
         align=WD_ALIGN_PARAGRAPH.CENTER, space_after=36)

add_table(doc, ["项目", "内容"], [
    ["报告主题", "团队构成、近三年研究方向图谱、代表性期刊/会议成果、潜力方向评估"],
    ["重点对象", "刘俊宇（副教授、博导）；团队负责人 李建东、盛敏"],
    ["依托平台", "空天地一体化综合业务网全国重点实验室（原 ISN 国家重点实验室）"],
    ["资料检索日期", "2026 年 7 月 30 日"],
    ["资料来源", "西电官网及教师主页、Google Scholar、IEEE Xplore、arXiv、Engineering 院刊、IEEE ICC/GLOBECOM 会议官网等公开信息"],
], widths=[3.2, 12.4], size=10)

doc.add_page_break()

# ============ 摘要 ============
add_heading(doc, "摘要：三句话看懂这个团队")
add_bullet(doc, "这是国内做「卫星互联网 / 空天地一体化组网」最顶尖的团队之一。带头人盛敏是 IEEE Fellow、"
                "国家杰青、科技部 6G 总体专家组成员，现任空天地一体化综合业务网全国重点实验室主任；"
                "团队前身是 1962 年成立的无线通信研究室，研制了我国第一套多信道自组织分组无线网络。",
           bold_head="① 平台顶级：")
add_bullet(doc, "从 2023 到 2026 年，团队的产出重心已经明显从「地面 5G/超密集网络」全面转向"
                "「LEO 巨型星座 + 星上计算 + 低空经济」三大战场，2026 年更是密集出现"
                "星上大模型推理（SpaceMoE）、星座抗毁拓扑（IEEE TMC/TCOM）等新方向。",
           bold_head="② 方向在转：")
add_bullet(doc, "刘俊宇老师是盛敏 2016 年毕业的博士，现为副教授、博导，个人主线非常清晰——"
                "「网络容量理论 + 节点/链路失效鲁棒性 + 空地/低空网络」，2026 年在 IEEE TCOM 上"
                "发表了低空异构网络可用性管理的工作，正好踩在低空经济的风口上。",
           bold_head="③ 刘老师定位：")

# ============ 一、团队概览 ============
add_heading(doc, "一、团队概览")

add_heading(doc, "1.1 团队基本情况", 2)
add_table(doc, ["条目", "内容"], [
    ["团队名称", "智能宽带无线通信网络团队（前身：通信工程学院无线通信研究室，成立于 1962 年）"],
    ["负责人", "李建东 教授、盛敏 教授"],
    ["核心成员", "李建东、盛敏、史琰、刘俊宇、文娟、白卫岗、周笛、郑阳"],
    ["依托平台", "空天地一体化综合业务网全国重点实验室（2022 年由原 ISN 国家重点实验室重组，科技部批准建设）"],
    ["团队称号", "科技部「智能无线通信系统」重点领域创新团队；教育部「宽带无线通信」创新团队；"
                "陕西省「超高密度异构自组织宽带无线通信网络」重点科技创新团队"],
    ["历史成果", "国家技术发明二等奖 2 项、省部级一等奖 4 项、国防科技奖励 5 项；"
                "研制我国第一套多信道自组织分组无线网络"],
    ["近期荣誉", "2024 年获中国电子学会科技进步一等奖；实验室通感算融合团队成果获 IEEE ICC 2026 最佳论文奖"],
], widths=[2.8, 12.8], size=9.5)

add_heading(doc, "1.2 两位关键人物", 2)

add_para(doc, "盛敏 教授（团队学术带头人 / 刘俊宇的博导）", size=11, bold=True, space_before=6, space_after=4)
add_table(doc, ["条目", "内容"], [
    ["学历经历", "1997/2000/2004 年于西电分别获学士（计算机通信）、硕士、博士（通信与信息系统）学位；"
                "2000 年留校，2007 年破格晋升教授，2008 年博导；2015 年多伦多大学高级访问学者"],
    ["现任职务", "空天地一体化综合业务网全国重点实验室主任；科技部 6G 总体专家组成员；"
                "IEEE 西安分会副主席；IEEE Fellow；中国电子学会会士"],
    ["主要荣誉", "国家杰出青年科学基金（2017）；教育部新世纪优秀人才（2006）；霍英东青年教师奖（2008）；"
                "陕西省三秦学者（2010）；全国三八红旗手；2020–2022 连续入选爱思唯尔中国高被引学者；"
                "2021 年入选全球前 2% 顶尖科学家榜单"],
    ["学术影响力", "Google Scholar 引用约 13,700 次，h 指数 57，i10 指数 212（2026-07 检索）"],
    ["期刊任职", "IEEE Wireless Communications、China Communications 等多个期刊编委"],
    ["联系方式", "msheng@mail.xidian.edu.cn；科技楼 A611"],
], widths=[2.8, 12.8], size=9.5)

add_para(doc, "刘俊宇 副教授（本次重点关注对象）", size=11, bold=True, space_before=8, space_after=4)
add_table(doc, ["条目", "内容"], [
    ["学历经历", "2016 年于西电获通信与信息系统专业工学博士学位（导师：盛敏教授），同年 12 月留校任教"],
    ["现任职务", "通信工程学院副教授、博士生导师；空天地一体化综合业务网全国重点实验室成员；"
                "陕西省通信学会《智能通信组网与抗干扰技术专业委员会》秘书"],
    ["研究方向", "① 异构密集无线网络容量理论及组网技术；② 天地一体化网络智能组网技术；③ 室内定位技术"],
    ["成果规模", "发表论文 60 余篇，申请/授权国家发明专利 30 余项"],
    ["人才称号", "第五届中国科协青年人才托举工程；陕西省青年科技新星；陕西省高校科协青年人才托举计划"],
    ["主要奖励", "中国通信学会优秀博士论文；陕西省优秀博士论文；省部级科学技术奖励 4 项"],
    ["教学荣誉", "2020 创共体杯前沿科技创新大赛「先进通信+」全国一等奖；指导互联网+大赛陕西省金奖 3 项、"
                "银奖 3 项；「西电优秀创新创业导师」「通信工程学院研究生最喜欢的老师」"],
    ["联系方式", "junyuliu@xidian.edu.cn；北校区老科技楼 A616"],
], widths=[2.8, 12.8], size=9.5)

add_para(doc, "补充：周笛 副教授（团队骨干，巨型星座资源管控方向）——2019 年西电博士（导师盛敏），"
              "主攻天地一体化巨型星座系统架构与资源管理、网络性能评估、空间信息网络任务规划，"
              "近五年发表 IEEE 期刊/会议论文 50 余篇，是「星座拓扑与容量」这条主线上的高产核心作者。",
         size=10, space_before=6)

doc.add_page_break()

# ============ 二、方向图谱 ============
add_heading(doc, "二、近三年（2023–2026）研究方向图谱")
add_para(doc, "以下按「研究主线」归类，每条主线给出代表性成果。判断依据是团队成员 Google Scholar "
              "按发表时间倒序的完整论文列表，以及 IEEE ICC/GLOBECOM 官方程序册。"
              "越靠前的主线，近两年投入的力量越大。", size=10, space_after=8)

# 主线 A
add_heading(doc, "主线 A｜LEO 巨型星座容量理论与抗毁拓扑设计 ★团队招牌", 2)
add_para(doc, "通俗解释：星链、千帆这类由成千上万颗卫星组成的「巨型星座」，卫星之间靠激光链路连成一张网。"
              "这张网到底最多能传多少数据？卫星坏了、链路断了会怎样？怎么设计拓扑才最抗打？"
              "团队用随机几何、图论、渗流理论把这些问题做成了一套数学理论体系——这是别人短期内抢不走的护城河。",
         size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "Capacity Analysis and Robust Topology Design of LEO Satellite Constellation with Node/Link Failure", "IEEE Trans. Communications"],
    ["2026", "Anti-Vulnerability Topology Design of LEO Satellite Networks With Node/Link Failure", "IEEE Trans. Mobile Computing"],
    ["2026", "The Capacity of LEO Satellite Constellations with Link Failures", "IEEE Trans. Communications"],
    ["2026", "Optimal Zone Routing Scheme for LEO Mega-Constellation Networks", "IEEE Trans. Mobile Computing"],
    ["2026", "Capacity Limits of LEO Satellite Constellations with Link Failures", "IEEE ICC 2026"],
    ["2026", "On Capacity and Delay of Wireless Networks with Node Failures", "arXiv 预印本"],
    ["2025", "Capacity Analysis of LEO Mega-Constellations With Quasi-Torus Topologies", "IEEE Trans. Communications"],
    ["2025", "Hierarchically Dynamic Planning of Inter-Layer Connections", "IEEE Trans. Wireless Communications"],
    ["2024", "Constellation Topology Design for Maximum Capacity of LEO Satellite Networks", "IEEE Trans. Communications"],
    ["2024", "Robust Throughput Capacity of Multi-Connectivity Wireless Networks", "IEEE Trans. Communications"],
    ["2024", "Inter-Satellite Link Planning for High Capacity in LEO Mega-Constellations", "IEEE ICC 2024"],
    ["2024", "Tiered Clustering-Based Management Architecture in Mega-Satellite Networks", "Science China Info. Sciences"],
    ["2023", "The Capacity of k-Connectivity d-Dimensional Wireless Networks with Node Failure", "Science China Info. Sciences"],
], widths=[1.3, 9.5, 4.8])
add_para(doc, "关键结论示例：团队把存在链路失效的 LEO 星座建模为 Δ-随机正则图（Δ≥4 为每颗卫星的天线数，"
              "即最多可建立的星间链路数），推导出星座结构崩溃的临界失效概率 pc(Δ) = (Δ−2)/(Δ−1)。"
              "这类「一个公式说清工程边界」的结果，正是该团队的风格。", size=9.5, space_after=8)

# 主线 B
add_heading(doc, "主线 B｜空间环境效应与星座可靠性 ★交叉学科独家", 2)
add_para(doc, "通俗解释：太阳辐射、宇宙射线、空间碎片会让卫星芯片「单粒子翻转」（SEU）、让激光链路被太阳背景噪声淹没。"
              "团队把这些物理层面的空间环境效应，一直算到整网吞吐量下降多少——把航天物理和网络理论打通了，"
              "国内外做这个交叉的团队非常少。", size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2025", "Effects of Space Environment on Satellite Mega-Constellations: From Nodes and Links to Network Performance", "Engineering（中国工程院院刊）"],
    ["2025", "Mega Satellite Constellation Design Under Single-Event Upsets", "IEEE Trans. Communications"],
    ["2025", "High Throughput-Oriented Mega-Constellation Design with the Impact of Single-Event Upsets", "IEEE GLOBECOM 2025"],
    ["2025", "A Network-Level 3-Layer Single Event Upset Risk Assessment Model for Satellite Mega Constellations", "IEEE/CIC ICCC 2025"],
    ["2025", "Impact Analysis of Solar Background Noise on LEO Mega-Constellations", "IEEE ICC 2025"],
], widths=[1.3, 9.5, 4.8])
add_para(doc, "注：Engineering 是中国工程院院刊，2025 年第 54 卷设有「空间互联网组网」专题，周笛参与编辑，"
              "该篇由盛敏、周笛、纪思静、白卫岗、朱彦、刘俊宇、李建东合作完成——是团队近年分量最重的成果之一。",
         size=9.5, space_after=8)

# 主线 C
add_heading(doc, "主线 C｜星上智能计算 / 算网融合 ★最新爆发点", 2)
add_para(doc, "通俗解释：卫星在太空能不间断晒太阳发电，于是有人提出把数据中心和大模型搬到天上去。"
              "团队 2026 年推出 SpaceMoE，研究如何把一个超大 MoE（混合专家）大模型的不同「专家」"
              "拆开部署到不同卫星上协同推理。这条线 2026 年才刚开，还挂在 arXiv 上，说明是真正的新战场。",
         size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "SpaceMoE: Towards Orbital General Intelligence with Distributed Mixture-of-Experts Inference", "arXiv 预印本"],
    ["2026", "SpaceMoE: Realizing Distributed Mixture-of-Experts Inference over Space Networks", "arXiv 预印本"],
    ["2026", "Computing-Network Integrated Resource Scheduling in Satellite Mega-Constellations: A Hybrid Transfer and RL Framework", "IEEE ICC 2026"],
    ["2026", "Prediction-Driven Receding Horizon Scheduling for Joint Multi-Satellite Collaborative Computing", "IEEE Wireless Comm. Letters"],
    ["2026", "User Capacity of DRSNs with Integrated Storage, Computation and Communication", "IEEE Trans. Communications"],
    ["2025", "Satellite Computing Network Construction: Optimal Computing Node Deployment", "IEEE Trans. Communications"],
    ["2025", "Intelligent Collaborative Scheduling Enabled Communication-Computing Integration", "IEEE Trans. Communications"],
    ["2025", "Satellite Task Scheduling Strategy Optimization: From a 3C Resources Perspective", "IEEE GLOBECOM 2025"],
    ["2025", "SAGIN-4C-6G: A Space-Air-Ground Integrated Network for Enhanced Communication, Computation, Caching and Control in 6G", "IEEE WCNC 2025"],
    ["2024", "Space-Ground Fluid AI for 6G Edge Intelligence", "arXiv 预印本"],
], widths=[1.3, 9.5, 4.8])
add_para(doc, "重要信号：SpaceMoE 的合作者包括香港大学黄凯斌（Kaibin Huang）教授、"
              "香港科技大学 Khaled B. Letaief 教授（均为无线通信领域国际顶级学者）。"
              "这意味着团队在这个新方向上一开局就是顶配阵容，学生有机会接触国际合作。", size=9.5, space_after=8)

doc.add_page_break()

# 主线 D
add_heading(doc, "主线 D｜低空经济 / 空地一体化网络 ★政策风口，刘俊宇主战场", 2)
add_para(doc, "通俗解释：无人机送货、eVTOL 飞行汽车要普及，天上几百米高的空域就需要一张专门的通信网。"
              "这就是「数字低空」。实验室 2025 年 4 月在全球 6G 大会上牵头发布了全球首部"
              "《数字低空网络架构、覆盖及关键技术白皮书》，等于在这个领域拿到了标准话语权。",
         size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "Availability-Aware Resource Management in Low-Altitude Heterogeneous Networks", "IEEE Trans. Communications"],
    ["2026", "Sustainable Air-Ground Integrated Coverage Networks: ISCC Architecture, Technologies, and Testbed", "arXiv 预印本"],
    ["2026", "Transmissive RIS-Enabled Simultaneous Coverage for Aerial and Ground Users in Cellular Networks", "IEEE Trans. Wireless Communications"],
    ["2026", "Impact of UAV Mobility and Wobble on Temporal Correlation of Air-to-Ground Channels", "IEEE Trans. Vehicular Technology"],
    ["2026", "Energy-Efficient Network Deployment and Resource Allocation in IAB Aerial-Terrestrial Network", "China Communications"],
    ["2025", "Energy-Efficient Beamforming for Near-Field STAR-RIS-Enhanced Low-Altitude ISAC Networks", "IEEE Trans. Cognitive Comm. and Networking"],
    ["2025", "Coverage Enhancement in Dynamic Aerial-Terrestrial Integrated Networks", "IEEE Trans. Wireless Communications"],
    ["2025", "Dynamic Trajectory Optimization and Power Control for Hierarchical UAV Swarms in 6G Aerial Access Network", "IEEE Trans. Wireless Communications"],
    ["2024", "Enabling Integrated Access and Backhaul in Dynamic Aerial-Terrestrial Networks for Coverage Enhancement", "IEEE Trans. Wireless Communications"],
    ["2024", "Ground-to-Air Wireless Coverage Extension for 6G: A Triangular Prism Structure-Based Approach", "Science China Info. Sciences"],
    ["2024", "Enhancing Network Capacity with Transmission Range Optimization in UAV Ad Hoc Networks", "IEEE Trans. Communications"],
], widths=[1.3, 9.5, 4.8])
add_para(doc, "注意：本主线第一条 TCOM 2026 论文，正是刘俊宇老师个人主页论文列表中最新的一篇，"
              "把他一贯的「网络可用性/容量理论」方法论直接迁移到了低空场景——这是判断他未来 3–5 年主攻方向的最强信号。",
         size=9.5, space_after=8)

# 主线 E
add_heading(doc, "主线 E｜通感一体化（ISAC）与网络智能", 2)
add_para(doc, "通俗解释：让基站在通信的同时兼做雷达，一边传数据一边感知环境（测距、测速、成像）。"
              "这是 6G 的核心特征之一，也是 3GPP 标准的热点。", size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "Multi-User Covert ISAC over Rician Fading", "IEEE J. Selected Areas in Communications"],
    ["2026", "AirBreath Sensing: Protecting Over-the-Air Distributed Sensing Against Interference", "IEEE Trans. Wireless Communications"],
    ["2026", "Robust Edge Inference with Graph Neural Networks under Channel Aging", "IEEE ICC 2026"],
    ["2025", "Generative AI-Enabled Integrated Sensing and Communication", "IEEE Communications Magazine"],
    ["2025", "Generative-Adversarial-Network-Enhanced DRL for ISAC with Double Active RISs", "IEEE Internet of Things Journal"],
    ["2025", "KR-MAE: An Image-Driven Framework for Distribution-Aware Radio Map Reconstruction", "IEEE GLOBECOM 2025"],
    ["2024", "Resource Allocation for Adaptive Beam Alignment in UAV-Assisted ISAC Networks", "IEEE J. Selected Areas in Communications"],
    ["2024", "Low-Power Beamforming Design for Near-Field ISAC Networks", "IEEE Internet of Things Journal"],
], widths=[1.3, 9.5, 4.8])

# 主线 F
add_heading(doc, "主线 F｜应急抗毁通信（刘俊宇深度参与）", 2)
add_para(doc, "通俗解释：地震、洪水把基站打掉之后，怎么用无人机、多连接技术快速把通信恢复起来，"
              "并且保证时延和可靠性。团队把「容量可扩展性」这套理论用来量化网络的抗灾能力。", size=10, space_after=6)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "Availability of Aerial Heterogeneous Networks for Reliable Emergency Communications", "IEEE ICC 2026"],
    ["2025", "Towards Disaster-Resistant Cellular Communication Networks Based on Network Capacity Scalability", "IEEE Trans. Wireless Communications"],
    ["2025", "Towards Reliable Communications with Delay Requirement in Aerial Disaster Emergency Networks via CoMP", "IEEE Trans. Communications"],
    ["2025", "Enabling High-Reliable and Low-Latency Multipoint-to-Multipoint Broadcast for Emergency Wireless Network via Multi-Connectivity", "IEEE GLOBECOM 2025"],
    ["2024", "Enhancing Network Availability in Aerial Disaster Emergency Networks via Coordinated Multi-Point", "IEEE GLOBECOM 2024"],
    ["2024", "Delay-Aware UAV Computation Offloading and Communication Assistance for Post-Disaster Rescue", "IEEE Trans. Wireless Communications"],
], widths=[1.3, 9.5, 4.8])

# 主线 G
add_heading(doc, "主线 G｜通导遥一体化与高精度定位", 2)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "Toward High-Precision Positioning for Enhanced Long-Range Navigation Systems", "IEEE Wireless Communications"],
    ["2026", "Satellite Remote Sensing Mission Scheduling for Ecological Monitoring", "IEEE Trans. Aerospace and Electronic Systems"],
    ["2025", "Robust Distributed TOA-Based Localization for Multi-Hop MANET", "IEEE Trans. Vehicular Technology"],
    ["2025", "3C Resources Joint Allocation for Time-Deterministic Remote Sensing Image Backhaul", "arXiv 预印本"],
    ["2024", "Integrated Communication, Navigation, and Remote Sensing in LEO Networks", "IEEE Wireless Communications"],
    ["2024", "Deterministic Maximum Likelihood Algorithm for Sky-Ground Waves Recognition in eLoran Systems", "IEEE Trans. Vehicular Technology"],
], widths=[1.3, 9.5, 4.8])

# 主线 H
add_heading(doc, "主线 H｜地面网络 AI 资源管理（传统强项，投入正在收缩）", 2)
add_table(doc, ["年份", "成果标题", "发表载体"], [
    ["2026", "SOCP-Embedded DRL for Low-Energy Hybrid Beamforming in Cell-Free Massive MIMO with Imperfect CSI", "IEEE ICC 2026"],
    ["2025", "Two-Stage GNN-Based Scalable Access Mode Selection and Power Control for Cell-Free and D2D Networks", "IEEE Trans. Cognitive Comm. and Networking"],
    ["2025", "Generalization-Enhanced DRL-Based Resource Allocation in Wireless Networks with Dynamic User Loads", "IEEE Wireless Comm. Letters"],
    ["2025", "Collaborative Energy and Communication Resources Optimization for Improving Carbon Efficiency", "IEEE Trans. Wireless Communications"],
    ["2024", "A Survey of Graph-Based Resource Management in Wireless Networks — Part I / Part II", "IEEE Trans. Cognitive Comm. and Networking"],
], widths=[1.3, 9.5, 4.8])
add_para(doc, "说明：刘俊宇老师早年成名的「超密集网络干扰管理 / 容量标度率」方向（IEEE TWC 2018 等），"
              "2023 年之后基本不再有新产出，可以视为已完成的历史阶段，报考时不宜再以此为主攻点。",
         size=9.5, space_after=8)

doc.add_page_break()

# ============ 三、发表阵地 ============
add_heading(doc, "三、团队主要发表阵地")
add_para(doc, "从近三年成果看，团队的投稿目标高度集中在通信领域最权威的几本 IEEE 汇刊和两大旗舰会议，"
              "整体档次很高，几乎不投低水平刊物。", size=10, space_after=6)
add_table(doc, ["类别", "主要阵地", "说明"], [
    ["顶级期刊（Trans.）", "IEEE TCOM、IEEE TWC、IEEE TMC、IEEE TVT、IEEE TCCN、IEEE TAES",
     "TCOM 和 TWC 是绝对主力，近三年数量最多；TMC 是 2026 年新增的高地"],
    ["顶级期刊（Letters）", "IEEE JSAC、IEEE Wireless Comm. Letters、IEEE IoT Journal",
     "JSAC 属于通信领域最高档次，团队近三年有 2 篇（ISAC 方向）"],
    ["综述/旗舰杂志", "IEEE Wireless Communications、IEEE Network、IEEE Communications Magazine",
     "用于发布方向性、前瞻性观点，影响力大"],
    ["顶级会议", "IEEE ICC、IEEE GLOBECOM、IEEE WCNC、IEEE/CIC ICCC",
     "ICC 与 GLOBECOM 每年稳定多篇，是研究生的主要练兵场"],
    ["国内顶刊", "Science China Information Sciences、Engineering（中国工程院院刊）、China Communications、通信学报、电子与信息学报",
     "Engineering 2025 年第 54 卷空间互联网专题是重要窗口"],
    ["预印本", "arXiv",
     "2026 年新方向（SpaceMoE、ISCC 架构、星座容量标度）先挂 arXiv，是观察团队最新动向的最佳渠道"],
], widths=[3.0, 6.6, 6.0], size=9.5)

# ============ 四、潜力评估 ============
add_heading(doc, "四、潜力方向评估（核心结论）")
add_para(doc, "评估维度：① 团队投入力度与产出趋势；② 国家战略/产业需求强度；③ 方向新旧程度（越新红利越大）；"
              "④ 竞争激烈程度；⑤ 对学生的门槛与可迁移性。", size=10, space_after=8)

add_heading(doc, "第一梯队：强烈推荐（高潜力）", 2)

add_para(doc, "① 星上智能计算 / 轨道通用智能（SpaceMoE 方向）", size=11, bold=True, space_before=6, space_after=3)
add_table(doc, ["评估项", "判断"], [
    ["推荐指数", "★★★★★"],
    ["为什么好", "2026 年才刚开辟，成果还停留在 arXiv 阶段，属于「进去就是早期作者」的窗口期；"
                "同时踩中「大模型」和「卫星互联网」两个最热风口；合作方是香港大学黄凯斌、"
                "香港科技大学 Letaief 这样的国际顶级学者，起点极高"],
    ["产业对应", "星上算力、太空数据中心是 2025 年以来国内外资本和航天企业的新焦点，就业和转化前景好"],
    ["需要什么基础", "分布式系统 + 大模型推理（MoE/并行策略）+ 优化理论；编程能力要求高（PyTorch、分布式仿真）"],
    ["风险提示", "方向太新，理论体系尚未成型，容易走弯路；且一旦火起来，2027 年后竞争会迅速白热化"],
], widths=[2.6, 13.0], size=9.5)

add_para(doc, "② LEO 巨型星座容量理论与抗毁拓扑设计", size=11, bold=True, space_before=8, space_after=3)
add_table(doc, ["评估项", "判断"], [
    ["推荐指数", "★★★★★"],
    ["为什么好", "这是团队最深的护城河，从 2023 年做到 2026 年越做越厚，2026 年一年内就有"
                "TCOM、TMC 多篇产出；理论门槛高（随机几何、图论、渗流理论），外部团队很难短期切入，"
                "意味着你的成果不容易被「撞车」"],
    ["产业对应", "直接对应国家「GW 星座」「千帆星座」等巨型星座工程的顶层设计需求，有明确的国家任务牵引"],
    ["需要什么基础", "数学要求最高：随机几何、图论、排队论、凸优化；需要能用 Matlab/Python + STK 做星座仿真"],
    ["风险提示", "偏理论，出成果周期相对长；如果数学基础不扎实，前一年会比较痛苦"],
], widths=[2.6, 13.0], size=9.5)

add_para(doc, "③ 低空经济 / 数字低空网络（刘俊宇老师当前主攻）", size=11, bold=True, space_before=8, space_after=3)
add_table(doc, ["评估项", "判断"], [
    ["推荐指数", "★★★★☆"],
    ["为什么好", "低空经济是国家层面明确的战略新兴产业；实验室 2025 年牵头发布了全球首部"
                "《数字低空网络架构、覆盖及关键技术白皮书》，掌握标准话语权；"
                "刘俊宇老师 2026 年 TCOM 论文正在这条线上，跟他做最容易对上频道"],
    ["产业对应", "eVTOL、无人机物流、低空监管平台等落地场景多，横向项目和就业机会都很充足"],
    ["需要什么基础", "无线网络覆盖分析、随机几何、资源优化、强化学习；门槛相对温和，适合作为切入点"],
    ["风险提示", "热度高意味着全国做的人多，同质化论文已经很多，必须靠「可用性/容量理论」这类"
                "有理论深度的角度做出差异化——而这恰好是刘老师的强项"],
], widths=[2.6, 13.0], size=9.5)

add_heading(doc, "第二梯队：稳健可选（中高潜力）", 2)
add_table(doc, ["方向", "推荐指数", "核心判断"], [
    ["空间环境效应与星座可靠性（SEU、太阳背景噪声）", "★★★★",
     "交叉学科独家优势，Engineering 院刊背书，国内外几乎没有竞争者；缺点是偏小众，"
     "换赛道时可迁移性弱一些，适合想深耕航天系统的同学"],
    ["通感一体化 ISAC + 隐蔽通信", "★★★★",
     "6G 标准的核心特征，团队近三年有 2 篇 JSAC；国内做 ISAC 的团队非常多，"
     "需要靠「隐蔽通信」「近场」「STAR-RIS」这类细分点做出区隔"],
    ["通导遥一体化与高精度定位", "★★★☆",
     "国家需求明确（北斗、eLoran、遥感星座），团队 2026 年有 IEEE Wireless Communications 和 TAES 产出；"
     "偏系统工程，理论创新空间相对有限"],
    ["应急抗毁通信 / 网络可用性", "★★★☆",
     "刘俊宇老师深度参与，方法论与主线 A 一脉相承；社会价值高，但产业化路径不如低空经济清晰，"
     "更适合作为主线 A/D 的配套方向"],
], widths=[4.4, 1.8, 9.4], size=9.5)

add_heading(doc, "第三梯队：谨慎选择（趋于饱和）", 2)
add_table(doc, ["方向", "推荐指数", "核心判断"], [
    ["Cell-Free Massive MIMO / DRL 资源分配 / 能效优化", "★★☆",
     "论文数量多但同质化严重，「换个场景 + 换个 DRL 算法」的套路已被做透，"
     "顶刊接收难度逐年上升；适合作为练手，不适合作为博士主攻"],
    ["超密集网络干扰管理 / 容量标度率", "★★",
     "刘俊宇老师 2016–2020 年的成名方向（IEEE TWC 2018 等），2023 年后团队基本停止投入，"
     "属于已完成的历史阶段，不建议再作为新课题"],
    ["室内定位（指纹法/深度学习）", "★★",
     "虽仍列在刘老师的公开研究方向中，但近三年几乎无新成果产出，"
     "推测已不是重点，报考前建议当面确认"],
], widths=[4.4, 1.8, 9.4], size=9.5)

doc.add_page_break()

# ============ 五、行动建议 ============
add_heading(doc, "五、给报考 / 合作者的实用建议")

add_heading(doc, "5.1 招生规模（据刘俊宇老师主页 2025 年公开信息）", 2)
add_table(doc, ["培养类别", "拟招人数"], [
    ["博士研究生（团队）", "约 10 人"],
    ["西电本部 工学硕士", "约 20 人"],
    ["西电本部 专业硕士", "约 15 人"],
    ["杭州研究院 专业硕士", "约 15 人"],
    ["广州研究院 专业硕士", "约 4 人"],
], widths=[6.0, 4.0], size=9.5)
add_para(doc, "说明：团队体量大、招生名额多，这既意味着机会多，也意味着需要主动争取导师的关注度。"
              "以上为 2025 年数据，2027 年入学的具体名额请以当年官网公告为准。", size=9.5)

add_heading(doc, "5.2 提前需要补的能力", 2)
add_bullet(doc, "随机几何、图论、概率论——这是团队理论工作的通用语言，缺了会很吃力。", bold_head="数学基础：")
add_bullet(doc, "凸优化、强化学习（DRL）、图神经网络（GNN）——近三年几乎每篇论文都会用到其中之一。", bold_head="方法工具：")
add_bullet(doc, "Python（含 PyTorch）、Matlab；卫星方向还需要 STK 或类似的星座仿真工具；"
                "低空方向需要熟悉 3GPP NTN 相关规范。", bold_head="编程仿真：")
add_bullet(doc, "能读懂 IEEE TCOM/TWC 级别的论文并复现其仿真结果，是入门的最低要求。", bold_head="论文能力：")

add_heading(doc, "5.3 联系导师前建议做的三件事", 2)
add_bullet(doc, "去 arXiv 搜索「Min Sheng Xidian」，看最近 3–6 个月的预印本——那才是团队真正在做的东西，"
                "比官网主页更新快得多。", bold_head="① 看最新预印本：")
add_bullet(doc, "从刘俊宇老师 2026 年那篇《Availability-Aware Resource Management in Low-Altitude "
                "Heterogeneous Networks》入手精读，这是他当前方向的最佳切入点，也是邮件里最好的谈资。",
           bold_head="② 精读一篇代表作：")
add_bullet(doc, "邮件（junyuliu@xidian.edu.cn）中说清楚：你读了哪篇论文、你对哪个具体问题有想法、"
                "你会哪些工具。避免只写「老师我想报考您的研究生」这类空泛内容。", bold_head="③ 写一封有内容的邮件：")

# ============ 六、来源与说明 ============
add_heading(doc, "六、资料来源与核实说明")
add_para(doc, "本报告全部信息来自公开渠道，检索时间 2026 年 7 月 30 日。主要来源如下：", size=10, space_after=5)
add_bullet(doc, "刘俊宇个人主页 web.xidian.edu.cn/junyuliu/ 与 faculty.xidian.edu.cn/LJY7/", size=9.5)
add_bullet(doc, "盛敏个人主页 web.xidian.edu.cn/shengmin/ 与团队页 /team.html", size=9.5)
add_bullet(doc, "空天地一体化综合业务网全国重点实验室官网 isn.xidian.edu.cn", size=9.5)
add_bullet(doc, "Google Scholar：Min Sheng（ID: 7_vuvZ8AAAAJ）、Junyu Liu（ID: pHDnvSIAAAAJ）", size=9.5)
add_bullet(doc, "IEEE Xplore 作者页、IEEE ICC 2025/2026 与 GLOBECOM 2024/2025 官方程序册", size=9.5)
add_bullet(doc, "arXiv 预印本平台；Engineering（中国工程院院刊）2025 年第 54 卷", size=9.5)

add_para(doc, "需要特别注意的三点：", size=10.5, bold=True, space_before=10, space_after=4)
add_bullet(doc, "Google Scholar 上「Junyu Liu」（ID: pHDnvSIAAAAJ）这个账号混入了另一位同名学者的"
                "量子计算类论文（如 Nature Communications、PRX Quantum、npj Quantum Information 上的"
                "量子机器学习、玻色采样等工作），那位是美国匹兹堡大学的 Junyu Liu，与西电刘俊宇老师并非同一人。"
                "因此该主页显示的引用数 5,710、h 指数 38 被污染，不能直接引用。本报告已剔除全部量子计算类条目，"
                "只保留通信网络方向的成果。",
           bold_head="① 同名混淆（重要）：")
add_bullet(doc, "IEEE Xplore 的「Junyu Liu」作者页同样合并了日本国立情报学研究所网络安全方向的同名研究者，"
                "查询时需按合作者（Min Sheng、Jiandong Li）二次筛选。",
           bold_head="② IEEE Xplore 也有混淆：")
add_bullet(doc, "本次检索时，西电官网域名（web.xidian.edu.cn / faculty.xidian.edu.cn）无法直接抓取全文，"
                "相关人物信息来自搜索引擎索引的页面摘要。人事职称、招生名额等信息请以官网当前页面为准。",
           bold_head="③ 部分信息为二手摘要：")

add_para(doc, "论文标题与发表载体主要来自 Google Scholar 的结构化著录，个别条目的卷期页码未逐一核对，"
              "正式引用前请到 IEEE Xplore 或 DOI 页面复核。", size=9.5, space_before=6)

p = doc.add_paragraph()
p.alignment = WD_ALIGN_PARAGRAPH.CENTER
p.paragraph_format.space_before = Pt(20)
set_run(p.add_run("— 报告结束 —"), size=10, color=RGBColor(0x80, 0x80, 0x80))

out = r"C:\Users\lenovo\Desktop\西电盛敏团队(刘俊宇)研究方向与潜力分析_20260730.docx"
doc.save(out)
print("SAVED:", out)
