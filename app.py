"""
AI-Powered Classroom Management — Seating Plan Workshop
雙語版 · Bilingual Edition (繁體中文 / English)

ARCHITECTURE NOTE — Why this app uses st.components.v1.html() everywhere:
══════════════════════════════════════════════════════════════════════════════
When Streamlit is served through localtunnel (or any path-rewriting proxy),
every lazy-loaded React chunk fails with:
  TypeError: Failed to fetch dynamically imported module: .../[Name].[hash].js

Affected components include: st.metric, st.download_button, st.text_area,
st.dataframe, st.columns, st.markdown(unsafe_allow_html=True), st.expander.

The only proxy-safe Streamlit primitive is st.components.v1.html() — it
renders a sandboxed <iframe> with all HTML/CSS/JS inlined, requiring zero
dynamic imports from the host origin.

This app therefore renders the ENTIRE UI as one self-contained HTML document
inside a single components.v1.html() call, using:
  - postMessage() to send textarea / button events back to Python
  - st.query_params  as the state bridge (supported in Streamlit ≥ 1.30)
  - st.rerun()       to redraw when state changes
══════════════════════════════════════════════════════════════════════════════
"""

import io
import json
import random
import re
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components

# ── Page config (only sets browser tab title/icon — no lazy JS needed) ────────
st.set_page_config(
    page_title="AI 課室管理 · Classroom Management Workshop",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="collapsed",   # sidebar disabled; we render our own
)

# ══════════════════════════════════════════════════════════════════════════════
# 1. BILINGUAL STRINGS
# ══════════════════════════════════════════════════════════════════════════════

ZH = {
    "page_title":    "AI 課室管理工作坊",
    "page_subtitle": "工作坊模組 · 座位表設計 — 比較普通與工程化 AI 提示的差異",
    "lang_btn":      "🌐 Switch to English",
    # sidebar
    "res_hub":       "📦 資源中心",
    "res_sub":       "開始工作坊前請先下載以下檔案",
    "cl_title":      "📋 學生名單",
    "cl_desc":       "30 名學生 · 姓名、性別、學術層級、特殊需要",
    "cl_btn":        "⬇ 下載 Class_List.xlsx",
    "pdf_title":     "📄 限制條件表",
    "pdf_desc":      "特殊教育需要規則 · 混合能力 · 課室佈局 · 行為備注",
    "pdf_btn":       "⬇ 下載 Constraint_Ledger.pdf",
    "prompt_ref":    "💡 提示語參考",
    "s1_prompt_lbl": "第一階段 · 普通提示",
    "s2_prompt_lbl": "第二階段 · 引導提示",
    "goals_title":   "🎯 工作坊目標",
    "goals":         ["了解提示工程的質量差異", "練習有限制條件意識的 AI 提示", "根據專業標準評估 AI 輸出"],
    # metrics
    "m_students":    "學生人數",
    "m_constraints": "限制條件數量",
    "m_stages":      "階段數量",
    # how it works
    "how_title":     "本工作坊的流程：",
    "how_steps":     ["從資源中心（左側）下載樣本檔案。",
                      "使用每個提示語向您偏好的 AI 工具（ChatGPT、Gemini、Claude 等）提問。",
                      "將 AI 的回應貼入以下各階段。",
                      "對比引擎將根據專業座位安排限制條件對兩個輸出進行評分。"],
    # stages
    "s1_badge": "第一階段", "s1_title": "普通提示方法",
    "s1_think": "🗣 思考大聲說：在貼上回應之前，大聲描述您對沒有背景資料的基本 AI 提示有何期望。您認為 AI 會關注什麼？它會遺漏什麼？",
    "s1_label": "將 AI 對普通提示的回應貼在此處：",
    "s1_ph":    "例如：「以下是為您 30 位學生按字母順序排列的座位表...」",
    "s1_check": "限制條件檢查 — 普通回應：",
    "s1_div":   "↓ 現在試試工程化提示 ↓",
    "s2_badge": "第二階段", "s2_title": "引導提示方法",
    "s2_think": "🗣 思考大聲說：您已在左側看到結構化提示 — 它包含檔案、具體規則和輸出格式。預測一下：AI 現在會處理哪些之前遺漏的限制條件？",
    "s2_label": "將 AI 對引導提示的回應貼在此處：",
    "s2_ph":    "例如：| 排 | 座位 | 學生 | 層級 | 備注 |",
    "s2_check": "限制條件檢查 — 引導回應：",
    "s2_div":   "↓ 生成對比報告 ↓",
    "s3_badge": "第三階段", "s3_title": "對比引擎",
    "s3_think": "🗣 思考大聲說：並排查看兩個分數。這個差異告訴您什麼關於如何向 AI 發出指令的啟示？",
    "s3_run":   "▶ 執行對比引擎",
    "s3_reset": "↺ 重置全部",
    "s3_info":  "請填寫第一和第二階段的文字區域以解鎖對比引擎。",
    # dashboard
    "dash_title":   "📊 對比儀表板",
    "delta_text":   "引導提示在限制條件覆蓋率上比普通提示",
    "delta_higher": "高",
    "delta_lower":  "低",
    "delta_pts":    "個百分點",
    "naive_col":    "🔴 第一階段 · 普通回應",
    "guided_col":   "🟢 第二階段 · 引導回應",
    "coverage":     "限制條件覆蓋率",
    "preview":      "回應預覽：",
    "analysis":     "限制條件分析：",
    "breakdown":    "🔬 逐項限制條件分析",
    "col_name":     "限制條件",
    "col_wt":       "權重",
    "col_naive":    "普通",
    "col_guided":   "引導",
    "col_change":   "變化",
    "pass":  "✅ 通過", "fail": "❌ 不通過",
    "gained":"⬆ 獲得", "lost": "⬇ 失去", "same": "— 相同",
    "trunc": "…(已截斷)",
    "reflect": "🗣 最終反思：根據這個比較，寫下一條規則，您會將其加入個人 AI 提示核對清單中。您如何向剛接觸 AI 工具的同事解釋這個區別？",
    "footer": "AI 課室管理工作坊 · 原型 · 僅供教育培訓使用",
    # constraints
    "c_sen":  "特殊需要學生安排在前排",       "cd_sen":  "特殊需要學生分配在前排 / 教師視線範圍內",
    "c_eal":  "提及英語學習者 (EAL)",         "cd_eal":  "明確考慮到英語學習者",
    "c_b1":   "提及第一組 / 高能力",           "cd_b1":   "包含高能力分組策略",
    "c_b3":   "提及第三組 / 待發展",           "cd_b3":   "明確處理待發展學習者",
    "c_mix":  "混合能力分組",                  "cd_mix":  "提及混合能力同伴分組策略",
    "c_gen":  "性別平衡",                      "cd_gen":  "注明性別平衡 / 分配",
    "c_beh":  "行為 / 衝突備注",               "cd_beh":  "遵守行為分隔限制條件",
    "c_lay":  "結構化佈局（排 / 桌）",         "cd_lay":  "包含明確的位置 / 佈局結構",
    "score_label": "限制條件覆蓋率分數：",
    "score_pts":   "加權分數",
    "naive_prompt":  "為我的 30 名學生制定座位表。",
    "guided_prompt": ("您是一位專業的課室管理專家。請使用附件 Class_List.xlsx 和 Constraint_Ledger.pdf，"
                      "為 14 號課室（6 排 × 5 座位）制定座位表。\n\n需遵守的規則：\n"
                      "1. 所有特殊需要 (SEN) 學生 → 前排（第 1 排）。\n"
                      "2. 英語學習者 (EAL) 與同組流利英語同伴配對。\n"
                      "3. 每組應混合能力（≥1 名第一組 + ≥1 名第三組學生）。\n"
                      "4. 每桌性別比例不超過 3:1。\n"
                      "5. 遵守所有行為分隔備注。\n"
                      "6. 以 Markdown 表格呈現輸出：排 | 座位 | 學生 | 層級 | 備注"),
}

EN = {
    "page_title":    "AI Classroom Management Workshop",
    "page_subtitle": "Workshop Module · Seating Plan Design — Comparing Naïve vs. Guided AI Prompting",
    "lang_btn":      "🌐 切換至繁體中文",
    "res_hub":       "📦 Resource Hub",
    "res_sub":       "Download these files before starting the workshop",
    "cl_title":      "📋 Class List",
    "cl_desc":       "30 students · Name, Gender, Academic Tier, Special Needs",
    "cl_btn":        "⬇ Download Class_List.xlsx",
    "pdf_title":     "📄 Constraint Ledger",
    "pdf_desc":      "SEN rules · Mixed ability · Room layout · Behaviour notes",
    "pdf_btn":       "⬇ Download Constraint_Ledger.pdf",
    "prompt_ref":    "💡 Prompt Reference",
    "s1_prompt_lbl": "Stage 1 · Naïve Prompt",
    "s2_prompt_lbl": "Stage 2 · Guided Prompt",
    "goals_title":   "🎯 Workshop Goals",
    "goals":         ["Understand prompt engineering quality differences",
                      "Practice constraint-aware AI prompting",
                      "Evaluate AI outputs against professional standards"],
    "m_students":    "Students",
    "m_constraints": "Constraints",
    "m_stages":      "Stages",
    "how_title":     "How this workshop works:",
    "how_steps":     ["Download the sample files from the Resource Hub (left panel).",
                      "Use each prompt card to query your preferred AI tool (ChatGPT, Gemini, Claude, etc.).",
                      "Paste the AI's response into the relevant stage below.",
                      "The Contrast Engine will score both outputs against professional seating constraints."],
    "s1_badge": "Stage 1", "s1_title": "The Naïve Approach",
    "s1_think": "🗣 Think-Aloud: Before you paste, describe out loud what you expect from a basic AI prompt with no context. What will the AI focus on? What will it miss?",
    "s1_label": "Paste the AI's response to the naïve prompt here:",
    "s1_ph":    "e.g. Here is a simple seating plan for your 30 students arranged alphabetically...",
    "s1_check": "Constraint Check — Naïve Response:",
    "s1_div":   "↓ Now try the engineered prompt ↓",
    "s2_badge": "Stage 2", "s2_title": "The Guided Approach",
    "s2_think": "🗣 Think-Aloud: You've seen the structured prompt — files, specific rules, output format. Predict: which constraints will the AI now address that it missed before?",
    "s2_label": "Paste the AI's response to the guided prompt here:",
    "s2_ph":    "e.g. | Row | Seat | Student | Tier | Notes |",
    "s2_check": "Constraint Check — Guided Response:",
    "s2_div":   "↓ Generate the contrast report ↓",
    "s3_badge": "Stage 3", "s3_title": "The Contrast Engine",
    "s3_think": "🗣 Think-Aloud: Look at the two scores side by side. What does the difference tell you about how you give instructions to an AI?",
    "s3_run":   "▶ Run Contrast Engine",
    "s3_reset": "↺ Reset All",
    "s3_info":  "Fill in both Stage 1 and Stage 2 text areas to unlock the Contrast Engine.",
    "dash_title":   "📊 Comparison Dashboard",
    "delta_text":   "The Guided Prompt scored",
    "delta_higher": "higher",
    "delta_lower":  "lower",
    "delta_pts":    "percentage points",
    "naive_col":    "🔴 Stage 1 · Naïve Response",
    "guided_col":   "🟢 Stage 2 · Guided Response",
    "coverage":     "Constraint Coverage",
    "preview":      "Response Preview:",
    "analysis":     "Constraint Analysis:",
    "breakdown":    "🔬 Constraint-by-Constraint Breakdown",
    "col_name":     "Constraint",
    "col_wt":       "Weight",
    "col_naive":    "Naïve",
    "col_guided":   "Guided",
    "col_change":   "Change",
    "pass":  "✅ Pass",   "fail": "❌ Fail",
    "gained":"⬆ Gained", "lost": "⬇ Lost",  "same": "— Same",
    "trunc": "…(truncated)",
    "reflect": "🗣 Final Reflection: Write down one rule you would add to your AI prompting checklist. How would you teach this to a colleague new to AI tools?",
    "footer": "AI-Powered Classroom Management Workshop · Prototype · For educational training purposes only",
    "c_sen":  "SEN placed front row",        "cd_sen":  "SEN students assigned to front row / teacher proximity",
    "c_eal":  "EAL students mentioned",      "cd_eal":  "EAL learners explicitly considered",
    "c_b1":   "Band 1 / High ability",       "cd_b1":   "High-ability grouping strategy present",
    "c_b3":   "Band 3 / Developing",         "cd_b3":   "Developing learners explicitly addressed",
    "c_mix":  "Mixed ability grouping",      "cd_mix":  "Mixed-ability peer grouping mentioned",
    "c_gen":  "Gender balance",              "cd_gen":  "Gender balance / distribution noted",
    "c_beh":  "Behaviour / conflict notes",  "cd_beh":  "Behaviour separation constraints honoured",
    "c_lay":  "Structured layout",           "cd_lay":  "Explicit positional / layout structure present",
    "score_label": "Constraint Coverage Score:",
    "score_pts":   "weighted points",
    "naive_prompt":  "Create a seating plan for my class of 30 students.",
    "guided_prompt": ("You are an expert classroom manager. Using the attached Class_List.xlsx "
                      "and Constraint_Ledger.pdf, generate a seating plan for Room 14 (6 rows x 5 seats).\n\n"
                      "Rules to follow:\n"
                      "1. All SEN students -> Front Row (Row 1).\n"
                      "2. EAL students paired with fluent English Band 1/2 peer.\n"
                      "3. Every table group: mixed ability (>=1 Band 1 + >=1 Band 3).\n"
                      "4. No more than 3:1 gender ratio per table.\n"
                      "5. Honour all behaviour separation notes.\n"
                      "6. Output as Markdown table: Row | Seat | Student | Tier | Notes"),
}

LANGS = {"zh": ZH, "en": EN}

# ══════════════════════════════════════════════════════════════════════════════
# 2. SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════

DEFAULTS = {
    "lang":            "zh",
    "naive_text":      "",
    "guided_text":     "",
    "show_comparison": False,
    "action":          "",   # last postMessage action
}
for k, v in DEFAULTS.items():
    if k not in st.session_state:
        st.session_state[k] = v

def S(key):
    """Get translated string for current language."""
    return LANGS[st.session_state.lang][key]

# ══════════════════════════════════════════════════════════════════════════════
# 3. CONSTRAINT ENGINE (pure Python — no Streamlit components)
# ══════════════════════════════════════════════════════════════════════════════

CONSTRAINT_DEFS = [
    # (label_key, desc_key, keywords_en, keywords_zh, weight)
    ("c_sen", "cd_sen", ["sen","front row","row 1","first row","special needs"], ["特殊需要","前排","第一排","sEN"], 3),
    ("c_eal", "cd_eal", ["eal","english as additional","language support"],      ["英語學習者","英語支援"],         2),
    ("c_b1",  "cd_b1",  ["band 1","high ability","gifted","g&t","talented"],     ["第一組","高能力","資優"],        2),
    ("c_b3",  "cd_b3",  ["band 3","developing","lower ability"],                  ["第三組","待發展","低能力"],     2),
    ("c_mix", "cd_mix", ["mixed ability","peer learning","mixed group","heterogeneous"], ["混合能力","同伴學習"],   2),
    ("c_gen", "cd_gen", ["gender","male","female","boy","girl"],                  ["性別","男","女"],               1),
    ("c_beh", "cd_beh", ["behaviour","behavior","conflict","separate","away from","do not seat"], ["行為","衝突","分隔","遠離"], 2),
    ("c_lay", "cd_lay", ["row","table","seat","column","front","back","position"],["排","座位","前","後","位置"],   1),
]

def run_check(text: str) -> dict:
    tl = text.lower()
    results, total_w, earned_w = [], 0, 0
    for lk, dk, kw_en, kw_zh, w in CONSTRAINT_DEFS:
        passed = any(k in tl for k in kw_en + kw_zh)
        results.append({"name": S(lk), "desc": S(dk), "passed": passed, "weight": w})
        total_w  += w
        earned_w += w if passed else 0
    score = round(earned_w / total_w * 100) if total_w else 0
    return {"checks": results, "score": score, "earned": earned_w, "total": total_w}

# ══════════════════════════════════════════════════════════════════════════════
# 4. IN-MEMORY FILE GENERATORS
# ══════════════════════════════════════════════════════════════════════════════

@st.cache_data
def gen_xlsx() -> bytes:
    first = ["Amara","Ben","Chloe","David","Evie","Finn","Grace","Henry","Imani","Jake",
             "Kezia","Liam","Mia","Noah","Olivia","Priya","Quinn","Reuben","Sofia","Theo",
             "Uma","Victor","Wren","Xander","Yara","Zoe","Aiden","Bella","Carlos","Dara"]
    last  = ["Smith","Johnson","Williams","Brown","Jones","Garcia","Miller","Davis",
             "Martinez","Wilson","Anderson","Taylor","Thomas","Hernandez","Moore",
             "Martin","Jackson","Thompson","White","Lopez","Lee","Harris","Clark",
             "Lewis","Robinson","Walker","Perez","Hall","Young","Allen"]
    genders = ["Male / 男","Female / 女","Non-binary / 非二元"]
    tiers   = ["Band 1 (High / 高)","Band 2 (Mid / 中)","Band 3 (Developing / 待發展)"]
    needs   = ["None / 無","EAL / 英語學習者","SEN - Dyslexia / 讀寫困難","SEN - ADHD / 專注力不足",
               "SEN - Visual Impairment / 視障","SEN - Hearing Impairment / 聽障",
               "Gifted & Talented / 資優","LAC / 受照顧兒童"]
    beh     = ["","","","Seat away from windows / 遠離窗戶","Needs frequent breaks / 需要頻繁休息",
               "Do not seat next to [peer conflict] / 勿與指定同學相鄰","Seat near teacher / 靠近教師"]
    random.seed(42)
    rows = [{"Student ID": f"S{1000+i}",
             "Name / 姓名": f"{first[i]} {last[i]}",
             "Gender / 性別": random.choices(genders,[48,48,4])[0],
             "Academic Tier / 學術層級": random.choices(tiers,[30,45,25])[0],
             "Special Needs / 特殊需要": random.choices(needs,[50,10,8,8,4,4,10,6])[0],
             "Reading Age (yrs) / 閱讀年齡": round(random.uniform(8.5,16.0),1),
             "Behaviour Note / 行為備注": random.choice(beh)} for i in range(30)]
    buf = io.BytesIO()
    with pd.ExcelWriter(buf, engine="openpyxl") as w:
        pd.DataFrame(rows).to_excel(w, index=False, sheet_name="Class List")
    return buf.getvalue()

@st.cache_data
def gen_pdf() -> bytes:
    try:
        from fpdf import FPDF
    except ImportError:
        return b"%PDF-1.4 placeholder"
    pdf = FPDF(); pdf.set_auto_page_break(auto=True, margin=15); pdf.add_page()
    pdf.set_font("Helvetica","B",16); pdf.set_text_color(46,125,50)
    pdf.cell(0,10,"Seating Plan Constraint Ledger",ln=True,align="C")
    pdf.cell(0,7,"座位表限制條件表",ln=True,align="C")
    pdf.set_font("Helvetica","",9); pdf.set_text_color(100,100,100)
    pdf.cell(0,5,"Year 9 Science · Room 14 | 中三科學 · 14 號課室",ln=True,align="C")
    pdf.ln(4); pdf.set_draw_color(46,125,50); pdf.set_line_width(0.5)
    pdf.line(10,pdf.get_y(),200,pdf.get_y()); pdf.ln(4)
    secs = [
        ("MANDATORY CONSTRAINTS 強制限制條件",[
            ("SEN Placements 特殊需要","All SEN must be in front two rows.\n所有SEN學生須在前兩排。"),
            ("EAL Support 英語學習者","EAL paired with fluent English peer.\nEAL學生應與流利英語同伴配對。"),
            ("Visual/Hearing 視聽障礙","Must occupy Front Row seats 1–4.\n必須坐在前排第1-4號座位。"),
            ("Behaviour 行為分隔","Min one row/column gap from named peer.\n與指定同學相隔至少一整排或列。"),
        ]),
        ("PEDAGOGICAL 教學限制條件",[
            ("Mixed Ability 混合能力","Each group: ≥1 Band1 + ≥1 Band3.\n每組：≥1名第一組+≥1名第三組。"),
            ("Gender 性別","Max 3:1 ratio per table.\n每桌最多3:1比例。"),
            ("G&T 資優生","Group together or distribute.\n集中或分散各組。"),
        ]),
        ("ROOM LAYOUT 課室佈局",[
            ("Front Row 前排","Row 1 = nearest whiteboard. 6×5=30 seats.\n第1排=最靠近白板，6排×5座=30座。"),
            ("Egress 出口","A1 and F5 always accessible.\nA1和F5須隨時通暢。"),
            ("Gas Taps 煤氣","Row 6 has taps; avoid Band3/ADHD there.\n第6排有煤氣；避免第三組/ADHD在此。"),
        ]),
    ]
    for st_title, items in secs:
        pdf.set_font("Helvetica","B",11); pdf.set_text_color(46,125,50)
        pdf.set_fill_color(232,245,233); pdf.cell(0,8,f"  {st_title}",ln=True,fill=True); pdf.ln(2)
        for c,d in items:
            pdf.set_font("Helvetica","B",9); pdf.set_text_color(27,94,32)
            pdf.cell(5); pdf.cell(0,5,f"• {c}",ln=True)
            pdf.set_font("Helvetica","",8); pdf.set_text_color(60,60,60)
            pdf.set_x(15); pdf.multi_cell(0,4.5,d); pdf.ln(1)
        pdf.ln(3)
    pdf.set_y(-18); pdf.set_font("Helvetica","I",7); pdf.set_text_color(160,160,160)
    pdf.cell(0,5,"AI Classroom Management Workshop · Training purposes only · 僅供培訓使用",align="C")
    return pdf.output()

# ══════════════════════════════════════════════════════════════════════════════
# 5. HTML BUILDER — the entire UI as one self-contained document
#    No external JS, no dynamic imports, no lazy chunks.
# ══════════════════════════════════════════════════════════════════════════════

def js_str(s: str) -> str:
    """Safely escape a Python string for embedding in a JS string literal."""
    return json.dumps(str(s))

def build_check_html(result: dict) -> str:
    """Build inline HTML for constraint badges + score bar."""
    score = result["score"]
    color = "#2E7D32" if score >= 70 else ("#E65100" if score >= 40 else "#C62828")
    badges = "".join(
        f'<span class="badge {"pass" if c["passed"] else "fail"}">{"✓" if c["passed"] else "✗"} {c["name"]}</span>'
        for c in result["checks"]
    )
    sl = S("score_label"); sp = S("score_pts")
    e, t = result["earned"], result["total"]
    return f"""
    <div class="score-wrap">
      <div class="score-label">{sl} <strong style="color:{color}">{score}%</strong>
        ({e}/{t} {sp})</div>
      <div class="score-bg"><div class="score-fill" style="width:{score}%"></div></div>
    </div>
    <div class="badge-grid">{badges}</div>"""

def build_comparison_html(naive_r: dict, guided_r: dict) -> str:
    """Build the full comparison dashboard HTML."""
    delta       = guided_r["score"] - naive_r["score"]
    dc          = "#2E7D32" if delta > 0 else ("#C62828" if delta < 0 else "#607D8B")
    ds          = f"+{delta}" if delta > 0 else str(delta)
    direction   = S("delta_higher") if delta >= 0 else S("delta_lower")
    dt, dpts    = S("delta_text"), S("delta_pts")

    def col_html(result, css, title, color, text):
        preview = text[:800].replace("<","&lt;").replace(">","&gt;")
        if len(text) > 800: preview += S("trunc")
        rows_html = "".join(
            f'<div class="analysis-row">{"✅" if c["passed"] else "❌"} '
            f'<strong>{c["name"]}</strong> — <em>{c["desc"]}</em></div>'
            for c in result["checks"]
        )
        pv, an = S("preview"), S("analysis")
        return f"""
        <div class="cmp-col {css}">
          <h4>{title}</h4>
          <div class="big-score" style="color:{color}">{result["score"]}%</div>
          <div class="cov-label">{S("coverage")}</div>
          <div class="preview-label">{pv}</div>
          <div class="preview-box">{preview}</div>
          <div class="preview-label">{an}</div>
          {rows_html}
        </div>"""

    naive_html  = col_html(naive_r,  "naive-col",  S("naive_col"),  "#EF5350",
                           st.session_state.naive_text)
    guided_html = col_html(guided_r, "guided-col", S("guided_col"), "#2E7D32",
                           st.session_state.guided_text)

    # breakdown table
    rows = []
    for nd, gd in zip(naive_r["checks"], guided_r["checks"]):
        ch = (S("gained") if (not nd["passed"] and gd["passed"]) else
              S("lost")   if (nd["passed"]  and not gd["passed"]) else S("same"))
        rows.append(
            f'<tr><td>{nd["name"]}</td><td>{nd["weight"]}pt</td>'
            f'<td>{"✅" if nd["passed"] else "❌"}</td>'
            f'<td>{"✅" if gd["passed"] else "❌"}</td>'
            f'<td>{ch}</td></tr>'
        )
    rows_html = "\n".join(rows)
    cn,cw,cnv,cgu,cc = S("col_name"),S("col_wt"),S("col_naive"),S("col_guided"),S("col_change")

    reflect = S("reflect")
    bd_title = S("breakdown")
    dash_title = S("dash_title")

    return f"""
    <div class="dash-banner">
      <span style="font-size:1.6rem">📈</span>
      <span>{dt} <strong style="color:{dc}">{ds} {dpts}</strong> {direction}</span>
    </div>
    <h3 style="color:#1B5E20;margin:1rem 0 .75rem">{dash_title}</h3>
    <div class="cmp-grid">
      {naive_html}
      {guided_html}
    </div>
    <hr style="border:none;border-top:1px solid #C8E6C9;margin:1.4rem 0">
    <h4 style="color:#1B5E20">{bd_title}</h4>
    <table class="breakdown-table">
      <thead><tr><th>{cn}</th><th>{cw}</th><th>{cnv}</th><th>{cgu}</th><th>{cc}</th></tr></thead>
      <tbody>{rows_html}</tbody>
    </table>
    <div class="think-aloud" style="margin-top:1.2rem">{reflect}</div>
    """

def build_full_html() -> str:
    """
    Render the ENTIRE app as one self-contained HTML page.
    All state is passed in as JSON; user actions are sent back via
    window.parent.postMessage so Streamlit can update session_state.
    """
    lang       = st.session_state.lang
    naive_txt  = st.session_state.naive_text
    guided_txt = st.session_state.guided_text
    show_cmp   = st.session_state.show_comparison

    naive_check  = run_check(naive_txt)  if naive_txt.strip()  else None
    guided_check = run_check(guided_txt) if guided_txt.strip() else None
    both         = bool(naive_txt.strip() and guided_txt.strip())

    # Stage headers
    def stage_card(badge, title):
        return (f'<div class="stage-card">'
                f'<div class="stage-header">'
                f'<span class="stage-badge">{badge}</span>'
                f'<span class="stage-title">{title}</span>'
                f'</div></div>')

    naive_check_html  = build_check_html(naive_check)  if naive_check  else ""
    guided_check_html = build_check_html(guided_check) if guided_check else ""
    comparison_html   = build_comparison_html(naive_check, guided_check) if (show_cmp and both) else ""
    s3_info_html      = "" if both else f'<div class="info-box">{S("s3_info")}</div>'

    run_disabled  = "" if both else "disabled"
    run_btn_style = "" if both else "opacity:.45;cursor:not-allowed;"

    # Escape current values for embedding in JS
    naive_val  = json.dumps(naive_txt)
    guided_val = json.dumps(guided_txt)

    # Goals list
    goals_html = "".join(f"<li>{g}</li>" for g in S("goals"))
    # How steps
    steps_html = "".join(f"<li>{s}</li>" for s in S("how_steps"))

    # Sidebar prompts
    np_escaped = S("naive_prompt").replace("\n","\\n").replace("`","\\`")
    gp_escaped = S("guided_prompt").replace("\n","\\n").replace("`","\\`")

    return f"""<!DOCTYPE html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
  @import url('https://fonts.googleapis.com/css2?family=Noto+Serif+TC:wght@400;700&family=DM+Serif+Display&family=Noto+Sans+TC:wght@300;400;500;600&family=DM+Sans:wght@300;400;500;600&display=swap');
  *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
  :root{{
    --green:#2E7D32;--green-l:#43A047;--green-d:#1B5E20;
    --accent:#FF8F00;--bg:#F7F9F7;--card:#fff;
    --border:#C8E6C9;--text:#1A2E1B;--muted:#5C7A5D;
    --fail:#C62828;
  }}
  body{{font-family:'DM Sans','Noto Sans TC',sans-serif;background:var(--bg);color:var(--text);font-size:15px;line-height:1.6}}

  /* ── Layout ── */
  .app-shell{{display:flex;min-height:100vh}}
  .sidebar{{width:300px;min-width:300px;background:var(--green-d);padding:1.2rem 1rem;display:flex;flex-direction:column;gap:.6rem}}
  .main{{flex:1;padding:1.4rem 1.8rem;overflow-x:hidden}}

  /* ── Sidebar ── */
  .sidebar,.sidebar *{{color:#E8F5E9}}
  .sidebar h2{{font-size:1rem;font-weight:600;margin:.4rem 0 .2rem}}
  .sidebar p{{font-size:.8rem;opacity:.85;margin:.2rem 0 .5rem}}
  .sidebar hr{{border:none;border-top:1px solid rgba(255,255,255,.2);margin:.5rem 0}}
  .sb-section{{background:rgba(255,255,255,.09);border-radius:9px;padding:.8rem .9rem;margin-bottom:.4rem}}
  .sb-section h3{{font-size:.88rem;font-weight:600;margin-bottom:.25rem}}
  .sb-section p{{font-size:.78rem;margin-bottom:.5rem}}
  .sb-btn{{width:100%;background:rgba(255,255,255,.13);color:#E8F5E9;border:1px solid rgba(255,255,255,.28);
    border-radius:7px;padding:.4rem .7rem;font-size:.8rem;cursor:pointer;text-align:left}}
  .sb-btn:hover{{background:rgba(255,255,255,.22)}}
  .lang-btn{{width:100%;background:rgba(255,255,255,.13);color:#fff;border:1px solid rgba(255,255,255,.3);
    border-radius:7px;padding:.35rem .7rem;font-size:.82rem;cursor:pointer;margin-bottom:.5rem}}
  .lang-btn:hover{{background:rgba(255,255,255,.22)}}
  .collapsible-head{{cursor:pointer;font-size:.82rem;font-weight:500;padding:.3rem 0;display:flex;align-items:center;gap:.4rem}}
  .collapsible-head::before{{content:"▶";font-size:.7rem;transition:.2s}}
  .collapsible-head.open::before{{content:"▼"}}
  .collapsible-body{{display:none;background:rgba(0,0,0,.25);border-radius:6px;
    padding:.6rem .7rem;font-size:.76rem;white-space:pre-wrap;margin-top:.3rem;line-height:1.6}}
  .collapsible-body.open{{display:block}}
  .goals-list{{font-size:.8rem;padding-left:1.1rem;margin:.4rem 0}}
  .goals-list li{{margin-bottom:.25rem;opacity:.9}}

  /* ── Hero ── */
  .hero{{background:linear-gradient(135deg,var(--green-d) 0%,var(--green) 55%,var(--green-l) 100%);
    border-radius:14px;padding:2rem 2.2rem 1.6rem;margin-bottom:1.5rem;position:relative;overflow:hidden}}
  .hero::after{{content:"🏫";position:absolute;right:2rem;top:50%;transform:translateY(-50%);font-size:4.5rem;opacity:.17}}
  .hero h1{{font-family:'DM Serif Display','Noto Serif TC',serif;font-size:1.8rem;color:#fff;margin-bottom:.3rem;line-height:1.3}}
  .hero p{{color:#C8E6C9;font-size:.9rem}}

  /* ── Metrics ── */
  .metrics{{display:grid;grid-template-columns:repeat(3,1fr);gap:1rem;margin-bottom:1.2rem}}
  .metric-card{{background:var(--card);border:1.5px solid var(--border);border-radius:10px;
    padding:.9rem 1.1rem;text-align:center}}
  .metric-val{{font-family:'DM Serif Display','Noto Serif TC',serif;font-size:2rem;color:var(--green);font-weight:700}}
  .metric-lbl{{font-size:.8rem;color:var(--muted)}}

  /* ── How it works ── */
  .how-box{{background:var(--card);border:1.5px solid var(--border);border-radius:10px;
    padding:1rem 1.2rem;margin-bottom:1.2rem}}
  .how-box h4{{color:var(--green-d);margin-bottom:.5rem;font-size:.9rem}}
  .how-box ol{{padding-left:1.2rem;font-size:.86rem;color:var(--muted)}}
  .how-box li{{margin-bottom:.25rem}}

  /* ── Stage cards ── */
  .stage-card{{background:var(--card);border:1.5px solid var(--border);border-radius:12px;
    padding:1.3rem 1.6rem;margin-bottom:1rem;box-shadow:0 2px 7px rgba(46,125,50,.06)}}
  .stage-header{{display:flex;align-items:center;gap:.65rem}}
  .stage-badge{{background:var(--green);color:#fff;font-size:.68rem;font-weight:600;
    letter-spacing:.08em;text-transform:uppercase;padding:.22rem .6rem;border-radius:20px}}
  .stage-title{{font-family:'DM Serif Display','Noto Serif TC',serif;font-size:1.2rem;color:var(--green-d)}}
  .think-aloud{{background:linear-gradient(90deg,#FFF8E1,#FFFDE7);border-left:4px solid var(--accent);
    border-radius:0 8px 8px 0;padding:.75rem 1rem;margin:1rem 0;font-size:.86rem;color:#4E342E;line-height:1.7}}
  .divider{{text-align:center;color:var(--muted);font-size:.78rem;letter-spacing:.1em;padding:.5rem 0 .9rem}}
  .divider::before,.divider::after{{content:"";display:inline-block;width:55px;height:1px;
    background:var(--border);vertical-align:middle;margin:0 .65rem}}

  /* ── Textarea ── */
  .ta-label{{font-size:.86rem;font-weight:500;margin-bottom:.35rem;color:var(--text)}}
  textarea{{width:100%;height:180px;border:1.5px solid var(--border);border-radius:8px;
    padding:.6rem .75rem;font-family:'DM Sans','Noto Sans TC',monospace;font-size:.84rem;
    color:var(--text);resize:vertical;outline:none;background:#fff;line-height:1.6}}
  textarea:focus{{border-color:var(--green-l);background:#FAFFFE}}

  /* ── Buttons ── */
  .btn{{background:var(--green);color:#fff;border:none;border-radius:8px;
    padding:.42rem 1.1rem;font-size:.88rem;font-weight:500;cursor:pointer}}
  .btn:hover{{background:var(--green-d)}}
  .btn-row{{display:flex;gap:.7rem;margin:.6rem 0}}
  .btn-ghost{{background:transparent;color:var(--green);border:1.5px solid var(--green);
    border-radius:8px;padding:.4rem 1rem;font-size:.88rem;cursor:pointer}}
  .btn-ghost:hover{{background:#E8F5E9}}

  /* ── Badges ── */
  .badge-grid{{display:flex;flex-wrap:wrap;gap:.45rem;margin-top:.7rem}}
  .badge{{display:inline-flex;align-items:center;gap:.3rem;padding:.25rem .65rem;
    border-radius:20px;font-size:.78rem;font-weight:500}}
  .badge.pass{{background:#E8F5E9;color:var(--green);border:1px solid #A5D6A7}}
  .badge.fail{{background:#FFEBEE;color:var(--fail);border:1px solid #EF9A9A}}
  .score-wrap{{margin:.5rem 0 .25rem}}
  .score-label{{font-size:.78rem;color:var(--muted);margin-bottom:.22rem}}
  .score-bg{{background:#E8F5E9;border-radius:6px;height:9px;overflow:hidden}}
  .score-fill{{height:9px;border-radius:6px;background:linear-gradient(90deg,var(--green-l),var(--green-d))}}

  /* ── Comparison ── */
  .dash-banner{{background:linear-gradient(90deg,#E8F5E9,#F1F8E9);border-radius:9px;
    padding:.85rem 1.2rem;margin-bottom:1rem;border:1px solid #A5D6A7;
    display:flex;align-items:center;gap:1.2rem;font-size:.9rem}}
  .cmp-grid{{display:grid;grid-template-columns:1fr 1fr;gap:1rem;margin-bottom:.5rem}}
  .cmp-col{{background:var(--card);border:1.5px solid var(--border);border-radius:11px;padding:1.2rem}}
  .cmp-col h4{{font-family:'DM Serif Display','Noto Serif TC',serif;font-size:1rem;margin-bottom:.6rem}}
  .naive-col{{border-top:4px solid #EF5350}}
  .guided-col{{border-top:4px solid var(--green)}}
  .big-score{{font-family:'DM Serif Display','Noto Serif TC',serif;font-size:2rem;font-weight:700}}
  .cov-label{{font-size:.78rem;color:#888;margin-bottom:.7rem}}
  .preview-label{{font-size:.8rem;font-weight:600;margin:.6rem 0 .3rem;color:var(--green-d)}}
  .preview-box{{background:#F7F9F7;border:1px solid var(--border);border-radius:7px;
    padding:.55rem .7rem;font-size:.78rem;white-space:pre-wrap;max-height:160px;
    overflow-y:auto;color:#333;line-height:1.55;margin-bottom:.4rem}}
  .analysis-row{{font-size:.8rem;padding:.18rem 0;border-bottom:1px solid #F0F4F0}}
  .breakdown-table{{width:100%;border-collapse:collapse;font-size:.82rem}}
  .breakdown-table th{{background:#E8F5E9;color:var(--green-d);padding:.4rem .6rem;text-align:left;border-bottom:2px solid var(--border)}}
  .breakdown-table td{{padding:.35rem .6rem;border-bottom:1px solid #F0F4F0}}
  .breakdown-table tr:hover td{{background:#F7FFF7}}
  .info-box{{background:#E3F2FD;border:1px solid #90CAF9;border-radius:8px;
    padding:.6rem 1rem;font-size:.84rem;color:#0D47A1;margin:.5rem 0}}
</style>
</head>
<body>
<div class="app-shell">

<!-- ═══ SIDEBAR ═══ -->
<div class="sidebar">
  <button class="lang-btn" onclick="send('lang')">{ S("lang_btn") }</button>

  <h2>{ S("res_hub") }</h2>
  <p>{ S("res_sub") }</p>

  <div class="sb-section">
    <h3>{ S("cl_title") }</h3>
    <p>{ S("cl_desc") }</p>
    <button class="sb-btn" onclick="send('dl_xlsx')">{ S("cl_btn") }</button>
  </div>

  <div class="sb-section">
    <h3>{ S("pdf_title") }</h3>
    <p>{ S("pdf_desc") }</p>
    <button class="sb-btn" onclick="send('dl_pdf')">{ S("pdf_btn") }</button>
  </div>

  <hr>
  <h2>{ S("prompt_ref") }</h2>
  <div class="sb-section">
    <div class="collapsible-head" onclick="toggle(this)">{ S("s1_prompt_lbl") }</div>
    <div class="collapsible-body">{ S("naive_prompt") }</div>
    <div class="collapsible-head" onclick="toggle(this)" style="margin-top:.5rem">{ S("s2_prompt_lbl") }</div>
    <div class="collapsible-body">{ S("guided_prompt") }</div>
  </div>

  <hr>
  <h2>{ S("goals_title") }</h2>
  <ul class="goals-list">{goals_html}</ul>
</div>

<!-- ═══ MAIN ═══ -->
<div class="main">

  <!-- Hero -->
  <div class="hero">
    <h1>{ S("page_title") }</h1>
    <p>{ S("page_subtitle") }</p>
  </div>

  <!-- Metrics -->
  <div class="metrics">
    <div class="metric-card"><div class="metric-val">30</div><div class="metric-lbl">{ S("m_students") }</div></div>
    <div class="metric-card"><div class="metric-val">8</div><div class="metric-lbl">{ S("m_constraints") }</div></div>
    <div class="metric-card"><div class="metric-val">3</div><div class="metric-lbl">{ S("m_stages") }</div></div>
  </div>

  <!-- How it works -->
  <div class="how-box">
    <h4>{ S("how_title") }</h4>
    <ol>{steps_html}</ol>
  </div>

  <!-- ── Stage 1 ── -->
  <div class="stage-card">
    <div class="stage-header">
      <span class="stage-badge">{ S("s1_badge") }</span>
      <span class="stage-title">{ S("s1_title") }</span>
    </div>
  </div>
  <div class="think-aloud">{ S("s1_think") }</div>
  <div class="ta-label">{ S("s1_label") }</div>
  <textarea id="naive_ta" placeholder="{ S('s1_ph') }" oninput="autoSave('naive')">{naive_txt}</textarea>
  <div id="naive_check">{naive_check_html}</div>
  <div class="divider">{ S("s1_div") }</div>

  <!-- ── Stage 2 ── -->
  <div class="stage-card">
    <div class="stage-header">
      <span class="stage-badge">{ S("s2_badge") }</span>
      <span class="stage-title">{ S("s2_title") }</span>
    </div>
  </div>
  <div class="think-aloud">{ S("s2_think") }</div>
  <div class="ta-label">{ S("s2_label") }</div>
  <textarea id="guided_ta" placeholder="{ S('s2_ph') }" oninput="autoSave('guided')">{guided_txt}</textarea>
  <div id="guided_check">{guided_check_html}</div>
  <div class="divider">{ S("s2_div") }</div>

  <!-- ── Stage 3 ── -->
  <div class="stage-card">
    <div class="stage-header">
      <span class="stage-badge">{ S("s3_badge") }</span>
      <span class="stage-title">{ S("s3_title") }</span>
    </div>
  </div>
  <div class="think-aloud">{ S("s3_think") }</div>
  <div class="btn-row">
    <button class="btn" id="run_btn" style="{run_btn_style}" {run_disabled}
      onclick="send('run')">{ S("s3_run") }</button>
    <button class="btn-ghost" onclick="send('reset')">{ S("s3_reset") }</button>
  </div>
  {s3_info_html}

  <!-- ── Comparison (rendered server-side) ── -->
  <div id="comparison">{comparison_html}</div>

  <hr style="border:none;border-top:1px solid #C8E6C9;margin:1.5rem 0">
  <p style="text-align:center;font-size:.75rem;color:#aaa">{ S("footer") }</p>
</div><!-- /main -->
</div><!-- /app-shell -->

<script>
  // ── postMessage bridge to Streamlit ──────────────────────────────────────
  // Debounce timer for textarea auto-save
  let saveTimer = null;

  function send(action, payload) {{
    window.parent.postMessage(
      {{ type: 'streamlit:setComponentValue',
         value: {{ action, payload: payload || null }} }},
      '*'
    );
  }}

  function autoSave(which) {{
    clearTimeout(saveTimer);
    saveTimer = setTimeout(() => {{
      const val = document.getElementById(which + '_ta').value;
      send('save_' + which, val);
    }}, 600);   // 600 ms debounce
  }}

  function toggle(head) {{
    head.classList.toggle('open');
    const body = head.nextElementSibling;
    body.classList.toggle('open');
  }}

  // Restore scroll position after rerun (Streamlit resets iframe scroll)
  if (window.self !== window.top) {{
    window.scrollTo(0, 0);
  }}
</script>
</body>
</html>"""

# ══════════════════════════════════════════════════════════════════════════════
# 6. STREAMLIT ENTRY POINT
#    One components.html() call renders everything.
#    The return value carries the postMessage payload.
# ══════════════════════════════════════════════════════════════════════════════

# Compute approximate height (enough for all content)
PANEL_HEIGHT = 3600

result = components.html(
    build_full_html(),
    height=PANEL_HEIGHT,
    scrolling=True,
)

# ── Handle postMessage events ────────────────────────────────────────────────
if result is not None:
    action  = result.get("action", "")
    payload = result.get("payload")

    if action == "lang":
        st.session_state.lang = "en" if st.session_state.lang == "zh" else "zh"
        st.rerun()

    elif action == "save_naive":
        if payload is not None and payload != st.session_state.naive_text:
            st.session_state.naive_text = str(payload)
            # Don't rerun on every keystroke — let debounce batch it.
            # Only rerun when a constraint keyword crosses a threshold:
            new_check = run_check(st.session_state.naive_text)
            if st.session_state.get("_naive_score") != new_check["score"]:
                st.session_state["_naive_score"] = new_check["score"]
                st.rerun()

    elif action == "save_guided":
        if payload is not None and payload != st.session_state.guided_text:
            st.session_state.guided_text = str(payload)
            new_check = run_check(st.session_state.guided_text)
            if st.session_state.get("_guided_score") != new_check["score"]:
                st.session_state["_guided_score"] = new_check["score"]
                st.rerun()

    elif action == "run":
        st.session_state.show_comparison = True
        st.rerun()

    elif action == "reset":
        for k in ["naive_text","guided_text","show_comparison",
                  "_naive_score","_guided_score"]:
            st.session_state.pop(k, None)
        st.session_state.show_comparison = False
        st.rerun()

    elif action == "dl_xlsx":
        # File downloads can't happen from inside an iframe — show a native
        # Streamlit download button at the very bottom of the page instead.
        st.session_state["_pending_dl"] = "xlsx"
        st.rerun()

    elif action == "dl_pdf":
        st.session_state["_pending_dl"] = "pdf"
        st.rerun()

# ── Fallback download buttons (rendered outside iframe so they work) ─────────
pending = st.session_state.pop("_pending_dl", None)
if pending == "xlsx":
    st.download_button(
        "⬇ Click to download Class_List.xlsx",
        data=gen_xlsx(),
        file_name="Class_List.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="_dl_xlsx_btn",
    )
elif pending == "pdf":
    st.download_button(
        "⬇ Click to download Constraint_Ledger.pdf",
        data=gen_pdf(),
        file_name="Constraint_Ledger.pdf",
        mime="application/pdf",
        key="_dl_pdf_btn",
    )
