"""
Workshop Prototype v2.1 — AI Classroom Management Workshop
Senior Python / Streamlit implementation.
Native Streamlit only — no st.components.v1.html() as primary UI.
"""

import io
import json
import datetime
import pandas as pd
import streamlit as st

# ──────────────────────────────────────────────
# 0. PAGE CONFIG  (must be first Streamlit call)
# ──────────────────────────────────────────────
st.set_page_config(
    layout="wide",
    page_title="AI Seating Workshop",
    page_icon="🏫",
)

# ──────────────────────────────────────────────
# 1. CSS INJECTION  (once, after set_page_config)
# ──────────────────────────────────────────────
st.markdown(
    """
    <style>
    /* Compact top header */
    .block-container { padding-top: 1.2rem; padding-bottom: 1rem; }

    /* Metric card subtle border */
    [data-testid="stMetric"] {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 0.6rem 1rem;
    }

    /* Stage header pill */
    .stage-pill {
        display: inline-block;
        background: #1f4e79;
        color: white;
        border-radius: 20px;
        padding: 4px 16px;
        font-size: 0.85rem;
        margin-bottom: 0.4rem;
    }

    /* Hero card */
    .hero-card {
        background: linear-gradient(135deg, #1f4e79 0%, #2e86c1 100%);
        color: white;
        border-radius: 12px;
        padding: 2rem 2.5rem;
        margin-bottom: 1.5rem;
    }

    /* Constraint checklist header */
    [data-testid="stDataEditor"] { border-radius: 8px; }

    /* Sidebar branding */
    .sidebar-brand { font-size: 1.1rem; font-weight: 700; color: #1f4e79; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ──────────────────────────────────────────────
# 2. TRANSLATIONS
# ──────────────────────────────────────────────
T = {
    "English": {
        # Global
        "app_title": "AI Classroom Management Workshop",
        "lang_label": "Language",
        # Nav
        "nav_items": [
            "0. Workshop Overview",
            "1. Upload Workshop Files",
            "2. Stage 1 — Baseline Submission",
            "3. Stage 2 — Refined Submission",
            "4. Compare Outputs",
            "5. Reflection + Exit Ticket",
        ],
        "nav_header": "Navigation",
        # Sidebar status
        "files_ok": "✓ Files uploaded",
        "files_missing": "⚠ Missing files",
        "s1_saved": "✓ Stage 1 saved",
        "s1_missing": "⚠ Stage 1 pending",
        "s2_saved": "✓ Stage 2 saved",
        "s2_missing": "⚠ Stage 2 pending",
        # Page 0
        "p0_title": "AI Classroom Management Workshop",
        "p0_caption": "Compare naïve vs guided prompting to create better seating plans.",
        "p0_students": "Students",
        "p0_constraints": "Constraints",
        "p0_stages": "Stages",
        "p0_how": "How it works",
        "p0_steps": [
            "**Upload** the three workshop resource files (Class List, Constraint Ledger, Template).",
            "**Stage 1** — Use the baseline (naïve) prompt and paste the AI output.",
            "**Stage 2** — Use the guided prompt and paste the refined AI output.",
            "**Compare** both outputs side-by-side with the manual constraint checklist.",
            "**Reflect** and complete the exit ticket.",
        ],
        "p0_facilitator": "Facilitator Notes",
        "p0_facilitator_body": (
            "Encourage teachers to notice what changes between Stage 1 and Stage 2. "
            "The constraint checklist helps make improvements concrete and measurable. "
            "Allow ~10 min per stage and ~15 min for the comparison discussion."
        ),
        "p0_cta": "Go to Step 1: Upload Workshop Files",
        # Page 1
        "p1_title": "Upload Workshop Files",
        "p1_classlist": "Class List",
        "p1_classlist_up": "Upload Class List",
        "p1_constraints_lbl": "Constraint Ledger",
        "p1_constraints_up": "Upload Constraint Ledger",
        "p1_template": "Seating Plan Template",
        "p1_template_up": "Upload Seating Plan Template",
        "p1_preview": "Preview",
        "p1_all_ok": "✅ All required workshop files uploaded.",
        "p1_missing": "⚠️ Please upload all three required files before continuing.",
        "p1_continue": "Continue to Stage 1 →",
        "p1_download": "Download",
        "p1_meta": "Uploaded: **{name}** ({size} KB)",
        # Page 2
        "p2_title": "Stage 1 — Baseline (Naïve Prompting)",
        "p2_caption": "Use the simple prompt below and submit the AI seating plan output.",
        "p2_prompt_label": "Prompt to use:",
        "p2_tab_paste": "Paste Output",
        "p2_tab_upload": "Upload Document",
        "p2_paste_label": "Paste AI Output (Stage 1)",
        "p2_upload_label": "Upload Stage 1 Output File",
        "p2_preview": "Submission Preview",
        "p2_save": "Save Stage 1 Submission",
        "p2_saved_ok": "Stage 1 submission saved.",
        "p2_download_sub": "Download Stage 1 Submission File",
        # Page 3
        "p3_title": "Stage 2 — Refined (Guided Prompting)",
        "p3_caption": "Use the guided structured prompt below and submit the refined AI output.",
        "p3_paste_label": "Paste AI Output (Stage 2)",
        "p3_upload_label": "Upload Stage 2 Output File",
        "p3_preview": "Submission Preview",
        "p3_save": "Save Stage 2 Submission",
        "p3_saved_ok": "Stage 2 submission saved.",
        "p3_download_sub": "Download Stage 2 Submission File",
        # Page 4
        "p4_title": "Comparison View — Before vs After",
        "p4_caption": "Facilitator-led discussion: review improvements and constraints addressed.",
        "p4_s1_header": "### Stage 1 — Baseline",
        "p4_s2_header": "### Stage 2 — Refined",
        "p4_notes_label": "Facilitator Notes (Key Differences)",
        "p4_checklist_header": "Constraint Checklist (Manual Review)",
        "p4_checklist_tip": (
            "💡 Prompt: Ask teachers which constraints appeared **only** after the guided prompt."
        ),
        "p4_col_constraint": "Constraint",
        "p4_col_s1": "Stage 1 ✓",
        "p4_col_s2": "Stage 2 ✓",
        "p4_col_notes": "Notes",
        "p4_reset_compare": "Reset Comparison Notes",
        "p4_reset_all": "Reset All Workshop Data",
        "p4_soft_reset": "Reset Submissions Only",
        "p4_download_csv": "Download Checklist as CSV",
        "p4_gate_warn": "⚠️ Complete Stage 1 and Stage 2 submissions first.",
        "p4_s1_empty": "_No Stage 1 text submitted._",
        "p4_s2_empty": "_No Stage 2 text submitted._",
        # Page 5
        "p5_title": "Reflection + Exit Ticket",
        "p5_q1": "What changed most between Stage 1 and Stage 2?",
        "p5_q2": "Which constraints did the AI miss initially?",
        "p5_q3": "What prompt-writing rule will you adopt?",
        "p5_rating": "How useful was this activity? (1 = low, 5 = high)",
        "p5_name": "Teacher name (optional)",
        "p5_school": "School (optional)",
        "p5_submit": "Submit Reflection",
        "p5_thanks": "✅ Reflection submitted. Thank you!",
        "p5_download_json": "Download Session Summary (JSON)",
        "p5_not_submitted": "Complete the form above and submit your reflection.",
    },
    "繁體中文": {
        # Global
        "app_title": "AI 教室管理工作坊",
        "lang_label": "語言",
        # Nav
        "nav_items": [
            "0. 工作坊概覽",
            "1. 上傳工作坊檔案",
            "2. 第一階段 — 基線提交",
            "3. 第二階段 — 精煉提交",
            "4. 比較輸出",
            "5. 反思 + 離場問卷",
        ],
        "nav_header": "導覽",
        "files_ok": "✓ 檔案已上傳",
        "files_missing": "⚠ 檔案缺失",
        "s1_saved": "✓ 第一階段已儲存",
        "s1_missing": "⚠ 第一階段待完成",
        "s2_saved": "✓ 第二階段已儲存",
        "s2_missing": "⚠ 第二階段待完成",
        # Page 0
        "p0_title": "AI 教室管理工作坊",
        "p0_caption": "比較樸素提示與引導提示，以創建更優質的座位計劃。",
        "p0_students": "學生人數",
        "p0_constraints": "限制條件",
        "p0_stages": "階段",
        "p0_how": "運作方式",
        "p0_steps": [
            "**上傳**三個工作坊資源檔案（學生名單、限制條件表、座位計劃模板）。",
            "**第一階段** — 使用基線（樸素）提示，並貼上 AI 輸出結果。",
            "**第二階段** — 使用引導式提示，並貼上優化後的 AI 輸出結果。",
            "**比較**兩個輸出結果，並使用手動限制條件核對清單進行對比。",
            "**反思**並完成離場問卷。",
        ],
        "p0_facilitator": "主持人備註",
        "p0_facilitator_body": (
            "鼓勵教師注意第一階段和第二階段之間的變化。"
            "限制條件核對清單有助於將改進之處具體化和可量化。"
            "每個階段大約需要 10 分鐘，比較討論大約需要 15 分鐘。"
        ),
        "p0_cta": "前往步驟 1：上傳工作坊檔案",
        # Page 1
        "p1_title": "上傳工作坊檔案",
        "p1_classlist": "學生名單",
        "p1_classlist_up": "上傳學生名單",
        "p1_constraints_lbl": "限制條件表",
        "p1_constraints_up": "上傳限制條件表",
        "p1_template": "座位計劃模板",
        "p1_template_up": "上傳座位計劃模板",
        "p1_preview": "預覽",
        "p1_all_ok": "✅ 所有必要工作坊檔案已上傳。",
        "p1_missing": "⚠️ 請上傳所有三個必要檔案後再繼續。",
        "p1_continue": "繼續至第一階段 →",
        "p1_download": "下載",
        "p1_meta": "已上傳：**{name}** ({size} KB)",
        # Page 2
        "p2_title": "第一階段 — 基線（樸素提示）",
        "p2_caption": "使用下方簡單提示，並提交 AI 座位計劃輸出結果。",
        "p2_prompt_label": "使用的提示：",
        "p2_tab_paste": "貼上輸出",
        "p2_tab_upload": "上傳文件",
        "p2_paste_label": "貼上 AI 輸出（第一階段）",
        "p2_upload_label": "上傳第一階段輸出檔案",
        "p2_preview": "提交預覽",
        "p2_save": "儲存第一階段提交",
        "p2_saved_ok": "第一階段提交已儲存。",
        "p2_download_sub": "下載第一階段提交檔案",
        # Page 3
        "p3_title": "第二階段 — 精煉（引導式提示）",
        "p3_caption": "使用下方引導式結構化提示，並提交優化後的 AI 輸出結果。",
        "p3_paste_label": "貼上 AI 輸出（第二階段）",
        "p3_upload_label": "上傳第二階段輸出檔案",
        "p3_preview": "提交預覽",
        "p3_save": "儲存第二階段提交",
        "p3_saved_ok": "第二階段提交已儲存。",
        "p3_download_sub": "下載第二階段提交檔案",
        # Page 4
        "p4_title": "比較視圖 — 前後對比",
        "p4_caption": "主持人引導討論：審查改進之處及已解決的限制條件。",
        "p4_s1_header": "### 第一階段 — 基線",
        "p4_s2_header": "### 第二階段 — 精煉",
        "p4_notes_label": "主持人備註（主要差異）",
        "p4_checklist_header": "限制條件核對清單（手動審查）",
        "p4_checklist_tip": "💡 提示：詢問教師哪些限制條件**僅在**引導式提示後才出現。",
        "p4_col_constraint": "限制條件",
        "p4_col_s1": "第一階段 ✓",
        "p4_col_s2": "第二階段 ✓",
        "p4_col_notes": "備註",
        "p4_reset_compare": "重置比較備註",
        "p4_reset_all": "重置所有工作坊資料",
        "p4_soft_reset": "僅重置提交內容",
        "p4_download_csv": "下載核對清單為 CSV",
        "p4_gate_warn": "⚠️ 請先完成第一階段和第二階段的提交。",
        "p4_s1_empty": "_未提交第一階段文字。_",
        "p4_s2_empty": "_未提交第二階段文字。_",
        # Page 5
        "p5_title": "反思 + 離場問卷",
        "p5_q1": "第一階段和第二階段之間最大的變化是什麼？",
        "p5_q2": "AI 最初遺漏了哪些限制條件？",
        "p5_q3": "您將採用什麼提示撰寫規則？",
        "p5_rating": "此活動的實用性如何？（1 = 低，5 = 高）",
        "p5_name": "教師姓名（選填）",
        "p5_school": "學校（選填）",
        "p5_submit": "提交反思",
        "p5_thanks": "✅ 反思已提交。謝謝！",
        "p5_download_json": "下載工作坊摘要（JSON）",
        "p5_not_submitted": "請完成上方表格並提交您的反思。",
    },
}

# ──────────────────────────────────────────────
# 3. PROMPTS
# ──────────────────────────────────────────────
NAIVE_PROMPT = {
    "English": """\
Create a seating plan for my class of 30 students.
""",
    "繁體中文": """\
為我的 30 名學生班級制定座位計劃。
""",
}

GUIDED_PROMPT = {
    "English": """\
You are an expert classroom management assistant.

Task: Generate a detailed seating plan for a class of 30 students.

Requirements:
1. Use the attached Class List which includes student names, learning needs, and
   any flagged behaviours.
2. Strictly respect ALL constraints listed in the Constraint Ledger:
   - Separate students with recorded conflicts.
   - Place students with visual/hearing impairments near the front.
   - Distribute high-engagement students evenly across rows.
   - Keep EAL (English as Additional Language) students near a bilingual peer.
   - Honour any teacher-specific notes per student.
   - Ensure no two students on a behaviour plan sit adjacent.
   - Place students who require frequent teacher support in accessible seats.
   - Maintain gender balance per table group where possible.
3. Output format: a grid table (rows × columns) with student names in each cell.
4. After the grid, provide a brief justification (2–3 sentences) for any
   non-obvious placement decision.
5. Flag any constraint that could NOT be satisfied and explain why.
""",
    "繁體中文": """\
您是一位專業的教室管理助理。

任務：為 30 名學生的班級生成詳細的座位計劃。

要求：
1. 使用附帶的學生名單，其中包括學生姓名、學習需求和任何標記的行為。
2. 嚴格遵守限制條件表中列出的所有限制條件：
   - 分開有記錄衝突的學生。
   - 將有視力/聽力障礙的學生安排在前排。
   - 將高參與度學生均勻分佈在各排。
   - 將英語作為附加語言（EAL）的學生安排在雙語同伴附近。
   - 遵守每位學生的教師特定備註。
   - 確保沒有兩名有行為計劃的學生相鄰而坐。
   - 將需要頻繁教師支持的學生安排在易於到達的座位。
   - 盡可能在每個桌組保持性別平衡。
3. 輸出格式：帶有每個格子中學生姓名的網格表（行 × 列）。
4. 在網格之後，為任何非顯而易見的安排決定提供簡短的理由（2-3 句話）。
5. 標記任何無法滿足的限制條件並解釋原因。
""",
}

# Default constraint list (8 items)
DEFAULT_CONSTRAINTS = [
    "Separate students with recorded conflicts",
    "Visual/hearing impairments near front",
    "High-engagement students distributed evenly",
    "EAL students near bilingual peer",
    "Teacher-specific notes honoured",
    "No two behaviour-plan students adjacent",
    "Students needing support in accessible seats",
    "Gender balance per table group",
]

DEFAULT_CONSTRAINTS_ZH = [
    "分開有記錄衝突的學生",
    "視力/聽力障礙學生靠近前排",
    "高參與度學生均勻分佈",
    "EAL 學生靠近雙語同伴",
    "遵守教師特定備註",
    "無兩名有行為計劃的學生相鄰",
    "需要支持的學生坐在易到達的座位",
    "每個桌組盡量保持性別平衡",
]

# ──────────────────────────────────────────────
# 4. SESSION STATE INITIALISATION
# ──────────────────────────────────────────────

def init_session_state() -> None:
    defaults: dict = {
        "lang": "English",
        "nav_step": 0,
        # Workshop files
        "workshop_files": {
            "class_list": None,
            "constraint_ledger": None,
            "template": None,
        },
        # Stage submissions
        "stage1_text": "",
        "stage1_file": None,
        "stage2_text": "",
        "stage2_file": None,
        "stage1_saved": False,
        "stage2_saved": False,
        # Comparison
        "comparison_notes": "",
        "constraint_checklist": None,   # will hold edited df as records
        # Reflection
        "ref_q1": "",
        "ref_q2": "",
        "ref_q3": "",
        "ref_rating": 3,
        "ref_name": "",
        "ref_school": "",
        "reflection_submitted": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def soft_reset() -> None:
    """Clear stage submissions, comparison, reflection — keep workshop files."""
    keys_to_clear = [
        "stage1_text", "stage1_file", "stage2_text", "stage2_file",
        "stage1_saved", "stage2_saved",
        "comparison_notes", "constraint_checklist",
        "ref_q1", "ref_q2", "ref_q3", "ref_rating",
        "ref_name", "ref_school", "reflection_submitted",
    ]
    for k in keys_to_clear:
        if k in ("stage1_text", "stage2_text", "comparison_notes",
                 "ref_q1", "ref_q2", "ref_q3", "ref_name", "ref_school"):
            st.session_state[k] = ""
        elif k in ("ref_rating",):
            st.session_state[k] = 3
        elif k in ("stage1_saved", "stage2_saved", "reflection_submitted"):
            st.session_state[k] = False
        else:
            st.session_state[k] = None


def hard_reset() -> None:
    """Clear everything except lang."""
    lang = st.session_state.get("lang", "English")
    keys_to_keep = {"lang"}
    for k in list(st.session_state.keys()):
        if k not in keys_to_keep:
            del st.session_state[k]
    st.session_state["lang"] = lang
    init_session_state()


# ──────────────────────────────────────────────
# 5. HELPERS
# ──────────────────────────────────────────────

def t(key: str) -> str:
    """Shorthand translation lookup."""
    lang = st.session_state.get("lang", "English")
    return T[lang].get(key, key)


def all_files_uploaded() -> bool:
    wf = st.session_state.workshop_files
    return all(wf[k] is not None for k in ("class_list", "constraint_ledger", "template"))


def file_bytes(file_dict: dict | None) -> bytes | None:
    if file_dict:
        return file_dict.get("bytes")
    return None


def build_constraint_df() -> pd.DataFrame:
    lang = st.session_state.get("lang", "English")
    constraints = DEFAULT_CONSTRAINTS if lang == "English" else DEFAULT_CONSTRAINTS_ZH
    return pd.DataFrame(
        {
            t("p4_col_constraint"): constraints,
            t("p4_col_s1"): [False] * len(constraints),
            t("p4_col_s2"): [False] * len(constraints),
            t("p4_col_notes"): [""] * len(constraints),
        }
    )


def session_summary() -> str:
    """Serialise session state to JSON (bytes-safe)."""
    safe: dict = {}
    for k, v in st.session_state.items():
        if isinstance(v, dict) and "bytes" in str(type(list(v.values())[0]) if v else ""):
            # workshop_files contain bytes — just store metadata
            safe[k] = {
                sub_k: (
                    {"filename": sub_v["filename"], "mime": sub_v["mime"],
                     "size_bytes": len(sub_v["bytes"])}
                    if sub_v and isinstance(sub_v, dict) and "bytes" in sub_v
                    else sub_v
                )
                for sub_k, sub_v in v.items()
            }
        elif isinstance(v, bytes):
            safe[k] = f"<bytes len={len(v)}>"
        elif isinstance(v, pd.DataFrame):
            safe[k] = v.to_dict(orient="records")
        else:
            safe[k] = v
    return json.dumps(safe, ensure_ascii=False, indent=2, default=str)


def store_uploaded_file(uploaded, slot_key: str) -> None:
    """Store a Streamlit UploadedFile into workshop_files."""
    if uploaded is not None:
        st.session_state.workshop_files[slot_key] = {
            "filename": uploaded.name,
            "bytes": uploaded.getvalue(),
            "mime": uploaded.type,
        }


# ──────────────────────────────────────────────
# 6. TOP BAR  (language toggle)
# ──────────────────────────────────────────────

def render_top_bar() -> None:
    col_title, col_spacer, col_lang = st.columns([7, 2, 1])
    with col_title:
        st.markdown(f"### 🏫 {t('app_title')}")
    with col_lang:
        chosen = st.radio(
            t("lang_label"),
            options=["English", "繁體中文"],
            index=0 if st.session_state.lang == "English" else 1,
            horizontal=True,
            key="_lang_radio",
            label_visibility="collapsed",
        )
        if chosen != st.session_state.lang:
            st.session_state.lang = chosen
            st.rerun()


# ──────────────────────────────────────────────
# 7. SIDEBAR
# ──────────────────────────────────────────────

def render_sidebar() -> None:
    with st.sidebar:
        st.markdown('<p class="sidebar-brand">EduLearn Institute</p>', unsafe_allow_html=True)
        st.divider()

        nav_labels = t("nav_items")
        current = st.session_state.nav_step

        selected = st.radio(
            t("nav_header"),
            options=list(range(len(nav_labels))),
            format_func=lambda i: nav_labels[i],
            index=current,
            key="nav_step_radio",
        )
        if selected != st.session_state.nav_step:
            st.session_state.nav_step = selected
            st.rerun()

        st.divider()
        st.markdown("**Status**")

        if all_files_uploaded():
            st.success(t("files_ok"))
        else:
            st.warning(t("files_missing"))

        if st.session_state.stage1_saved:
            st.success(t("s1_saved"))
        else:
            st.warning(t("s1_missing"))

        if st.session_state.stage2_saved:
            st.success(t("s2_saved"))
        else:
            st.warning(t("s2_missing"))

        # Progress bar  (0–5 steps)
        progress = 0
        if all_files_uploaded():
            progress += 1
        if st.session_state.stage1_saved:
            progress += 1
        if st.session_state.stage2_saved:
            progress += 1
        if st.session_state.comparison_notes:
            progress += 1
        if st.session_state.reflection_submitted:
            progress += 1
        st.progress(progress / 5, text=f"{progress}/5 complete")


# ──────────────────────────────────────────────
# 8. PAGE 0 — WORKSHOP OVERVIEW
# ──────────────────────────────────────────────

def page_overview() -> None:
    lang = st.session_state.lang

    st.markdown(
        f"""
        <div class="hero-card">
            <h2 style="margin:0; color:white;">{t("p0_title")}</h2>
            <p style="margin-top:0.4rem; opacity:0.9;">{t("p0_caption")}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    c1, c2, c3 = st.columns(3)
    c1.metric(t("p0_students"), "30")
    c2.metric(t("p0_constraints"), "8")
    c3.metric(t("p0_stages"), "2 + Compare")

    st.subheader(t("p0_how"))
    for step in t("p0_steps"):
        st.markdown(f"- {step}")

    with st.expander(t("p0_facilitator")):
        st.markdown(t("p0_facilitator_body"))

    st.markdown("")
    if st.button(t("p0_cta"), key="go_step_1", type="primary"):
        st.session_state.nav_step = 1
        st.rerun()


# ──────────────────────────────────────────────
# 9. PAGE 1 — UPLOAD WORKSHOP FILES
# ──────────────────────────────────────────────

def page_upload() -> None:
    st.subheader(t("p1_title"))

    # ── Upload cards ──────────────────────────
    col_cl, col_ct, col_tp = st.columns(3)

    with col_cl:
        with st.container(border=True):
            st.subheader(t("p1_classlist"))
            up_cl = st.file_uploader(
                t("p1_classlist_up"),
                type=["xlsx", "csv", "pdf"],
                key="upload_classlist",
            )
            if up_cl:
                store_uploaded_file(up_cl, "class_list")
                st.success(t("p1_meta").format(
                    name=up_cl.name, size=round(len(up_cl.getvalue()) / 1024, 1)
                ))

    with col_ct:
        with st.container(border=True):
            st.subheader(t("p1_constraints_lbl"))
            up_ct = st.file_uploader(
                t("p1_constraints_up"),
                type=["pdf", "docx", "txt"],
                key="upload_constraints",
            )
            if up_ct:
                store_uploaded_file(up_ct, "constraint_ledger")
                st.success(t("p1_meta").format(
                    name=up_ct.name, size=round(len(up_ct.getvalue()) / 1024, 1)
                ))

    with col_tp:
        with st.container(border=True):
            st.subheader(t("p1_template"))
            up_tp = st.file_uploader(
                t("p1_template_up"),
                type=["xlsx", "docx", "pdf"],
                key="upload_template",
            )
            if up_tp:
                store_uploaded_file(up_tp, "template")
                st.success(t("p1_meta").format(
                    name=up_tp.name, size=round(len(up_tp.getvalue()) / 1024, 1)
                ))

    # ── Preview ──────────────────────────────
    st.divider()
    st.subheader(t("p1_preview"))

    wf = st.session_state.workshop_files
    tab_cl, tab_ct, tab_tp = st.tabs(
        [t("p1_classlist"), t("p1_constraints_lbl"), t("p1_template")]
    )

    with tab_cl:
        _preview_file(wf["class_list"], tabular_types=["xlsx", "csv"])

    with tab_ct:
        _preview_file(wf["constraint_ledger"], tabular_types=[])

    with tab_tp:
        _preview_file(wf["template"], tabular_types=["xlsx"])

    # ── Download buttons ──────────────────────
    st.divider()
    dl_col1, dl_col2, dl_col3 = st.columns(3)

    for col, slot_key, label in [
        (dl_col1, "class_list", t("p1_classlist")),
        (dl_col2, "constraint_ledger", t("p1_constraints_lbl")),
        (dl_col3, "template", t("p1_template")),
    ]:
        fd = wf[slot_key]
        with col:
            if fd:
                st.download_button(
                    f"{t('p1_download')} {label}",
                    data=fd["bytes"],
                    file_name=fd["filename"],
                    mime=fd["mime"],
                    key=f"dl_{slot_key}",
                )
            else:
                st.button(f"{t('p1_download')} {label}", disabled=True, key=f"dl_{slot_key}_dis")

    # ── Completion indicator + CTA ────────────
    st.divider()
    if all_files_uploaded():
        st.success(t("p1_all_ok"))
        if st.button(t("p1_continue"), key="btn_to_stage1", type="primary"):
            st.session_state.nav_step = 2
            st.rerun()
    else:
        st.warning(t("p1_missing"))


def _preview_file(fd: dict | None, tabular_types: list[str]) -> None:
    """Render a preview for a stored file dict."""
    if fd is None:
        st.info("No file uploaded yet.")
        return

    ext = fd["filename"].rsplit(".", 1)[-1].lower()
    size_kb = round(len(fd["bytes"]) / 1024, 1)
    st.info(f"📄 **{fd['filename']}** — {size_kb} KB")

    if ext in tabular_types:
        try:
            raw = io.BytesIO(fd["bytes"])
            df = pd.read_excel(raw) if ext == "xlsx" else pd.read_csv(raw)
            st.dataframe(df.head(15), use_container_width=True)
        except Exception as exc:
            st.warning(f"Could not parse as table: {exc}")
    elif ext == "txt":
        try:
            text = fd["bytes"].decode("utf-8", errors="replace")
            st.text(text[:2000])
        except Exception:
            pass


# ──────────────────────────────────────────────
# 10. STAGE SUBMISSION (shared logic for p2 & p3)
# ──────────────────────────────────────────────

def page_stage(stage: int) -> None:
    lang = st.session_state.lang
    assert stage in (1, 2)

    if stage == 1:
        title = t("p2_title")
        caption = t("p2_caption")
        prompt_text = NAIVE_PROMPT[lang]
        tab_paste_label = t("p2_tab_paste")
        tab_upload_label = t("p2_tab_upload")
        paste_label = t("p2_paste_label")
        upload_label = t("p2_upload_label")
        preview_header = t("p2_preview")
        save_btn = t("p2_save")
        saved_ok = t("p2_saved_ok")
        download_label = t("p2_download_sub")
        text_key = "stage1_text"
        file_key = "stage1_file"
        saved_key = "stage1_saved"
    else:
        title = t("p3_title")
        caption = t("p3_caption")
        prompt_text = GUIDED_PROMPT[lang]
        tab_paste_label = t("p2_tab_paste")
        tab_upload_label = t("p2_tab_upload")
        paste_label = t("p3_paste_label")
        upload_label = t("p3_upload_label")
        preview_header = t("p3_preview")
        save_btn = t("p3_save")
        saved_ok = t("p3_saved_ok")
        download_label = t("p3_download_sub")
        text_key = "stage2_text"
        file_key = "stage2_file"
        saved_key = "stage2_saved"

    # Header
    st.markdown(f'<span class="stage-pill">Stage {stage}</span>', unsafe_allow_html=True)
    st.subheader(title)
    st.caption(caption)

    # Prompt display card
    with st.container(border=True):
        st.markdown(f"**{t('p2_prompt_label') if stage == 1 else t('p2_prompt_label')}**")
        st.code(prompt_text, language="markdown")

    st.divider()

    # Submission tabs
    tab_paste, tab_upload = st.tabs([tab_paste_label, tab_upload_label])

    with tab_paste:
        user_text = st.text_area(
            paste_label,
            value=st.session_state[text_key],
            height=260,
            key=f"_ta_stage{stage}",
        )
        # Sync back without triggering rerun on every keystroke
        st.session_state[text_key] = user_text

    with tab_upload:
        up_doc = st.file_uploader(
            upload_label,
            type=["pdf", "docx", "xlsx", "txt"],
            key=f"_up_stage{stage}",
        )
        if up_doc:
            st.session_state[file_key] = {
                "filename": up_doc.name,
                "bytes": up_doc.getvalue(),
                "mime": up_doc.type,
            }
            st.success(f"📎 {up_doc.name}")

    # Preview
    st.subheader(preview_header)
    text_val = st.session_state[text_key]
    file_val = st.session_state[file_key]

    if text_val:
        with st.expander("Text preview", expanded=True):
            st.markdown(text_val[:4000])

    if file_val:
        st.download_button(
            download_label,
            data=file_val["bytes"],
            file_name=file_val["filename"],
            mime=file_val["mime"],
            key=f"dl_stage{stage}_file",
        )

    if not text_val and not file_val:
        st.info("No submission yet.")

    # Save button
    st.divider()
    col_save, col_status = st.columns([2, 5])
    with col_save:
        if st.button(save_btn, key=f"save_stage{stage}", type="primary"):
            st.session_state[saved_key] = True
            st.session_state[f"stage{stage}_saved_ts"] = datetime.datetime.now().strftime(
                "%Y-%m-%d %H:%M"
            )
    with col_status:
        if st.session_state[saved_key]:
            ts = st.session_state.get(f"stage{stage}_saved_ts", "")
            st.success(f"✅ {saved_ok}" + (f"  _{ts}_" if ts else ""))

    # Navigation shortcut
    if st.session_state[saved_key]:
        next_step = stage + 1 if stage < 5 else 5
        if st.button(
            f"Continue to Step {next_step} →",
            key=f"continue_stage{stage}",
        ):
            st.session_state.nav_step = next_step
            st.rerun()


# ──────────────────────────────────────────────
# 11. PAGE 4 — COMPARE OUTPUTS
# ──────────────────────────────────────────────

def page_compare() -> None:
    # Gate
    if not st.session_state.stage1_saved or not st.session_state.stage2_saved:
        st.warning(t("p4_gate_warn"))
        st.stop()

    st.subheader(t("p4_title"))
    st.caption(t("p4_caption"))

    # Side-by-side text
    col_l, col_r = st.columns(2)

    with col_l:
        st.markdown(t("p4_s1_header"))
        with st.container(border=True):
            text1 = st.session_state.stage1_text
            if text1:
                st.markdown(text1[:4000])
            else:
                st.markdown(t("p4_s1_empty"))
        fd1 = st.session_state.stage1_file
        if fd1:
            st.download_button(
                "⬇ Stage 1 File",
                data=fd1["bytes"],
                file_name=fd1["filename"],
                mime=fd1["mime"],
                key="compare_dl_s1",
            )

    with col_r:
        st.markdown(t("p4_s2_header"))
        with st.container(border=True):
            text2 = st.session_state.stage2_text
            if text2:
                st.markdown(text2[:4000])
            else:
                st.markdown(t("p4_s2_empty"))
        fd2 = st.session_state.stage2_file
        if fd2:
            st.download_button(
                "⬇ Stage 2 File",
                data=fd2["bytes"],
                file_name=fd2["filename"],
                mime=fd2["mime"],
                key="compare_dl_s2",
            )

    st.divider()

    # Facilitator notes
    notes = st.text_area(
        t("p4_notes_label"),
        value=st.session_state.comparison_notes,
        height=150,
        key="_compare_notes_ta",
    )
    st.session_state.comparison_notes = notes

    st.divider()

    # Constraint checklist
    st.subheader(t("p4_checklist_header"))
    st.info(t("p4_checklist_tip"))

    # Build or reuse existing df
    if st.session_state.constraint_checklist is None:
        df_check = build_constraint_df()
    else:
        df_check = pd.DataFrame(st.session_state.constraint_checklist)
        # Re-label columns if language changed
        expected_cols = [
            t("p4_col_constraint"), t("p4_col_s1"), t("p4_col_s2"), t("p4_col_notes")
        ]
        if list(df_check.columns) != expected_cols:
            df_check = build_constraint_df()

    edited_df = st.data_editor(
        df_check,
        num_rows="fixed",
        use_container_width=True,
        key="_constraint_editor",
        column_config={
            t("p4_col_s1"): st.column_config.CheckboxColumn(t("p4_col_s1")),
            t("p4_col_s2"): st.column_config.CheckboxColumn(t("p4_col_s2")),
        },
    )
    # Persist
    st.session_state.constraint_checklist = edited_df.to_dict(orient="records")

    # Action buttons row
    st.divider()
    btn_c1, btn_c2, btn_c3, _ = st.columns([2, 2, 2, 4])

    with btn_c1:
        if st.button(t("p4_reset_compare"), key="reset_compare"):
            st.session_state.comparison_notes = ""
            st.session_state.constraint_checklist = None
            st.rerun()

    with btn_c2:
        if st.button(t("p4_soft_reset"), key="btn_soft_reset"):
            soft_reset()
            st.session_state.nav_step = 2
            st.rerun()

    with btn_c3:
        if st.button(t("p4_reset_all"), key="reset_all", type="secondary"):
            hard_reset()
            st.session_state.nav_step = 0
            st.rerun()

    # CSV download
    csv_bytes = edited_df.to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        t("p4_download_csv"),
        data=csv_bytes,
        file_name="constraint_checklist.csv",
        mime="text/csv",
        key="dl_checklist_csv",
    )

    # Navigation
    if st.button("Continue to Reflection →", key="continue_compare"):
        st.session_state.nav_step = 5
        st.rerun()


# ──────────────────────────────────────────────
# 12. PAGE 5 — REFLECTION + EXIT TICKET
# ──────────────────────────────────────────────

def page_reflection() -> None:
    st.subheader(t("p5_title"))

    if not st.session_state.reflection_submitted:
        with st.form("reflection_form"):
            q1 = st.text_area(t("p5_q1"), value=st.session_state.ref_q1, key="ref_q1_f")
            q2 = st.text_area(t("p5_q2"), value=st.session_state.ref_q2, key="ref_q2_f")
            q3 = st.text_area(t("p5_q3"), value=st.session_state.ref_q3, key="ref_q3_f")
            rating = st.slider(
                t("p5_rating"), 1, 5,
                value=st.session_state.ref_rating,
                key="ref_rating_f",
            )
            name = st.text_input(t("p5_name"), value=st.session_state.ref_name, key="ref_name_f")
            school = st.text_input(t("p5_school"), value=st.session_state.ref_school, key="ref_school_f")

            submitted = st.form_submit_button(t("p5_submit"), type="primary")

        if submitted:
            st.session_state.ref_q1 = q1
            st.session_state.ref_q2 = q2
            st.session_state.ref_q3 = q3
            st.session_state.ref_rating = rating
            st.session_state.ref_name = name
            st.session_state.ref_school = school
            st.session_state.reflection_submitted = True
            st.rerun()
    else:
        st.success(t("p5_thanks"))

        # Summary display
        with st.expander("View submitted reflection", expanded=True):
            st.markdown(f"**{t('p5_q1')}**")
            st.markdown(st.session_state.ref_q1 or "_—_")
            st.markdown(f"**{t('p5_q2')}**")
            st.markdown(st.session_state.ref_q2 or "_—_")
            st.markdown(f"**{t('p5_q3')}**")
            st.markdown(st.session_state.ref_q3 or "_—_")
            st.markdown(f"**{t('p5_rating')}:** {st.session_state.ref_rating}/5")
            if st.session_state.ref_name:
                st.markdown(f"**{t('p5_name')}:** {st.session_state.ref_name}")
            if st.session_state.ref_school:
                st.markdown(f"**{t('p5_school')}:** {st.session_state.ref_school}")

        # JSON export
        summary_json = session_summary()
        st.download_button(
            t("p5_download_json"),
            data=summary_json.encode("utf-8"),
            file_name="workshop_session.json",
            mime="application/json",
            key="dl_session_json",
        )

        # Allow re-edit
        if st.button("Edit reflection", key="re_edit_reflection"):
            st.session_state.reflection_submitted = False
            st.rerun()


# ──────────────────────────────────────────────
# 13. MAIN ROUTER
# ──────────────────────────────────────────────

def main() -> None:
    init_session_state()
    render_top_bar()
    render_sidebar()

    step = st.session_state.nav_step

    if step == 0:
        page_overview()
    elif step == 1:
        page_upload()
    elif step == 2:
        page_stage(1)
    elif step == 3:
        page_stage(2)
    elif step == 4:
        page_compare()
    elif step == 5:
        page_reflection()
    else:
        st.error("Unknown step.")


if __name__ == "__main__":
    main()
