# -*- coding: utf-8 -*-
"""生成"阮玉晗老师及团队资料整理"Word 文档。

数据来源：西电个人主页 + DBLP + Semantic Scholar（/tmp/s2.json）。
"""
import json
import os
from docx import Document
from docx.shared import Pt, RGBColor, Cm
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.oxml.ns import qn

S2_JSON = os.path.join(os.environ.get("TEMP", "/tmp"), "s2.json")
OUT = os.path.join(os.path.expanduser("~"), "Desktop",
                   "阮玉晗老师及团队资料整理_20260730.docx")

# Semantic Scholar 同名混入条目，需剔除
EXCLUDE_KEYWORDS = ["Final Program", "A PRECISE RANGING WITH SUBCARRIER DIVERSITY"]

VENUE_CN = {
    "IEEE Transactions on Wireless Communications": "IEEE TWC（中科院一区Top）",
    "IEEE Transactions on Vehicular Technology": "IEEE TVT（中科院一区）",
    "IEEE Transactions on Cognitive Communications and Networking": "IEEE TCCN（中科院一区）",
    "IEEE Transactions on Instrumentation and Measurement": "IEEE TIM（中科院一区）",
    "IEEE Internet of Things Journal": "IEEE IoT-J（中科院一区Top）",
    "IEEE Communications Letters": "IEEE CL（通信快报）",
    "IEEE Wireless Communications Letters": "IEEE WCL（无线快报）",
    "IEEE Systems Journal": "IEEE Systems Journal",
    "IEEE Sensors Journal": "IEEE Sensors Journal",
    "IEEE Access": "IEEE Access",
    "Science China Information Sciences": "中国科学·信息科学",
    "Journal of Information and Intelligence": "Journal of Information and Intelligence",
    "Transactions on Emerging Telecommunications Technologies": "ETT",
    "J. Commun. Networks": "Journal of Communications and Networks",
    "IEEE Vehicular Technology Conference": "IEEE VTC（会议）",
    "Global Communications Conference": "IEEE GLOBECOM（会议）",
    "IEEE Wireless Communications and Networking Conference": "IEEE WCNC（会议）",
    "ICC 2025 - IEEE International Conference on Communications": "IEEE ICC（会议）",
    "2017 IEEE International Conference on Communications (ICC)": "IEEE ICC（会议）",
    "2025 IEEE 102nd Vehicular Technology Conference (VTC2025-Fall)": "IEEE VTC-Fall（会议）",
    "2017 IEEE/CIC International Conference on Communications in China (ICCC)": "IEEE/CIC ICCC（会议）",
    "2015 IEEE Wireless Communications and Networking Conference Workshops (WCNCW)": "IEEE WCNC Workshops（会议）",
    "IEEE International Symposium on Personal, Indoor and Mobile Radio Communications": "IEEE PIMRC（会议）",
    "Italian National Conference on Sensors": "Sensors（期刊）",
}


def load_papers():
    with open(S2_JSON, encoding="utf-8") as f:
        data = json.load(f)
    papers = []
    for p in data["data"]:
        title = p.get("title") or ""
        if any(k in title for k in EXCLUDE_KEYWORDS):
            continue
        authors = [a["name"] for a in p.get("authors", [])]
        pos = next((i + 1 for i, n in enumerate(authors) if "Ruan" in n), 0)
        papers.append({
            "year": p.get("year") or 0,
            "title": title,
            "venue": p.get("venue") or "",
            "cites": p.get("citationCount") or 0,
            "pos": pos,
            "n": len(authors),
        })
    papers.sort(key=lambda x: (-x["year"], -x["cites"]))
    return papers


# ---------- 排版工具 ----------
def set_doc_font(doc, cn="宋体", en="Times New Roman", size=10.5):
    style = doc.styles["Normal"]
    style.font.name = en
    style.font.size = Pt(size)
    style.element.rPr.rFonts.set(qn("w:eastAsia"), cn)


def h(doc, text, level=1):
    p = doc.add_heading(text, level=level)
    for run in p.runs:
        run.font.name = "微软雅黑"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
        run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    return p


def para(doc, text, bold=False, size=10.5, align=None, space_after=4):
    p = doc.add_paragraph()
    run = p.add_run(text)
    run.bold = bold
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    p.paragraph_format.space_after = Pt(space_after)
    if align:
        p.alignment = align
    return p


def bullet(doc, text, size=10.5):
    p = doc.add_paragraph(style="List Bullet")
    run = p.add_run(text)
    run.font.size = Pt(size)
    run.font.name = "Times New Roman"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    p.paragraph_format.space_after = Pt(2)
    return p


def table(doc, headers, rows, widths=None, size=9):
    t = doc.add_table(rows=1, cols=len(headers))
    t.style = "Light Grid Accent 1"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    for i, txt in enumerate(headers):
        cell = t.rows[0].cells[i]
        cell.text = ""
        run = cell.paragraphs[0].add_run(txt)
        run.bold = True
        run.font.size = Pt(size)
        run.font.name = "微软雅黑"
        run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    for row in rows:
        cells = t.add_row().cells
        for i, txt in enumerate(row):
            cells[i].text = ""
            run = cells[i].paragraphs[0].add_run(str(txt))
            run.font.size = Pt(size)
            run.font.name = "Times New Roman"
            run._element.rPr.rFonts.set(qn("w:eastAsia"), "宋体")
    if widths:
        for r in t.rows:
            for i, w in enumerate(widths):
                r.cells[i].width = Cm(w)
    return t


# ---------- 正文 ----------
def build():
    papers = load_papers()
    total = len(papers)
    total_cites = sum(p["cites"] for p in papers)
    first_author = [p for p in papers if p["pos"] == 1]
    journals = [p for p in papers if "会议" not in VENUE_CN.get(p["venue"], p["venue"])
                and "Conference" not in p["venue"] and "Workshops" not in p["venue"]
                and "Symposium" not in p["venue"]]

    doc = Document()
    set_doc_font(doc)

    # 封面标题
    t = doc.add_paragraph()
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = t.add_run("西安电子科技大学 通信工程学院\n阮玉晗老师及所在团队资料整理")
    run.bold = True
    run.font.size = Pt(20)
    run.font.name = "微软雅黑"
    run._element.rPr.rFonts.set(qn("w:eastAsia"), "微软雅黑")
    run.font.color.rgb = RGBColor(0x1F, 0x3B, 0x63)
    para(doc, "整理日期：2026年7月30日　|　资料来源：西电个人主页、DBLP、Semantic Scholar（均为公开信息）",
         size=9, align=WD_ALIGN_PARAGRAPH.CENTER)

    # 一、速览
    h(doc, "一、一页速览（先看这里）", 1)
    table(doc, ["项目", "内容"], [
        ["姓名", "阮玉晗（英文署名 Yuhan Ruan / Y. Ruan），女，1991年生"],
        ["单位", "西安电子科技大学 通信工程学院；综合业务网理论及关键技术国家重点实验室（ISN国家重点实验室）"],
        ["职称/身份", "副教授、硕士生导师（个人主页显示；早期公开资料记为“讲师／华山准聘副教授”，说明近年已晋升）"],
        ["联系方式", "邮箱 yhruan@xidian.edu.cn；办公室 北校区主楼 I-260；主页 web.xidian.edu.cn/yhruan/"],
        ["学术产出", f"公开可查论文约 {total} 篇（其中期刊约 {len(journals)} 篇），累计被引约 {total_cites} 次，h 指数约 16；第一作者论文 {len(first_author)} 篇"],
        ["主持项目", "4 项：国家自然科学基金青年项目、陕西省自然科学基础研究计划青年项目、中国博士后基金面上一等资助、ISN 国家重点实验室自主课题"],
        ["所在团队", "李勇朝教授（博导、IEEE 高级会员）团队；同团队青年骨干：张锐、李陶"],
        ["核心方向", "① 星地融合/空天地一体化网络资源管理　② AI 赋能频谱感知与无人机识别　③ 无蜂窝大规模 MIMO　④ 短包/NOMA 可靠传输　⑤ 区块链赋能资源交易"],
        ["一句话结论", "典型的“大团队 + 强产出”青年骨干：论文稳定发在 IEEE 一区期刊，方向紧贴 6G 与低轨卫星国家需求，适合想做通信理论+AI 交叉的硕士生"],
    ], widths=[3.0, 13.0])

    # 二、个人信息
    h(doc, "二、个人基本信息与经历", 1)
    h(doc, "2.1 教育与工作经历", 2)
    table(doc, ["时间", "单位 / 阶段", "备注"], [
        ["2009.08–2013.07", "西安电子科技大学　通信工程　学士", "本科即在西电"],
        ["2013.08–2018.06", "西安电子科技大学　通信与信息系统　博士（直博）", "导师：李勇朝 教授"],
        ["2016.03–2017.03", "英国赫瑞瓦特大学（Heriot-Watt University）联合培养博士生", "导师：Cheng-Xiang Wang（IEEE Fellow，信道建模领域国际权威）"],
        ["2018.07– 至今", "西安电子科技大学　军事通信学　博士后 → 留校任教", "博士后导师：李赞 教授"],
    ], widths=[3.4, 7.6, 5.0])
    para(doc, "解读：本硕博＋博士后全程在西电 ISN 国家重点实验室体系内，是典型的“本土培养 + 一年海外联培”路径。"
              "海外联培导师 Cheng-Xiang Wang 是 IEEE Fellow，这条线为她早期论文带来了很高的国际合作水准。", size=10)

    h(doc, "2.2 官方标注的研究方向", 2)
    for x in ["区块链（Blockchain）",
              "空天地一体化组网（卫星—空中—地面融合网络）",
              "认知星地网络资源分配（频谱共享、功率/带宽优化）"]:
        bullet(doc, x)
    para(doc, "注意：官方主页写的是“研究兴趣”，与实际发文重心并不完全一致。真实重心见第五章的论文数据分析。", size=10)

    # 三、团队
    h(doc, "三、所在团队情况", 1)
    h(doc, "3.1 团队带头人：李勇朝 教授", 2)
    table(doc, ["项目", "内容"], [
        ["身份", "教授、博士生导师；IEEE 高级会员，中国通信学会/中国电子学会高级会员；国家级一流课程负责人、校级教学名师"],
        ["团队荣誉", "西电校级“三好三有”研究生导学团队"],
        ["团队四大方向", "① 6G 通信技术（通感融合、车联网/应急救援）　② 人工智能赋能感知（无人机识别定位、射频指纹识别）　③ 星地网络融合（广域覆盖、认知通信）　④ 软硬件开发（C++、网络仿真、FPGA）"],
        ["培养去向", "毕业生主要进入中国电科系统各所、华为、中兴等（团队主页自述）"],
        ["团队文化", "主页自述“宽松和谐、团结进取”，重视校企/校所联合培养与国际交流"],
    ], widths=[3.0, 13.0])
    para(doc, "阮玉晗老师是该团队的青年教师骨干之一：她的博士导师即李勇朝，留校后仍在同一课题组，"
              "近五年论文几乎全部与李勇朝、张锐、李陶三位老师共同署名，学生一作、她挂第 2–4 作者（指导角色）。", size=10)

    h(doc, "3.2 团队常见合作者（从论文署名反推）", 2)
    table(doc, ["姓名", "单位", "在团队中的角色"], [
        ["李勇朝（Yongzhao Li）", "西电 ISN 国家重点实验室", "团队负责人、博导，几乎所有论文的通信作者"],
        ["张锐（Rui Zhang）", "西电 ISN 国家重点实验室", "青年骨干，主攻能效优化、无蜂窝 MIMO、短包/NOMA"],
        ["李陶（Tao Li）", "西电 ISN 国家重点实验室", "青年骨干，主攻无人机识别、射频指纹、信源数估计"],
        ["张海林（Hailin Zhang）", "西电 ISN 国家重点实验室", "资深教授，早期（2015–2019）论文合作者"],
        ["Cheng-Xiang Wang", "东南大学 / 赫瑞瓦特大学", "IEEE Fellow，她博士期间联培导师，2016–2019 论文密集合作"],
        ["Octavia A. Dobre", "加拿大纽芬兰纪念大学", "IEEE Fellow，射频指纹/无人机识别方向合作"],
        ["Cunhua Pan / Maged Elkashlan", "东南大学 / 伦敦玛丽女王大学", "2024 年 TWC 星地资源交易论文合作者"],
        ["Pei Xiao", "英国萨里大学 5GIC", "无蜂窝 MIMO、频谱感知方向合作"],
    ], widths=[4.2, 5.4, 6.4])
    para(doc, "解读：团队国际合作面很实（3 位 IEEE Fellow 级别的长期合作者），这对硕士生发论文和申请出国/读博是加分项。", size=10)

    # 四、项目
    h(doc, "四、主持科研项目（个人主页公开）", 1)
    table(doc, ["序号", "项目名称", "项目类型", "角色"], [
        ["1", "复杂干扰环境下无人机辅助的物联网通信中安全传输设计", "国家自然科学基金 青年科学基金项目", "主持"],
        ["2", "资源受限条件下无人机辅助的物联网通信中安全传输设计", "陕西省自然科学基础研究计划 青年项目", "主持"],
        ["3", "区块链架构下面向认知星地网络共赢的资源管理策略研究", "国家重点实验室创新人才类自主课题", "主持"],
        ["4", "面向物联网的高通量卫星多组多播传输技术", "中国博士后科学基金 面上项目一等资助", "主持"],
    ], widths=[1.2, 7.4, 5.4, 2.0])
    para(doc, "重要提示：主页未公开项目编号与起止年份。项目 1、2 都是“无人机辅助物联网安全传输”，"
              "说明这是她个人拿基金的主打标签；项目 3 对应“区块链 + 认知星地网络”，与她 2024 年 TWC 那篇博弈论文直接呼应。", size=10)

    # 五、论文成果
    h(doc, "五、论文成果", 1)
    h(doc, "5.1 总体统计（截至 2026 年 7 月 30 日）", 2)
    table(doc, ["统计项", "数值", "说明"], [
        ["公开论文总数", f"约 {total} 篇", "已剔除同名作者混入条目"],
        ["期刊论文", f"约 {len(journals)} 篇", "以 IEEE Transactions / Letters 为主"],
        ["会议论文", f"约 {total - len(journals)} 篇", "GLOBECOM、ICC、VTC、WCNC 等通信主流会议"],
        ["累计被引", f"约 {total_cites} 次", "Semantic Scholar 口径"],
        ["h 指数", "约 16", "对 1991 年出生的青年教师属于较强水平"],
        ["第一作者论文", f"{len(first_author)} 篇", "集中在 2015–2022 年，之后转为指导学生一作"],
    ], widths=[3.6, 3.0, 9.4])

    h(doc, "5.2 主要发表刊物分布", 2)
    venue_rank = {}
    for p in papers:
        key = VENUE_CN.get(p["venue"], p["venue"] or "其他")
        venue_rank[key] = venue_rank.get(key, 0) + 1
    rows = [[k, v] for k, v in sorted(venue_rank.items(), key=lambda x: -x[1]) if v >= 2]
    table(doc, ["刊物 / 会议", "篇数"], rows, widths=[12.0, 4.0])
    para(doc, "解读：IEEE Transactions on Wireless Communications（TWC）是无线通信领域公认的顶刊（中科院一区 Top），"
              "团队能稳定产出，说明理论功底扎实；同时大量 Letters（短文）说明产出节奏快，适合硕士生在 2–3 年内出成果。", size=10)

    h(doc, "5.3 高被引代表作（Top 12）", 2)
    top = sorted(papers, key=lambda x: -x["cites"])[:12]
    rows = []
    for p in top:
        rows.append([p["year"], p["title"], VENUE_CN.get(p["venue"], p["venue"]),
                     p["cites"], f"第{p['pos']}/{p['n']}" if p["pos"] else "—"])
    table(doc, ["年份", "论文标题", "发表刊物", "被引", "作者位次"], rows,
          widths=[1.3, 7.2, 4.0, 1.2, 2.3], size=8.5)

    h(doc, "5.4 完整论文清单（按年份倒序）", 2)
    para(doc, "说明：以下清单来自 DBLP 与 Semantic Scholar 自动索引，可能存在少量遗漏；"
              "“作者位次”中第 1 位表示她主导，第 2 位及之后多为她指导学生完成。", size=9)
    cur_year = None
    for p in papers:
        if p["year"] != cur_year:
            cur_year = p["year"]
            para(doc, f"【{cur_year} 年】", bold=True, size=10.5, space_after=2)
        pos = f"第{p['pos']}/{p['n']}作者" if p["pos"] else "作者位次未定"
        bullet(doc, f"{p['title']}. {VENUE_CN.get(p['venue'], p['venue'])}. "
                    f"（{pos}；被引 {p['cites']}）", size=9)

    # 六、研究脉络
    doc.add_page_break()
    h(doc, "六、研究方向演变脉络（重点分析）", 1)
    para(doc, "把她 10 年的论文按时间排开，可以清楚看到三个阶段的演变：", size=10)

    h(doc, "阶段一（2015–2019）：星地融合网络的理论性能分析 —— 打地基", 2)
    for x in ["关键词：混合星地协作网络、分布式空时码、中断概率、有效容量、能效/频谱效率权衡。",
              "代表作：TWC 2018《Energy Efficient Adaptive Transmissions in Integrated Satellite-Terrestrial Networks》（被引 77）、"
              "TWC 2019《Energy Efficient Power Allocation for Delay Constrained Cognitive Satellite Terrestrial Networks》（被引 86，她的最高被引论文）。",
              "特点：她本人一作为主，纯理论推导（概率分布、凸优化），与 IEEE Fellow Cheng-Xiang Wang 合作。这是她的学术“看家本领”。"]:
        bullet(doc, x, size=10)

    h(doc, "阶段二（2020–2024）：认知星地网络资源管理 + 博弈/区块链 —— 立标签", 2)
    for x in ["关键词：认知多波束卫星、认知区域设计、覆盖式（overlay）认知协作、分层博弈、资源交易、无人机三维部署。",
              "代表作：TWC 2024《A Hierarchical Game Framework for Win-Win Resource Trading in Cognitive Satellite Terrestrial Networks》"
              "（分层博弈实现星地双赢资源交易，被引 15，对应她主持的区块链自主课题）。",
              "特点：从“分析性能”转向“设计机制”，引入博弈论、经济学激励模型，这是她个人最具辨识度的方向。"]:
        bullet(doc, x, size=10)

    h(doc, "阶段三（2022–2026）：AI 赋能频谱感知与目标识别 + 6G 传输技术 —— 抢风口", 2)
    for x in ["方向 A｜AI + 电磁频谱：宽带频谱感知的时频定位（Transformer 自监督、GAN 域适应）、"
              "无人机射频识别（RFFI，用晶振漂移做设备指纹）、多无人机检测分类、信源数估计。"
              "代表作：TWC 2025《A Transformer-Based Self-Supervised Learning Framework for Robust Time-Frequency Localization》、"
              "TIM 2024《Radio Frequency Fingerprinting for WiFi Devices Using Oscillator Drifts》（被引 32）、"
              "IoT-J 2024《Anchor-Free Multi-UAV Detection and Classification Using Spectrogram》（被引 30）。",
              "方向 B｜无蜂窝大规模 MIMO（Cell-free massive MIMO）：异步系统的相干联合传输校准、CJT-NCJT 混合服务模式、分布式分簇。"
              "2024–2026 年产出集中，是团队新的增长点（主要与张锐老师合作）。",
              "方向 C｜短包 / URLLC / NOMA：有限码长下的功耗最小化、上行协作 NOMA 中继选择、短包 SNR 判定。稳定产出 TWC / TVT。",
              "特点：这一阶段她基本是第 2–4 作者（指导学生），说明她已进入“带学生出成果”的稳定期。"]:
        bullet(doc, x, size=10)

    # 七、潜力方向评估
    h(doc, "七、潜力方向评估（个人判断，供参考）", 1)
    para(doc, "评估维度说明：团队积累＝已有论文/代码/数据基础；领域热度＝2026 年学界与产业关注度；"
              "出论文难度＝硕士 2–3 年内发出 SCI 的难易；对口度＝毕业找工作或读博的匹配面。推荐指数 5 星最高。", size=9)
    table(doc, ["方向", "团队积累", "领域热度", "出论文难度", "就业/读博对口", "推荐指数"], [
        ["AI 赋能频谱感知与无人机/辐射源识别（RFFI、时频定位）", "很强（2022–2026 主力）", "高", "中（有数据和代码基线）", "极好：电科各所、反无人机、电磁频谱安全", "★★★★★"],
        ["星地融合 / 空天地一体化资源管理（含博弈、区块链激励）", "最强（十年积累）", "很高（低轨卫星国家战略）", "中偏难（理论推导重）", "很好：星网、航天五院/西安分院、电科", "★★★★★"],
        ["无蜂窝大规模 MIMO 与异步相干联合传输", "较强且在快速增长", "高（6G 标准候选技术）", "难（信号处理+数学门槛高）", "很好：华为、中兴、大唐等标准/算法岗", "★★★★"],
        ["无人机辅助物联网的安全传输（物理层安全）", "中（她两项主持基金的方向）", "中高", "中", "好：军工院所、保密通信", "★★★★"],
        ["短包通信 / URLLC / NOMA 有限码长", "强（稳定发 TWC/TVT）", "中", "中（套路成熟）", "中等：偏理论，工业界岗位面窄一些", "★★★"],
        ["区块链赋能网络资源交易", "弱（有课题但论文最少）", "中（已过最热期）", "难（跨领域，无现成基线）", "一般：与通信岗匹配度低", "★★☆"],
    ], widths=[4.4, 2.6, 2.0, 2.6, 3.4, 1.6], size=8.5)

    h(doc, "7.1 如果只选一个方向，建议怎么选", 2)
    for x in ["想“稳出论文 + 好就业”：选 AI + 频谱感知/无人机识别。这个方向团队有现成数据集（如 WiSig）、"
              "现成模型基线（CNN/Transformer/GAN），改进点多、审稿周期短，而且反无人机与电磁频谱安全是当前军工院所最缺人的方向之一。",
              "想“做有分量的理论 + 蹭国家战略红利”：选星地融合资源管理。这是她和团队的立身之本，"
              "低轨卫星互联网（中国星网、GW/G60 星座）正在大规模建设，方向不会过时，但需要能吃苦推公式（凸优化、博弈论、随机几何）。",
              "想“进华为/中兴做 6G 标准”：选无蜂窝大规模 MIMO。门槛最高但工业界最认，需要较好的线性代数与信号处理基础。",
              "谨慎选择区块链方向：虽然是她主持的自主课题，但团队公开论文里几乎看不到纯区块链成果，"
              "属于“想做但还没做起来”的状态，风险偏高（可能面临没有师兄师姐带、无现成基线的困境）。"]:
        bullet(doc, x, size=10)

    h(doc, "7.2 潜在风险与需要注意的点", 2)
    for x in ["她不是博导（目前公开信息为硕士生导师），若打算读博需要转投李勇朝教授等博导名下，报考前务必问清。",
              "近年论文中她多为第 2–4 作者，说明实际带学生方式可能是“大团队统一管理 + 她具体指导”，"
              "组内资源（服务器、数据、项目经费）通常由团队统筹，选导师时应把整个团队氛围一起考察。",
              "个人主页信息更新不及时（英文页几乎空白、招生信息栏是模板占位），不能只看主页判断她当前状态，建议直接邮件联系。"]:
        bullet(doc, x, size=10)

    # 八、联系与报考建议
    h(doc, "八、联系与报考实操建议", 1)
    for x in ["联系方式：邮箱 yhruan@xidian.edu.cn（学术邮件首选）；办公室 北校区主楼 I-260。",
              "邮件要点：一页以内说清——你是谁（学校/专业/成绩排名）、想做哪个方向（直接点名她某篇具体论文）、"
              "你已具备的技能（Python/PyTorch、MATLAB、凸优化、C++/FPGA 任一）、附简历 PDF。",
              "加分准备：若走 AI 方向，先跑通一个频谱图（spectrogram）分类的小项目；"
              "若走星地/资源分配方向，先自学凸优化（Boyd 教材前 5 章）并复现她 TWC 2019 那篇的功率分配仿真。",
              "教学信息：她承担本科《信号与系统》课程，这门课成绩若不错可在邮件里提一句。",
              "需自行核实的信息：当年硕士招生名额与学科代码（信息与通信工程 学硕 / 电子信息 专硕）、"
              "是否接收推免、组内是否有企业联合培养名额——这些主页上都没有，只能问她本人或研究生院招生目录。"]:
        bullet(doc, x, size=10)

    # 九、资料来源
    h(doc, "九、资料来源与免责说明", 1)
    for x in ["阮玉晗老师个人主页（个人信息 / 科学研究 / 论文成果 / 课程教学栏目）：https://web.xidian.edu.cn/yhruan/",
              "李勇朝教授个人主页（团队方向与培养情况）：https://web.xidian.edu.cn/yzli/",
              "DBLP 作者页（论文条目核对）：https://dblp.org/pid/163/8873",
              "Semantic Scholar 作者数据（被引次数、h 指数、2025–2026 最新论文）：api.semanticscholar.org",
              "西电通信工程学院导师介绍页：https://ste.xidian.edu.cn/yjsjy1/dsjs.htm",
              ]:
        bullet(doc, x, size=9)
    para(doc, "免责说明：以上全部内容来自公开网络信息，整理日期为 2026 年 7 月 30 日。"
              "论文清单由 DBLP / Semantic Scholar 自动索引生成，已人工剔除同名作者条目，但仍可能存在少量遗漏或误收；"
              "被引次数随时间变化。职称、招生名额、项目编号等关键信息请以学校官方发布或老师本人答复为准。"
              "第七章的方向评估为基于公开论文数据的分析判断，不代表老师或团队的官方规划。", size=9)

    doc.save(OUT)
    print("saved:", OUT)
    print("papers:", total, "cites:", total_cites, "first-author:", len(first_author))


if __name__ == "__main__":
    build()
