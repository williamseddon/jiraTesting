import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import requests
from PIL import Image
from io import BytesIO

# ── OpenAI (graceful fallback if missing) ─────────────────────────────────────
try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

def get_openai_client():
    if not OPENAI_AVAILABLE:
        return None
    try:
        key = st.secrets.get("OPENAI_API_KEY", "")
        return OpenAI(api_key=key) if key else None
    except:
        return None

# ══════════════════════════════════════════════════════════════════════════════
#  PAGE CONFIG
# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="SharkNinja Jira Dashboard",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background:#F0F2F5; }
  [data-testid="stSidebar"] { background:#0052CC; }
  [data-testid="stSidebar"] * { color:white !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stTextInput label,
  [data-testid="stSidebar"] .stRadio label {
    color:#B3D4FF !important; font-size:11px; font-weight:700;
    text-transform:uppercase; letter-spacing:0.6px;
  }
  [data-testid="stSidebar"] hr { border-color:rgba(255,255,255,0.2) !important; }
  [data-testid="metric-container"] {
    background:white; border-radius:6px; padding:16px 20px;
    border:1px solid #DFE1E6; border-left:4px solid #0052CC;
    box-shadow:0 1px 3px rgba(0,0,0,0.06);
  }
  [data-testid="stMetricValue"] { color:#172B4D; font-size:26px; font-weight:700; }
  [data-testid="stMetricLabel"] { color:#5E6C84; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; }

  .card { background:white; border-radius:6px; border:1px solid #DFE1E6; padding:16px; margin-bottom:12px; box-shadow:0 1px 3px rgba(0,0,0,0.04); }

  .top-bar {
    background:linear-gradient(135deg,#0052CC 0%,#0065FF 100%);
    padding:14px 24px; border-radius:8px; margin-bottom:16px;
    display:flex; align-items:center; justify-content:space-between;
    box-shadow:0 2px 8px rgba(0,82,204,0.25);
  }
  .top-bar-left { display:flex; align-items:center; gap:14px; }
  .top-bar h1 { color:white; margin:0; font-size:20px; font-weight:700; }
  .top-bar .subtitle { color:#B3D4FF; font-size:12px; margin:2px 0 0 0; }
  .top-bar-badge { background:rgba(255,255,255,0.2); color:white; border-radius:20px; padding:4px 14px; font-size:13px; font-weight:600; }

  .section-header {
    font-size:11px; font-weight:700; color:#5E6C84;
    text-transform:uppercase; letter-spacing:0.8px;
    margin:20px 0 10px 0; padding-bottom:6px; border-bottom:2px solid #0052CC;
  }

  .badge { display:inline-block; padding:3px 9px; border-radius:3px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.4px; }
  .badge-new      { background:#DFE1E6; color:#42526E; }
  .badge-progress { background:#DEEBFF; color:#0052CC; }
  .badge-verify   { background:#EAE6FF; color:#403294; }
  .badge-rcca     { background:#FFF0B3; color:#7A5200; }
  .badge-hold     { background:#FFEBE6; color:#BF2600; }
  .badge-done     { background:#E3FCEF; color:#006644; }
  .badge-close    { background:#E3FCEF; color:#006644; }
  .badge-rtc      { background:#E3FCEF; color:#006644; }

  .detail-header { font-size:20px; font-weight:700; color:#172B4D; margin-bottom:10px; line-height:1.4; }
  .detail-meta-table { width:100%; font-size:13px; border-collapse:collapse; }
  .detail-meta-table tr { border-bottom:1px solid #F4F5F7; }
  .detail-meta-table td { padding:7px 4px; vertical-align:top; }
  .detail-meta-label { color:#6B778C; font-weight:600; font-size:12px; width:110px; }
  .detail-section-title { font-size:11px; font-weight:700; color:#6B778C; text-transform:uppercase; letter-spacing:0.6px; margin:14px 0 8px 0; padding-bottom:4px; border-bottom:1px solid #DFE1E6; }
  .breadcrumb { font-size:12px; color:#6B778C; margin-bottom:12px; display:flex; align-items:center; gap:6px; }
  .breadcrumb .sep { color:#97A0AF; }

  .desc-box { background:#F4F5F7; border-radius:4px; border:1px solid #DFE1E6; padding:14px; font-size:13px; color:#172B4D; line-height:1.7; white-space:pre-wrap; word-break:break-word; max-height:320px; overflow-y:auto; }
  .field-box { background:#F4F5F7; border-radius:4px; border-left:3px solid #DFE1E6; padding:10px 14px; font-size:13px; color:#172B4D; line-height:1.6; white-space:pre-wrap; word-break:break-word; margin-bottom:10px; }
  .field-box.expected { border-left-color:#36B37E; }
  .field-box.actual   { border-left-color:#FF5630; }
  .field-box.trigger  { border-left-color:#0052CC; }

  .rcca-step { background:#F8F9FA; border:1px solid #DFE1E6; border-radius:4px; padding:10px 14px; margin-bottom:6px; }
  .rcca-step-label { font-size:10px; font-weight:700; color:#0052CC; text-transform:uppercase; letter-spacing:0.6px; margin-bottom:5px; }
  .rcca-step-value { font-size:13px; color:#172B4D; line-height:1.6; white-space:pre-wrap; word-break:break-word; }

  .comment-bubble { background:#F8F9FA; border:1px solid #DFE1E6; border-radius:6px; padding:12px 14px; margin-bottom:10px; }
  .comment-avatar { width:28px; height:28px; border-radius:50%; background:#0052CC; color:white; font-size:11px; font-weight:700; display:inline-flex; align-items:center; justify-content:center; flex-shrink:0; }
  .comment-author { font-weight:600; font-size:13px; color:#172B4D; }
  .comment-date   { font-size:11px; color:#6B778C; }
  .comment-body   { font-size:13px; color:#344563; line-height:1.65; white-space:pre-wrap; word-break:break-word; margin-top:6px; }

  .attach-chip { display:inline-flex; align-items:center; gap:6px; background:#F4F5F7; border:1px solid #DFE1E6; border-radius:4px; padding:6px 12px; margin:3px; font-size:12px; color:#172B4D; text-decoration:none; font-weight:500; }
  .attach-chip:hover { background:#DEEBFF; border-color:#B3D4FF; color:#0052CC; }

  .board-col-header { border-radius:4px; padding:8px 12px; margin-bottom:8px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.5px; display:flex; align-items:center; justify-content:space-between; }
  .board-count { background:rgba(0,0,0,0.12); border-radius:10px; padding:1px 8px; font-size:11px; }
  .board-card { background:white; border-radius:4px; padding:10px 12px; margin-bottom:6px; box-shadow:0 1px 2px rgba(0,0,0,0.06); }

  .ai-badge { display:inline-flex; align-items:center; gap:5px; background:linear-gradient(135deg,#667eea,#764ba2); color:white; border-radius:12px; padding:3px 10px; font-size:11px; font-weight:700; }
  .chat-msg-user { background:#0052CC; color:white; border-radius:12px 12px 4px 12px; padding:10px 14px; margin:6px 0; font-size:13px; line-height:1.5; max-width:85%; float:right; clear:both; }
  .chat-msg-ai   { background:white; color:#172B4D; border:1px solid #DFE1E6; border-radius:12px 12px 12px 4px; padding:10px 14px; margin:6px 0; font-size:13px; line-height:1.5; max-width:85%; float:left; clear:both; }
  .chat-container { min-height:200px; max-height:420px; overflow-y:auto; padding:10px; background:#F8F9FA; border-radius:6px; border:1px solid #DFE1E6; margin-bottom:10px; }
  .chat-clearfix { clear:both; }

  .ai-score-card { background:white; border:1px solid #DFE1E6; border-radius:6px; padding:14px; text-align:center; }
  .ai-score-value { font-size:28px; font-weight:700; color:#0052CC; }
  .ai-score-label { font-size:11px; color:#6B778C; font-weight:600; text-transform:uppercase; margin-top:2px; }
  .preset-chip { display:inline-flex; align-items:center; gap:5px; background:#EAE6FF; color:#403294; border:1px solid #C0B6F2; border-radius:4px; padding:4px 10px; margin:3px; font-size:12px; font-weight:600; }

  .stButton > button { border-radius:6px !important; }
  [data-testid="stTextInput"] input { border:2px solid #DFE1E6; border-radius:6px; background:white; font-size:14px; }
  [data-testid="stTextInput"] input:focus { border-color:#0052CC; box-shadow:0 0 0 2px rgba(0,82,204,0.12); }
  #MainMenu { visibility:hidden; }
  footer     { visibility:hidden; }
  header     { visibility:hidden; }
  [data-testid="stDecoration"] { display:none; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CONSTANTS
# ══════════════════════════════════════════════════════════════════════════════
PAGE_SIZE = 50

STATUS_ORDER = ["New","In Progress","RCCA","Verify","On Hold","Ready to Close","Done","Close"]
COL_COLORS = {
    "New":           ("#DFE1E6","#42526E"),
    "In Progress":   ("#DEEBFF","#0052CC"),
    "RCCA":          ("#FFF0B3","#7A5200"),
    "Verify":        ("#EAE6FF","#403294"),
    "On Hold":       ("#FFEBE6","#BF2600"),
    "Done":          ("#E3FCEF","#006644"),
    "Close":         ("#E3FCEF","#006644"),
    "Ready to Close":("#E3FCEF","#006644"),
}
PRI_COLORS = {
    "Critical":"#BF2600","Highest":"#BF2600",
    "High":"#FF5630","Medium":"#FF991F","Low":"#36B37E",
}
CLOSED_STATUSES = {"Close","Done","Ready to Close"}
HIGH_PRI        = {"High","Highest","Critical"}

PRESET_QUESTIONS = {
    "✅ Properly Closed": {
        "prompt": "Based on the ticket information, RCCA data, and comments, is this issue properly closed out? Answer: YES, NO, or PARTIAL. Then provide a 1-2 sentence explanation.",
        "type": "text", "col": "AI_Properly_Closed",
    },
    "🦺 Safety Rating": {
        "prompt": "Rate the safety risk of this issue 1–10 (1=no concern, 10=critical hazard). Reply ONLY as: score;one-sentence rationale. Example: 7;Unit overheats under load.",
        "type": "score", "col": "AI_Safety_Rating",
    },
    "😊 CSAT Rating": {
        "prompt": "Rate the likely customer satisfaction impact 1–10 (1=very negative, 10=no impact). Reply ONLY as: score;one-sentence rationale.",
        "type": "score", "col": "AI_CSAT_Rating",
    },
    "⚙️ Reliability Rating": {
        "prompt": "Rate the product reliability concern 1–10 (1=severe issue, 10=no concern). Reply ONLY as: score;one-sentence rationale.",
        "type": "score", "col": "AI_Reliability_Rating",
    },
    "🔍 Root Cause Summary": {
        "prompt": "Provide a concise 1-2 sentence plain-English summary of the root cause based on all available information.",
        "type": "text", "col": "AI_Root_Cause_Summary",
    },
    "💡 Recommended Action": {
        "prompt": "What is the single most important recommended next action for this ticket? Answer in 1-2 sentences.",
        "type": "text", "col": "AI_Recommended_Action",
    },
}

RCCA_STEP_MAP = {
    "D2 – Problem Description":          "Custom field (D2 - Problem Description)",
    "D2 – Problem Categorization":        "Custom field (D2 - Problem Categorization)",
    "D3 – Containment Actions":           "Custom field (D3 - Initiate Interim Containment Actions)",
    "D3 – Implementation Date":           "Custom field (D3 - Implementation Date)",
    "D4 – Root Cause (Occurred)":         "Custom field (D4 - Define/Verify Root Cause for Problem to Occur)",
    "D4 – Root Cause (Failed to Detect)": "Custom field (D4 - Define/Verify Root Cause for Failure to Detect the Problem)",
    "D5 – Temp Corrective Action":        "Custom field (D5 \u2013 Define Temporary Corrective Action)",
    "D5 – Acceptance Criteria":           "Custom field (D5 - Acceptance Criteria)",
    "D5 – Disposition":                   "Custom field (D5 - Disposition)",
    "D5 – Verification":                  "Custom field (D5 - Verification of Temporary Corrective Action)",
    "D5 – Verified By":                   "Custom field (D5 - Verified By)",
    "D6 – Permanent Corrective Action":   "Custom field (D6 - Define Permanent Corrective Action)",
    "D6 – ECN Number":                    "Custom field (D6 - ECN Number)",
    "D6 – Implementation Date":           "Custom field (D6 - Implementation Date)",
    "D6 – Verification":                  "Custom field (D6 - Verification of Permanent Corrective Action)",
    "D7 – Prevent Recurrence":            "Custom field (D7 - Actions to prevent Recurrence)",
    "D8 – Recognize Team":                "Custom field (D8 - Recognize the Team)",
    "Root Cause":                         "Custom field (Root Cause)",
    "Corrective Action":                  "Custom field (Corrective Action)",
    "Containment Action":                 "Custom field (Containment Action)",
}

RCCA_GROUPS = {
    "🔴  D2 · Problem Definition": "D2",
    "🟠  D3 · Containment":        "D3",
    "🟡  D4 · Root Cause":         "D4",
    "🔵  D5 · Temp Corrective":    "D5",
    "🟢  D6 · Perm Corrective":    "D6",
    "✅  D7–D8 · Close Out":       "D7D8",
    "📋  General Fields":          "GEN",
}

JB = "#0052CC"
JC = ["#0052CC","#0065FF","#4C9AFF","#B3D4FF","#172B4D","#36B37E","#FF5630","#FF991F","#6554C0","#00B8D9"]
CHART_BASE = dict(
    paper_bgcolor="white", plot_bgcolor="white",
    font=dict(family="Inter, Arial, sans-serif", size=12, color="#172B4D"),
    margin=dict(t=10, b=10, l=10, r=10),
)

# ══════════════════════════════════════════════════════════════════════════════
#  DATA LOADING
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data(path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for col in ["Created","Updated","Due date","Resolved"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Summary","Assignee","Reporter","Status","Priority","Issue Type","Project name","Resolution"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unassigned" if col == "Assignee" else "").astype(str).str.strip()
    return df

# ══════════════════════════════════════════════════════════════════════════════
#  PURE HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def status_badge(s: str) -> str:
    cls = {"New":"badge-new","In Progress":"badge-progress","Verify":"badge-verify",
           "RCCA":"badge-rcca","On Hold":"badge-hold","Done":"badge-done",
           "Close":"badge-close","Ready to Close":"badge-rtc"}.get(s,"badge-new")
    return f'<span class="badge {cls}">{s}</span>'

def priority_icon(p: str) -> str:
    return {"Critical":"🔴","Highest":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}.get(p,"⚪") + f" {p}"

def type_icon(t: str) -> str:
    return {"Bug":"🐛","Task":"✅","Epic":"⚡","Sub-task":"↳","VA/VE":"🔧"}.get(t,"📋") + f" {t}"

def fmt_dt(val, short=False) -> str:
    try:
        ts = pd.Timestamp(val)
        if pd.isna(ts): return "—"
        return ts.strftime("%b %d, %Y") if short else ts.strftime("%b %d, %Y  %H:%M")
    except: return "—"

def clean_markup(text: str) -> str:
    t = str(text or "")
    t = re.sub(r'\[~accountid:[^\]]+\]', '@user', t)
    t = re.sub(r'\[([^\|]+)\|[^\]]+\|smart-link\]', r'\1', t)
    t = re.sub(r'\[([^\|]+)\|[^\]]+\]', r'\1', t)
    t = re.sub(r'\{color[^}]*\}', '', t)
    t = re.sub(r'\{[^}]+\}', '', t)
    return t.strip()

def parse_comments(row, comment_cols: list) -> list:
    out = []
    for col in comment_cols:
        val = str(row.get(col,"") or "")
        if val.strip() in ("","nan"): continue
        parts = val.split(";",2)
        body  = clean_markup(parts[2].strip() if len(parts)>2 else val.strip())
        if body:
            out.append({"date": parts[0].strip() if parts else "",
                        "author": parts[1].strip() if len(parts)>1 else "",
                        "body":   body})
    return out

def parse_attachments(row, attach_cols: list) -> list:
    out = []
    for col in attach_cols:
        val = str(row.get(col,"") or "")
        if val.strip() in ("","nan"): continue
        parts    = val.split(";")
        filename = parts[2].strip() if len(parts)>2 else "file"
        url      = parts[3].strip() if len(parts)>3 else ""
        if filename and filename != "nan":
            ext = filename.rsplit(".",1)[-1].lower() if "." in filename else ""
            out.append({"filename":filename, "url":url,
                        "is_image": ext in ("png","jpg","jpeg","gif","webp","bmp"),
                        "date": parts[0].strip() if parts else ""})
    return out

def get_sprint(row, all_cols: list):
    for c in ["Sprint","Sprint.1","Sprint.2","Sprint.3"]:
        if c in all_cols:
            v = str(row.get(c,"") or "").strip()
            if v and v!="nan": return v
    return None

def get_epic(row, all_cols: list):
    c = "Custom field (Epic Name)"
    if c in all_cols:
        v = str(row.get(c,"") or "").strip()
        if v and v!="nan": return v
    return None

@st.cache_data(show_spinner=False)
def try_load_image(url: str):
    if not url: return None
    try:
        r = requests.get(url, timeout=5)
        if r.status_code==200 and "image" in r.headers.get("Content-Type",""):
            return Image.open(BytesIO(r.content))
    except: pass
    return None

def score_color(val) -> str:
    try:
        v = float(str(val).split(";")[0].strip())
        if v>=7: return "#36B37E"
        if v>=4: return "#FF991F"
        return "#FF5630"
    except: return "#6B778C"

def score_val(val) -> str:
    try: return str(val).split(";")[0].strip()
    except: return "—"

def build_ticket_context(row, comment_cols, all_cols, rcca_steps, max_chars=6000) -> str:
    lines = [
        f"TICKET: {row['Issue key']}",
        f"Summary: {row['Summary']}",
        f"Type: {row['Issue Type']}  |  Status: {row['Status']}  |  Priority: {row['Priority']}",
        f"Assignee: {row['Assignee']}  |  Reporter: {row['Reporter']}",
        f"Project: {row['Project name']}",
        f"Created: {fmt_dt(row['Created'])}  |  Updated: {fmt_dt(row['Updated'])}",
        f"Resolution: {row.get('Resolution','') or 'Unresolved'}",
    ]
    sprint = get_sprint(row, all_cols)
    epic   = get_epic(row, all_cols)
    if sprint: lines.append(f"Sprint: {sprint}")
    if epic:   lines.append(f"Epic: {epic}")

    desc = clean_markup(row.get("Description","") or "")
    if desc and desc!="nan":
        lines += ["","DESCRIPTION:", desc[:800]]

    for label, field in [
        ("Expected Behavior", "Custom field (Expected Behavior)"),
        ("Actual Behavior",   "Custom field (Actual Behavior)"),
        ("Trigger/Scenario",  "Custom field (Trigger / Scenario)"),
    ]:
        if field in all_cols:
            v = clean_markup(row.get(field,"") or "")
            if v and v!="nan": lines += [f"\n{label.upper()}:", v[:300]]

    rcca_lines = []
    for label, col in rcca_steps.items():
        v = clean_markup(row.get(col,"") or "")
        if v and v!="nan": rcca_lines.append(f"  {label}: {v[:200]}")
    if rcca_lines: lines += ["","RCCA:"] + rcca_lines

    comments = parse_comments(row, comment_cols)
    if comments:
        lines += ["","COMMENTS:"]
        for c in comments[:8]: lines.append(f"  [{c['date']}] {c['body'][:200]}")

    return "\n".join(lines)[:max_chars]

def ai_call(client, messages, model="gpt-4o-mini", max_tokens=400) -> str:
    try:
        r = client.chat.completions.create(
            model=model, messages=messages,
            max_tokens=max_tokens, temperature=0.3,
        )
        return r.choices[0].message.content.strip()
    except Exception as e:
        return f"⚠️ Error: {e}"

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE INIT
# ══════════════════════════════════════════════════════════════════════════════
_defaults = {
    "selected_key":     None,
    "list_page":        0,
    "chat_history":     {},
    "ai_results":       {},
    "custom_questions": [],
}
for k, v in _defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR — upload + filters
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("## 🦈 SharkNinja")
    st.markdown("### Jira Dashboard")
    st.markdown("---")
    uploaded = st.file_uploader("📂 Upload Jira CSV", type="csv")

if uploaded:
    df = load_data(uploaded)
else:
    try:
        df = load_data("Jira_-_SharkNinja__22_.csv")
    except:
        st.error("⚠️ No data found. Upload a Jira CSV export using the sidebar.")
        st.stop()

# Derived column groups
all_cols     = df.columns.tolist()
comment_cols = [c for c in all_cols if c=="Comment" or re.match(r"Comment\.\d+$",c)]
attach_cols  = [c for c in all_cols if c=="Attachment" or re.match(r"Attachment\.\d+$",c)]
rcca_steps   = {k:v for k,v in RCCA_STEP_MAP.items() if v in all_cols}

client       = get_openai_client()
ai_available = client is not None

with st.sidebar:
    st.markdown("### 🔍 Filters")
    sel_projects = st.multiselect("Project",    options=sorted(df["Project name"].dropna().unique()), default=[])
    sel_status   = st.multiselect("Status",     options=sorted(df["Status"].dropna().unique()),       default=[])
    sel_priority = st.multiselect("Priority",   options=sorted(df["Priority"].dropna().unique()),     default=[])
    sel_type     = st.multiselect("Issue Type", options=sorted(df["Issue Type"].dropna().unique()),   default=[])
    sel_assignee = st.multiselect("Assignee",   options=sorted(df["Assignee"].dropna().unique()),     default=[])

    st.markdown("### 📅 Date Range")
    min_d, max_d = df["Created"].min(), df["Created"].max()
    if pd.notna(min_d) and pd.notna(max_d):
        date_from = st.date_input("From", value=min_d.date(), min_value=min_d.date(), max_value=max_d.date())
        date_to   = st.date_input("To",   value=max_d.date(), min_value=min_d.date(), max_value=max_d.date())
    else:
        date_from = date_to = None

    st.markdown("---")
    st.markdown("### 📊 View")
    view_mode = st.radio("", ["🗂️ Board","📋 List","📊 Analytics","🤖 AI Analyst"], index=1)

    st.markdown("---")
    if ai_available:
        st.markdown('<div style="background:rgba(54,179,126,0.2); border-radius:6px; padding:8px 12px; text-align:center;"><span style="font-size:12px; font-weight:700; color:#36B37E;">🤖 AI Ready</span><div style="font-size:10px; color:#B3D4FF; margin-top:2px;">OpenAI connected</div></div>', unsafe_allow_html=True)
    else:
        st.markdown('<div style="background:rgba(255,255,255,0.1); border-radius:6px; padding:8px 12px; text-align:center;"><span style="font-size:12px; color:#B3D4FF;">🤖 AI Offline</span><div style="font-size:10px; color:#B3D4FF; margin-top:2px;">Add OPENAI_API_KEY to Streamlit secrets</div></div>', unsafe_allow_html=True)

# ── Apply filters ──────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_projects: fdf = fdf[fdf["Project name"].isin(sel_projects)]
if sel_status:   fdf = fdf[fdf["Status"].isin(sel_status)]
if sel_priority: fdf = fdf[fdf["Priority"].isin(sel_priority)]
if sel_type:     fdf = fdf[fdf["Issue Type"].isin(sel_type)]
if sel_assignee: fdf = fdf[fdf["Assignee"].isin(sel_assignee)]
if date_from and date_to:
    fdf = fdf[(fdf["Created"].dt.date >= date_from) & (fdf["Created"].dt.date <= date_to)]

with st.sidebar:
    st.markdown("---")
    pct = int(100*len(fdf)/len(df)) if len(df) else 0
    st.markdown(f'<div style="background:rgba(255,255,255,0.15); border-radius:6px; padding:10px 12px; text-align:center;"><div style="font-size:22px; font-weight:700; color:white;">{len(fdf):,}</div><div style="font-size:11px; color:#B3D4FF; margin-top:2px;">of {len(df):,} issues ({pct}%)</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  TOP BAR + SEARCH + QUICK FILTERS + KPIs
# ══════════════════════════════════════════════════════════════════════════════
open_count = len(fdf[~fdf["Status"].isin(CLOSED_STATUSES)])
closed     = len(fdf[fdf["Status"].isin(CLOSED_STATUSES)])
bugs       = len(fdf[fdf["Issue Type"]=="Bug"])
high_pri   = len(fdf[fdf["Priority"].isin(HIGH_PRI)])
close_rate = int(100*closed/len(fdf)) if len(fdf) else 0

ai_pill = '<span class="ai-badge">🤖 AI ON</span>' if ai_available else ""
st.markdown(f"""
<div class="top-bar">
  <div class="top-bar-left">
    <span style="font-size:28px; line-height:1;">🦈</span>
    <div>
      <h1>SharkNinja · Jira Dashboard &nbsp;{ai_pill}</h1>
      <p class="subtitle">Issue tracking, analytics &amp; AI insights</p>
    </div>
  </div>
  <div><span class="top-bar-badge">{len(fdf):,} issues</span></div>
</div>
""", unsafe_allow_html=True)

search = st.text_input("", placeholder="🔎  Search by summary or ticket key…", label_visibility="collapsed")
if search:
    fdf = fdf[fdf["Summary"].str.contains(search,case=False,na=False) | fdf["Issue key"].str.contains(search,case=False,na=False)]
    st.session_state.list_page = 0

# Quick filters
st.markdown('<div class="section-header">Quick Filters</div>', unsafe_allow_html=True)
qf_defs = {
    "🔓 Open Only":     lambda d: d[~d["Status"].isin(CLOSED_STATUSES)],
    "🔴 High Priority": lambda d: d[d["Priority"].isin(HIGH_PRI)],
    "🐛 Bugs Only":     lambda d: d[d["Issue Type"]=="Bug"],
    "🔬 RCCA":          lambda d: d[d["Status"]=="RCCA"],
    "⏳ On Hold":        lambda d: d[d["Status"]=="On Hold"],
    "✅ Verify":         lambda d: d[d["Status"]=="Verify"],
}
qf_cols = st.columns(6)
for i,(label,fn) in enumerate(qf_defs.items()):
    with qf_cols[i]:
        if st.button(f"{label}  ({len(fn(fdf))})", key=f"qf_{i}"):
            fdf = fn(fdf); st.session_state.list_page = 0

# KPIs
st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total Issues",  f"{len(fdf):,}")
c2.metric("Open",          f"{open_count:,}", delta=f"{open_count-closed:+,} vs closed", delta_color="inverse")
c3.metric("Closed / Done", f"{closed:,}")
c4.metric("Bugs",          f"{bugs:,}")
c5.metric("High Priority", f"{high_pri:,}")
c6.metric("Close Rate",    f"{close_rate}%")

ce, _ = st.columns([1,5])
with ce:
    csv_bytes = fdf[["Issue key","Summary","Status","Priority","Issue Type","Assignee","Reporter","Created","Updated"]].to_csv(index=False).encode()
    st.download_button("⬇️  Export CSV", data=csv_bytes, file_name="jira_filtered.csv", mime="text/csv")

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET DETAIL PANEL
# ══════════════════════════════════════════════════════════════════════════════
def render_ticket_detail(row):
    comments    = parse_comments(row, comment_cols)
    attachments = parse_attachments(row, attach_cols)
    images      = [a for a in attachments if a["is_image"]]
    files       = [a for a in attachments if not a["is_image"]]
    sprint      = get_sprint(row, all_cols)
    epic        = get_epic(row, all_cols)
    key         = row["Issue key"]
    ai_res      = st.session_state.ai_results.get(key, {})

    rcca_has = any(
        str(row.get(v,"") or "").strip() not in ("","nan")
        for v in rcca_steps.values()
    )

    # Breadcrumb
    st.markdown(f'<div class="breadcrumb"><span>🦈 SharkNinja</span><span class="sep">›</span><span>{row["Project name"]}</span><span class="sep">›</span><strong style="color:#172B4D;">{key}</strong></div>', unsafe_allow_html=True)

    # Header card
    pills = ""
    if rcca_has: pills += ' <span style="background:#FFF0B3; color:#7A5200; font-size:10px; font-weight:700; padding:2px 7px; border-radius:3px;">RCCA DATA</span>'
    if ai_res:   pills += ' <span style="background:linear-gradient(135deg,#667eea,#764ba2); color:white; font-size:10px; font-weight:700; padding:2px 7px; border-radius:3px;">🤖 AI SCORED</span>'

    st.markdown(f"""
    <div class="card" style="border-left:5px solid #0052CC;">
      <div class="detail-header">{row['Summary']}{pills}</div>
      <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
        {status_badge(row['Status'])}
        <span style="font-size:13px; color:#5E6C84;">{type_icon(row['Issue Type'])}</span>
        <span style="font-size:13px; color:#5E6C84;">{priority_icon(row['Priority'])}</span>
        {'<span style="font-size:12px; background:#EAE6FF; color:#403294; padding:2px 8px; border-radius:3px; font-weight:600;">⚡ ' + epic + '</span>' if epic else ''}
        {'<span style="font-size:12px; background:#DEEBFF; color:#0052CC; padding:2px 8px; border-radius:3px; font-weight:600;">🏃 ' + sprint[:30] + '</span>' if sprint else ''}
      </div>
      <div style="font-size:12px; color:#97A0AF; font-family:monospace; font-weight:600;">{key} &nbsp;·&nbsp; {row['Project name']}</div>
    </div>
    """, unsafe_allow_html=True)

    cc, _ = st.columns([1,5])
    with cc:
        if st.button("✕  Close", key=f"close_{key}"):
            st.session_state.selected_key = None; st.rerun()

    left, right = st.columns([3,1])

    # ── Right sidebar ──
    with right:
        st.markdown(f"""
        <div class="card" style="background:#F8F9FA;">
          <div class="detail-section-title">Details</div>
          <table class="detail-meta-table">
            <tr><td class="detail-meta-label">Assignee</td><td><strong>{row['Assignee']}</strong></td></tr>
            <tr><td class="detail-meta-label">Reporter</td><td>{row['Reporter']}</td></tr>
            <tr><td class="detail-meta-label">Priority</td><td>{priority_icon(row['Priority'])}</td></tr>
            <tr><td class="detail-meta-label">Status</td><td>{status_badge(row['Status'])}</td></tr>
            <tr><td class="detail-meta-label">Resolution</td><td style="color:#6B778C; font-size:12px;">{row.get('Resolution','') or '—'}</td></tr>
            <tr><td class="detail-meta-label">Created</td><td style="color:#6B778C; font-size:12px;">{fmt_dt(row['Created'])}</td></tr>
            <tr><td class="detail-meta-label">Updated</td><td style="color:#6B778C; font-size:12px;">{fmt_dt(row['Updated'])}</td></tr>
            <tr><td class="detail-meta-label">Due Date</td><td style="color:#6B778C; font-size:12px;">{fmt_dt(row.get('Due date'))}</td></tr>
            {'<tr><td class="detail-meta-label">Sprint</td><td style="color:#0052CC; font-size:12px; font-weight:600;">' + sprint + '</td></tr>' if sprint else ''}
            {'<tr><td class="detail-meta-label">Epic</td><td style="color:#403294; font-size:12px; font-weight:600;">' + epic + '</td></tr>' if epic else ''}
          </table>
        </div>
        """, unsafe_allow_html=True)

        # AI score mini cards
        if ai_res:
            safety = ai_res.get("AI_Safety_Rating","")
            csat   = ai_res.get("AI_CSAT_Rating","")
            rely   = ai_res.get("AI_Reliability_Rating","")
            if any([safety, csat, rely]):
                st.markdown(f"""
                <div class="card" style="background:#F8F9FA; padding:12px;">
                  <div class="detail-section-title">🤖 AI Scores</div>
                  <div style="display:grid; grid-template-columns:1fr 1fr 1fr; gap:6px; margin-top:8px;">
                    <div class="ai-score-card"><div class="ai-score-value" style="color:{score_color(safety)};">{score_val(safety)}</div><div class="ai-score-label">Safety</div></div>
                    <div class="ai-score-card"><div class="ai-score-value" style="color:{score_color(csat)};">{score_val(csat)}</div><div class="ai-score-label">CSAT</div></div>
                    <div class="ai-score-card"><div class="ai-score-value" style="color:{score_color(rely)};">{score_val(rely)}</div><div class="ai-score-label">Reliability</div></div>
                  </div>
                </div>
                """, unsafe_allow_html=True)

        if files:
            st.markdown('<div class="detail-section-title">📄 Files</div>', unsafe_allow_html=True)
            st.markdown('<div style="display:flex; flex-wrap:wrap;">' + "".join(
                f'<a href="{f["url"]}" target="_blank" class="attach-chip">📄 {f["filename"]}</a>'
                if f["url"] else f'<span class="attach-chip">📄 {f["filename"]}</span>'
                for f in files
            ) + '</div>', unsafe_allow_html=True)

    # ── Left tabs ──
    with left:
        chat_dot = " ●" if st.session_state.chat_history.get(key) else ""
        tabs = st.tabs([
            "📝  Description",
            f"🔬  RCCA{'  ✓' if rcca_has else ''}",
            f"💬  Comments ({len(comments)})",
            f"🖼️  Images ({len(images)})",
            f"🤖  AI Chat{chat_dot}",
        ])

        # Description
        with tabs[0]:
            desc = clean_markup(row.get("Description","") or "")
            st.markdown(
                f'<div class="desc-box">{desc[:3000]}</div>' if desc and desc!="nan"
                else '<div class="desc-box" style="color:#A5ADBA; font-style:italic; text-align:center; padding:30px;">No description provided.</div>',
                unsafe_allow_html=True
            )
            for label, field, css in [
                ("✅  Expected Behavior","Custom field (Expected Behavior)","expected"),
                ("❌  Actual Behavior",  "Custom field (Actual Behavior)",  "actual"),
                ("🔁  Trigger/Scenario", "Custom field (Trigger / Scenario)","trigger"),
            ]:
                if field in all_cols:
                    v = clean_markup(row.get(field,"") or "")
                    if v and v!="nan":
                        st.markdown(f'<div style="font-size:11px; font-weight:700; color:#5E6C84; text-transform:uppercase; letter-spacing:0.5px; margin:12px 0 5px 0;">{label}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="field-box {css}">{v[:500]}</div>', unsafe_allow_html=True)

        # RCCA
        with tabs[1]:
            has_any = False
            for group_label, prefix in RCCA_GROUPS.items():
                if prefix == "D7D8":
                    keys_in_group = [k for k in rcca_steps if k.startswith("D7") or k.startswith("D8")]
                elif prefix == "GEN":
                    keys_in_group = [k for k in rcca_steps if not any(k.startswith(p) for p in ["D2","D3","D4","D5","D6","D7","D8"])]
                else:
                    keys_in_group = [k for k in rcca_steps if k.startswith(prefix)]
                populated = [(k, clean_markup(row.get(rcca_steps[k],"") or "")) for k in keys_in_group]
                populated = [(k,v) for k,v in populated if v and v!="nan"]
                if populated:
                    st.markdown(f'<div style="font-size:12px; font-weight:700; color:#344563; margin:14px 0 8px 0;">{group_label}</div>', unsafe_allow_html=True)
                    st.markdown("".join(f'<div class="rcca-step"><div class="rcca-step-label">{k}</div><div class="rcca-step-value">{v[:600]}</div></div>' for k,v in populated), unsafe_allow_html=True)
                    has_any = True
            if not has_any:
                st.markdown('<div style="text-align:center; padding:50px; color:#A5ADBA;"><div style="font-size:36px;">🔬</div><div style="font-size:14px; font-weight:600; margin-top:8px;">No RCCA data for this ticket</div></div>', unsafe_allow_html=True)

        # Comments
        with tabs[2]:
            if comments:
                for c in comments:
                    initials = (c["author"][:2]).upper() if c["author"] else "?"
                    author   = c["author"][:16]+"…" if len(c["author"])>18 else c["author"]
                    st.markdown(f'<div class="comment-bubble"><div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;"><div class="comment-avatar">{initials}</div><div><div class="comment-author">{author}</div><div class="comment-date">{c["date"]}</div></div></div><div class="comment-body">{c["body"][:1000]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center; padding:50px; color:#A5ADBA;"><div style="font-size:36px;">💬</div><div style="font-size:14px; font-weight:600; margin-top:8px;">No comments</div></div>', unsafe_allow_html=True)

        # Images
        with tabs[3]:
            if images:
                loaded_any = False
                for att in images:
                    img = try_load_image(att["url"]) if att["url"] else None
                    if img:
                        st.image(img, caption=att["filename"], use_container_width=True)
                        loaded_any = True
                    else:
                        st.markdown(
                            f'<a href="{att["url"]}" target="_blank" class="attach-chip">🖼️ {att["filename"]}</a>' if att["url"]
                            else f'<span class="attach-chip">🖼️ {att["filename"]}</span>',
                            unsafe_allow_html=True
                        )
                if not loaded_any:
                    st.info("🔐 Images require Jira login. Links above open them in your browser.", icon="ℹ️")
            else:
                st.markdown('<div style="text-align:center; padding:50px; color:#A5ADBA;"><div style="font-size:36px;">🖼️</div><div style="font-size:14px; font-weight:600; margin-top:8px;">No images attached</div></div>', unsafe_allow_html=True)

        # AI Chat
        with tabs[4]:
            if not ai_available:
                st.warning("Add `OPENAI_API_KEY` to your Streamlit secrets to enable AI chat.", icon="🔐")
            else:
                if key not in st.session_state.chat_history:
                    st.session_state.chat_history[key] = []
                history = st.session_state.chat_history[key]
                context = build_ticket_context(row, comment_cols, all_cols, rcca_steps)
                system_msg = {"role":"system","content":f"You are a SharkNinja engineering quality analyst. Answer questions about Jira tickets concisely and accurately.\n\nTICKET CONTEXT:\n{context}"}

                # Suggested questions
                st.markdown("**💡 Suggested:**")
                suggestions = [
                    "Is this properly closed?", "What is the root cause?",
                    "What should happen next?",  "What's the safety risk?",
                    "Summarize in 2 sentences",  "Any red flags?",
                ]
                sq_cols = st.columns(3)
                for i, q in enumerate(suggestions):
                    with sq_cols[i%3]:
                        if st.button(q, key=f"sq_{key}_{i}"):
                            history.append({"role":"user","content":q})
                            with st.spinner("Thinking…"):
                                reply = ai_call(client, [system_msg]+history[-10:])
                            history.append({"role":"assistant","content":reply})
                            st.session_state.chat_history[key] = history
                            st.rerun()

                st.markdown("")

                # Chat history
                if history:
                    html = '<div class="chat-container">'
                    for m in history:
                        if m["role"]=="user":
                            html += f'<div class="chat-msg-user">{m["content"]}</div>'
                        else:
                            html += f'<div class="chat-msg-ai">🤖 {m["content"]}</div>'
                    html += '<div class="chat-clearfix"></div></div>'
                    st.markdown(html, unsafe_allow_html=True)
                else:
                    st.markdown('<div style="text-align:center; padding:30px; color:#A5ADBA; background:#F8F9FA; border-radius:6px; border:1px solid #DFE1E6;"><div style="font-size:28px;">🤖</div><div style="font-size:13px; margin-top:6px;">Ask anything about this ticket</div></div>', unsafe_allow_html=True)

                user_input = st.text_input("Ask about this ticket…", key=f"ci_{key}", placeholder="e.g. Is this properly closed? What's the root cause?", label_visibility="collapsed")
                s_col, c_col, _ = st.columns([1,1,4])
                with s_col:
                    if st.button("Send ➤", key=f"cs_{key}") and user_input.strip():
                        history.append({"role":"user","content":user_input.strip()})
                        with st.spinner("Thinking…"):
                            reply = ai_call(client, [system_msg]+history[-10:])
                        history.append({"role":"assistant","content":reply})
                        st.session_state.chat_history[key] = history
                        st.rerun()
                with c_col:
                    if st.button("🗑️ Clear", key=f"cc_{key}") and history:
                        st.session_state.chat_history[key] = []; st.rerun()

    st.markdown('<hr style="border:none; border-top:2px solid #DFE1E6; margin:20px 0;">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🗂️ Board":
    if st.session_state.selected_key:
        match = fdf[fdf["Issue key"]==st.session_state.selected_key]
        if not match.empty:
            st.markdown('<div class="section-header">Ticket Detail</div>', unsafe_allow_html=True)
            render_ticket_detail(match.iloc[0])

    st.markdown('<div class="section-header">Board</div>', unsafe_allow_html=True)
    present = [s for s in STATUS_ORDER if s in fdf["Status"].unique()]
    for s in fdf["Status"].unique():
        if s not in present: present.append(s)

    cols = st.columns(min(len(present),6))
    for col, status in zip(cols, present[:6]):
        grp = fdf[fdf["Status"]==status].head(25)
        bg, fg = COL_COLORS.get(status,("#F4F5F7","#42526E"))
        with col:
            st.markdown(f'<div class="board-col-header" style="background:{bg}; color:{fg};"><span>{status.upper()}</span><span class="board-count">{len(fdf[fdf["Status"]==status])}</span></div>', unsafe_allow_html=True)
            for _, row in grp.iterrows():
                pc  = PRI_COLORS.get(row["Priority"],"#97A0AF")
                sel = st.session_state.selected_key == row["Issue key"]
                ai_dot = " 🤖" if row["Issue key"] in st.session_state.ai_results else ""
                border = f"border:2px solid #0052CC; border-left:3px solid {pc};" if sel else f"border:1px solid #DFE1E6; border-left:3px solid {pc};"
                st.markdown(f'<div class="board-card" style="{border}"><div style="color:#0052CC; font-weight:700; font-family:monospace; font-size:11px; margin-bottom:5px;">{row["Issue key"]}{ai_dot}</div><div style="color:#172B4D; font-size:12px; line-height:1.4; margin-bottom:8px;">{str(row["Summary"])[:80]}{"…" if len(str(row["Summary"]))>80 else ""}</div><div style="display:flex; justify-content:space-between; align-items:center;"><span style="font-size:11px; color:#6B778C;">{type_icon(row["Issue Type"])}</span><span style="width:22px; height:22px; border-radius:50%; background:{pc}; color:white; font-size:10px; font-weight:700; display:inline-flex; align-items:center; justify-content:center;" title="{row["Assignee"]}">{str(row["Assignee"])[:1].upper()}</span></div></div>', unsafe_allow_html=True)
                if st.button(row["Issue key"], key=f"b_{row['Issue key']}", help=f"Open {row['Issue key']}"):
                    st.session_state.selected_key = row["Issue key"] if not sel else None
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📋 List":
    if st.session_state.selected_key:
        match = fdf[fdf["Issue key"]==st.session_state.selected_key]
        if not match.empty:
            st.markdown('<div class="section-header">Ticket Detail</div>', unsafe_allow_html=True)
            render_ticket_detail(match.iloc[0])

    st.markdown('<div class="section-header">Issues</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns([2,2])
    with sc1: sort_col = st.selectbox("Sort by", ["Created","Updated","Priority","Status","Issue key"])
    with sc2: sort_dir = st.selectbox("Order",   ["Descending","Ascending"])

    if sort_col == "Priority":
        fdf = fdf.copy()
        fdf["_ps"] = fdf["Priority"].map({"Critical":0,"Highest":1,"High":2,"Medium":3,"Low":4}).fillna(5)
        fdf = fdf.sort_values("_ps", ascending=(sort_dir=="Ascending"))
    else:
        fdf = fdf.sort_values(sort_col, ascending=(sort_dir=="Ascending"), na_position="last")

    total_pages = max(1,(len(fdf)+PAGE_SIZE-1)//PAGE_SIZE)
    page        = min(st.session_state.list_page, total_pages-1)
    page_df     = fdf.iloc[page*PAGE_SIZE:(page+1)*PAGE_SIZE]

    COLS = [1.4,4,1.4,1.5,1.3,2.2,1.5,1.5]
    HDRS = ["KEY","SUMMARY","TYPE","STATUS","PRIORITY","ASSIGNEE","CREATED","UPDATED"]
    hrow = st.columns(COLS)
    for hc, lbl in zip(hrow, HDRS):
        hc.markdown(f'<div style="font-size:11px; font-weight:700; color:#5E6C84; text-transform:uppercase; letter-spacing:0.5px; padding:8px 0 6px 0; border-bottom:2px solid #DFE1E6;">{lbl}</div>', unsafe_allow_html=True)

    for _, row in page_df.iterrows():
        is_sel = st.session_state.selected_key == row["Issue key"]
        ai_dot = " 🤖" if row["Issue key"] in st.session_state.ai_results else ""
        bg     = "#EBF2FF" if is_sel else "white"
        border = "border-left:3px solid #0052CC;" if is_sel else "border-left:3px solid transparent;"
        cell   = f"background:{bg}; {border} padding:8px 4px; border-bottom:1px solid #F4F5F7; font-size:13px;"
        r = st.columns(COLS)
        with r[0]:
            if st.button(f"{row['Issue key']}{ai_dot}", key=f"l_{row['Issue key']}"):
                st.session_state.selected_key = row["Issue key"] if not is_sel else None
                st.rerun()
        r[1].markdown(f'<div style="{cell} overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#172B4D;" title="{row["Summary"]}">{str(row["Summary"])[:60]}{"…" if len(str(row["Summary"]))>60 else ""}</div>', unsafe_allow_html=True)
        r[2].markdown(f'<div style="{cell} color:#5E6C84;">{type_icon(row["Issue Type"])}</div>', unsafe_allow_html=True)
        r[3].markdown(f'<div style="{cell}">{status_badge(row["Status"])}</div>', unsafe_allow_html=True)
        r[4].markdown(f'<div style="{cell}">{priority_icon(row["Priority"])}</div>', unsafe_allow_html=True)
        r[5].markdown(f'<div style="{cell} color:#5E6C84; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{row["Assignee"]}</div>', unsafe_allow_html=True)
        r[6].markdown(f'<div style="{cell} color:#97A0AF; font-size:12px;">{fmt_dt(row["Created"],short=True)}</div>', unsafe_allow_html=True)
        r[7].markdown(f'<div style="{cell} color:#97A0AF; font-size:12px;">{fmt_dt(row["Updated"],short=True)}</div>', unsafe_allow_html=True)

    st.markdown("")
    pg1,pg2,pg3,pg4,_ = st.columns([1,1,2,1,3])
    with pg1:
        if st.button("◀  Prev", disabled=(page==0), key="prev_p"):
            st.session_state.list_page=max(0,page-1); st.rerun()
    with pg2:
        if st.button("Next  ▶", disabled=(page>=total_pages-1), key="next_p"):
            st.session_state.list_page=min(total_pages-1,page+1); st.rerun()
    with pg3:
        s,e = page*PAGE_SIZE+1, min((page+1)*PAGE_SIZE,len(fdf))
        st.markdown(f'<div style="font-size:12px; color:#6B778C; padding-top:10px;">Showing {s}–{e} of {len(fdf):,} · Page {page+1}/{total_pages}</div>', unsafe_allow_html=True)
    with pg4:
        jump = st.number_input("", min_value=1, max_value=total_pages, value=page+1, step=1, label_visibility="collapsed")
        if jump-1 != page:
            st.session_state.list_page=jump-1; st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📊 Analytics":
    def chart(fig, h=300):
        fig.update_layout(**CHART_BASE, height=h)
        st.plotly_chart(fig, use_container_width=True)

    r1l, r1r = st.columns(2)
    with r1l:
        st.markdown('<div class="section-header">Issues by Status</div>', unsafe_allow_html=True)
        d = fdf["Status"].value_counts().reset_index(); d.columns=["Status","Count"]
        fig = px.bar(d, x="Status", y="Count", color="Status", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(showlegend=False, xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title=""))
        chart(fig)

    with r1r:
        st.markdown('<div class="section-header">Issues by Priority</div>', unsafe_allow_html=True)
        d = fdf["Priority"].value_counts().reset_index(); d.columns=["Priority","Count"]
        fig = px.pie(d, names="Priority", values="Count", hole=0.5, color="Priority",
                     color_discrete_map={"Critical":"#BF2600","Highest":"#FF5630","High":"#FF7452","Medium":"#FF991F","Low":"#36B37E"})
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="white",width=2)))
        fig.update_layout(showlegend=False)
        chart(fig)

    r2l, r2r = st.columns(2)
    with r2l:
        st.markdown('<div class="section-header">Issues Created Over Time</div>', unsafe_allow_html=True)
        ts = fdf.dropna(subset=["Created"]).copy()
        ts["Week"] = ts["Created"].dt.to_period("W").dt.start_time
        tsg = ts.groupby("Week").size().reset_index(name="Count")
        fig = px.area(tsg, x="Week", y="Count", color_discrete_sequence=[JB])
        fig.update_traces(fill="tozeroy", line_color=JB, fillcolor="rgba(0,82,204,0.10)", line_width=2)
        fig.update_layout(xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title=""))
        chart(fig)

    with r2r:
        st.markdown('<div class="section-header">Top Assignees</div>', unsafe_allow_html=True)
        d = fdf[fdf["Assignee"]!="Unassigned"]["Assignee"].value_counts().head(12).reset_index(); d.columns=["Assignee","Count"]
        fig = px.bar(d, x="Count", y="Assignee", orientation="h", color="Count", color_continuous_scale=["#DEEBFF",JB], text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title="",categoryorder="total ascending"))
        chart(fig, h=360)

    st.markdown('<div class="section-header">Open vs Closed Over Time</div>', unsafe_allow_html=True)
    ts2 = fdf.dropna(subset=["Created"]).copy()
    ts2["Week"] = ts2["Created"].dt.to_period("W").dt.start_time
    ts2["Type"] = ts2["Status"].apply(lambda s: "Closed" if s in CLOSED_STATUSES else "Open")
    oc = ts2.groupby(["Week","Type"]).size().reset_index(name="Count")
    fig = px.bar(oc, x="Week", y="Count", color="Type", color_discrete_map={"Open":"#FF5630","Closed":"#36B37E"}, barmode="stack")
    fig.update_layout(xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title=""), legend=dict(orientation="h",yanchor="bottom",y=1.02,xanchor="right",x=1))
    chart(fig, h=280)

    r3l, r3r = st.columns(2)
    with r3l:
        st.markdown('<div class="section-header">Issue Type Breakdown</div>', unsafe_allow_html=True)
        d = fdf["Issue Type"].value_counts().reset_index(); d.columns=["Type","Count"]
        fig = px.bar(d, x="Type", y="Count", color="Type", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(showlegend=False, xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title=""))
        chart(fig, h=280)

    with r3r:
        st.markdown('<div class="section-header">Resolution Breakdown</div>', unsafe_allow_html=True)
        d = fdf["Resolution"].replace("","Unresolved").value_counts().head(8).reset_index(); d.columns=["Resolution","Count"]
        fig = px.bar(d, x="Count", y="Resolution", orientation="h", color="Count", color_continuous_scale=["#DEEBFF",JB], text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(coloraxis_showscale=False, xaxis=dict(gridcolor="#F4F5F7",title=""), yaxis=dict(gridcolor="#F4F5F7",title="",categoryorder="total ascending"))
        chart(fig, h=280)

    st.markdown('<div class="section-header">Status × Priority Heatmap</div>', unsafe_allow_html=True)
    heat  = fdf.groupby(["Status","Priority"]).size().reset_index(name="Count")
    pivot = heat.pivot(index="Status", columns="Priority", values="Count").fillna(0)
    fig   = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#F0F4FF"],[0.5,"#4C9AFF"],[1,JB]],
        text=pivot.values.astype(int), texttemplate="%{text}", showscale=True, xgap=2, ygap=2,
    ))
    chart(fig)

# ══════════════════════════════════════════════════════════════════════════════
#  AI ANALYST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "🤖 AI Analyst":
    st.markdown('<div class="section-header">🤖 AI Analyst</div>', unsafe_allow_html=True)

    if not ai_available:
        st.error("OpenAI API key not found. Add `OPENAI_API_KEY` to your Streamlit secrets and reboot the app.", icon="🔐")
        st.code('OPENAI_API_KEY = "sk-proj-your-key-here"', language="toml")
        st.stop()

    st.markdown("""
    <div class="card" style="border-left:4px solid #764ba2;">
      <div style="display:flex; align-items:center; gap:10px; margin-bottom:6px;">
        <span style="font-size:24px;">🤖</span>
        <div>
          <div style="font-size:16px; font-weight:700; color:#172B4D;">Bulk AI Analysis</div>
          <div style="font-size:12px; color:#6B778C;">Run preset + custom questions across tickets and export an enriched CSV</div>
        </div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    cfg_l, cfg_r = st.columns([2,1])

    with cfg_l:
        st.markdown("**📋 Preset Questions**")
        st.markdown('<div style="display:flex; flex-wrap:wrap; gap:4px; margin-bottom:12px;">' + "".join(f'<span class="preset-chip">{q}</span>' for q in PRESET_QUESTIONS) + '</div>', unsafe_allow_html=True)
        selected_presets = st.multiselect("Select presets to run", options=list(PRESET_QUESTIONS.keys()), default=list(PRESET_QUESTIONS.keys()), key="preset_sel")

        st.markdown("**➕ Custom Questions**")
        new_q = st.text_input("Type a custom question and press Add", placeholder="e.g. Does this affect multiple SKUs?", key="new_q")
        if st.button("➕ Add") and new_q.strip():
            if new_q.strip() not in st.session_state.custom_questions:
                st.session_state.custom_questions.append(new_q.strip())
            st.rerun()

        for i, q in enumerate(st.session_state.custom_questions):
            qc1, qc2 = st.columns([5,1])
            qc1.markdown(f'<div style="font-size:13px; padding:6px 10px; background:#F4F5F7; border-radius:4px;">{q}</div>', unsafe_allow_html=True)
            with qc2:
                if st.button("✕", key=f"dq_{i}"):
                    st.session_state.custom_questions.pop(i); st.rerun()

    with cfg_r:
        st.markdown("**🎯 Ticket Selection**")
        scope = st.radio("Analyze:", ["Current filtered tickets","Specific ticket keys"], key="ai_scope")
        ticket_limit = 50

        if scope == "Current filtered tickets":
            analyze_df = fdf.head(ticket_limit).copy()
            st.info(f"Will analyze **{min(len(fdf),ticket_limit)}** tickets (max {ticket_limit})", icon="ℹ️")
        else:
            manual_keys = st.text_area("Paste ticket keys (one per line)", placeholder="PCOPT-1821\nPCOPT-1820", height=120, key="mk")
            keys_list  = [k.strip() for k in (manual_keys or "").strip().split("\n") if k.strip()]
            analyze_df = fdf[fdf["Issue key"].isin(keys_list)].head(ticket_limit).copy() if keys_list else pd.DataFrame()
            st.info(f"**{len(analyze_df)}** matching tickets found", icon="ℹ️")

        model_choice = st.selectbox("Model", ["gpt-4o-mini","gpt-4o","gpt-4-turbo"], index=0)

    st.markdown("")
    total_q  = len(selected_presets) + len(st.session_state.custom_questions)
    n_tix    = len(analyze_df) if not analyze_df.empty else 0
    disabled = n_tix==0 or total_q==0

    run_c, reset_c, _ = st.columns([2,1,4])
    with run_c:
        run_btn = st.button(f"🚀  Run Analysis  ({n_tix} tickets × {total_q} questions)", disabled=disabled, type="primary", key="run_ai")
    with reset_c:
        if st.button("🗑️  Clear Results", key="clear_ai"):
            st.session_state.ai_results = {}; st.rerun()

    if run_btn and not disabled:
        prog    = st.progress(0)
        status  = st.empty()
        total   = n_tix * total_q
        done    = 0
        sys_base = "You are a SharkNinja engineering quality analyst. Answer questions about Jira tickets concisely and factually."

        for _, row in analyze_df.iterrows():
            k       = row["Issue key"]
            ctx     = build_ticket_context(row, comment_cols, all_cols, rcca_steps)
            sys_msg = {"role":"system","content":f"{sys_base}\n\nTICKET CONTEXT:\n{ctx}"}
            if k not in st.session_state.ai_results:
                st.session_state.ai_results[k] = {}

            for q_label in selected_presets:
                q = PRESET_QUESTIONS[q_label]
                status.markdown(f'<div style="font-size:12px; color:#6B778C;">Analyzing **{k}** — {q_label}…</div>', unsafe_allow_html=True)
                result = ai_call(client, [sys_msg,{"role":"user","content":q["prompt"]}], model=model_choice, max_tokens=200)
                st.session_state.ai_results[k][q["col"]] = result
                done += 1; prog.progress(done/total)

            for cq in st.session_state.custom_questions:
                col_name = "AI_" + re.sub(r'[^a-zA-Z0-9_]','_', cq[:30])
                status.markdown(f'<div style="font-size:12px; color:#6B778C;">Analyzing **{k}** — {cq[:40]}…</div>', unsafe_allow_html=True)
                result = ai_call(client, [sys_msg,{"role":"user","content":cq}], model=model_choice, max_tokens=200)
                st.session_state.ai_results[k][col_name] = result
                done += 1; prog.progress(done/total)

        prog.progress(1.0)
        status.markdown(f'<div style="font-size:13px; font-weight:600; color:#36B37E;">✅ Complete — {n_tix} tickets, {total} answers</div>', unsafe_allow_html=True)
        st.rerun()

    # ── Results ────────────────────────────────────────────────────────────────
    if st.session_state.ai_results:
        st.markdown('<div class="section-header">Results</div>', unsafe_allow_html=True)

        rows = []
        for k, res in st.session_state.ai_results.items():
            m = fdf[fdf["Issue key"]==k]
            if m.empty: continue
            row_data = {"Issue key":k, "Summary":m.iloc[0]["Summary"][:60], "Status":m.iloc[0]["Status"], "Priority":m.iloc[0]["Priority"]}
            row_data.update(res)
            rows.append(row_data)

        if rows:
            res_df = pd.DataFrame(rows)

            # Score distribution charts
            score_cols = [c for c in res_df.columns if c in ["AI_Safety_Rating","AI_CSAT_Rating","AI_Reliability_Rating"]]
            if score_cols:
                st.markdown("**📊 Score Distributions**")
                sc_cols = st.columns(len(score_cols))
                for i, sc in enumerate(score_cols):
                    with sc_cols[i]:
                        def extract(v):
                            try: return float(str(v).split(";")[0].strip())
                            except: return None
                        scores = res_df[sc].apply(extract).dropna()
                        if not scores.empty:
                            avg   = scores.mean()
                            color = "#36B37E" if avg>=7 else "#FF991F" if avg>=4 else "#FF5630"
                            label = sc.replace("AI_","").replace("_"," ")
                            fig   = px.histogram(scores, nbins=10, color_discrete_sequence=[color])
                            fig.update_layout(**CHART_BASE, height=180, showlegend=False,
                                              title=dict(text=f"{label}  (avg {avg:.1f})", font=dict(size=12,color="#172B4D")),
                                              xaxis=dict(range=[0,10],gridcolor="#F4F5F7",title=""),
                                              yaxis=dict(gridcolor="#F4F5F7",title=""))
                            st.plotly_chart(fig, use_container_width=True)

            # Full table
            st.markdown("**📋 Full Results**")
            col_cfg = {
                "Issue key": st.column_config.TextColumn("Key",       width=100),
                "Summary":   st.column_config.TextColumn("Summary",   width=250),
                "Status":    st.column_config.TextColumn("Status",    width=100),
                "Priority":  st.column_config.TextColumn("Priority",  width=80),
                "AI_Safety_Rating":      st.column_config.TextColumn("🦺 Safety",     width=80),
                "AI_CSAT_Rating":        st.column_config.TextColumn("😊 CSAT",       width=80),
                "AI_Reliability_Rating": st.column_config.TextColumn("⚙️ Reliability", width=80),
                "AI_Properly_Closed":    st.column_config.TextColumn("✅ Closed?",    width=100),
                "AI_Root_Cause_Summary": st.column_config.TextColumn("🔍 Root Cause", width=200),
                "AI_Recommended_Action": st.column_config.TextColumn("💡 Action",     width=200),
            }
            st.dataframe(res_df, use_container_width=True, height=400, column_config=col_cfg)

            # Expand a result
            st.markdown("**🔍 Expand a result**")
            expand_key = st.selectbox("Select ticket to review", [""]+list(res_df["Issue key"]), key="exp_res")
            if expand_key:
                res_row = res_df[res_df["Issue key"]==expand_key].iloc[0]
                ai_col_list = [c for c in res_row.index if c.startswith("AI_")]
                exp_cols = st.columns(2)
                for i, col in enumerate(ai_col_list):
                    with exp_cols[i%2]:
                        label = col.replace("AI_","").replace("_"," ")
                        val   = str(res_row[col])
                        if ";" in val and col in ["AI_Safety_Rating","AI_CSAT_Rating","AI_Reliability_Rating"]:
                            sp, rp = val.split(";",1)
                            c = score_color(sp)
                            st.markdown(f'<div class="card"><div style="font-size:11px; font-weight:700; color:#6B778C; text-transform:uppercase; margin-bottom:6px;">{label}</div><div style="font-size:28px; font-weight:700; color:{c};">{sp.strip()}<span style="font-size:14px; color:#6B778C;">/10</span></div><div style="font-size:12px; color:#344563; margin-top:4px;">{rp.strip()}</div></div>', unsafe_allow_html=True)
                        else:
                            st.markdown(f'<div class="card"><div style="font-size:11px; font-weight:700; color:#6B778C; text-transform:uppercase; margin-bottom:6px;">{label}</div><div style="font-size:13px; color:#172B4D; line-height:1.6;">{val}</div></div>', unsafe_allow_html=True)

            # Export enriched CSV
            export_df = fdf.copy()
            for k, res in st.session_state.ai_results.items():
                for col_name, value in res.items():
                    if col_name not in export_df.columns:
                        export_df[col_name] = ""
                    export_df.loc[export_df["Issue key"]==k, col_name] = value

            base_cols = ["Issue key","Summary","Status","Priority","Issue Type","Assignee","Reporter","Created","Updated"]
            ai_export_cols = [c for c in export_df.columns if c.startswith("AI_")]
            enriched_csv = export_df[base_cols+ai_export_cols].to_csv(index=False).encode()

            ex_c, _ = st.columns([2,4])
            with ex_c:
                st.download_button("⬇️  Export Enriched CSV", data=enriched_csv, file_name="jira_ai_enriched.csv", mime="text/csv", key="exp_ai")
    else:
        st.markdown('<div style="text-align:center; padding:60px; color:#A5ADBA; background:#F8F9FA; border-radius:8px; border:2px dashed #DFE1E6;"><div style="font-size:48px; margin-bottom:12px;">🤖</div><div style="font-size:16px; font-weight:600; color:#344563;">No analysis run yet</div><div style="font-size:13px; margin-top:6px;">Configure questions above and click Run Analysis</div></div>', unsafe_allow_html=True)

# ── Footer ──────────────────────────────────────────────────────────────────────
st.markdown('<div style="text-align:center; color:#97A0AF; font-size:11px; margin-top:32px; padding-top:16px; border-top:1px solid #DFE1E6;">🦈 SharkNinja Jira Dashboard &nbsp;·&nbsp; Powered by Streamlit &amp; OpenAI</div>', unsafe_allow_html=True)
