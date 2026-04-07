import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import re
import requests
from PIL import Image
from io import BytesIO

st.set_page_config(
    page_title="SharkNinja Jira Dashboard",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #F0F2F5; }
  [data-testid="stSidebar"] { background: #0052CC; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stTextInput label,
  [data-testid="stSidebar"] .stRadio label {
    color: #B3D4FF !important; font-size:11px; font-weight:700;
    text-transform:uppercase; letter-spacing:0.6px;
  }
  [data-testid="stSidebar"] hr { border-color: rgba(255,255,255,0.2) !important; }

  /* Metrics */
  [data-testid="metric-container"] {
    background: white; border-radius: 6px; padding: 16px 20px;
    border: 1px solid #DFE1E6; border-left: 4px solid #0052CC;
    box-shadow: 0 1px 3px rgba(0,0,0,0.06);
  }
  .metric-high [data-testid="metric-container"] { border-left-color: #FF5630 !important; }
  .metric-bug  [data-testid="metric-container"] { border-left-color: #FF991F !important; }
  [data-testid="stMetricValue"] { color: #172B4D; font-size: 26px; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #5E6C84; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px; }

  /* Cards */
  .card { background: white; border-radius: 6px; border: 1px solid #DFE1E6; padding: 16px; margin-bottom: 12px; box-shadow: 0 1px 3px rgba(0,0,0,0.04); }

  /* Top bar */
  .top-bar {
    background: linear-gradient(135deg, #0052CC 0%, #0065FF 100%);
    padding: 14px 24px; border-radius: 8px; margin-bottom: 16px;
    display: flex; align-items: center; justify-content: space-between;
    box-shadow: 0 2px 8px rgba(0,82,204,0.25);
  }
  .top-bar-left { display: flex; align-items: center; gap: 14px; }
  .top-bar h1 { color: white; margin: 0; font-size: 20px; font-weight: 700; }
  .top-bar .subtitle { color: #B3D4FF; font-size: 12px; margin: 2px 0 0 0; }
  .top-bar-badge { background: rgba(255,255,255,0.2); color: white; border-radius: 20px; padding: 4px 14px; font-size: 13px; font-weight: 600; }

  /* Section headers */
  .section-header {
    font-size: 11px; font-weight: 700; color: #5E6C84;
    text-transform: uppercase; letter-spacing: 0.8px;
    margin: 20px 0 10px 0; padding-bottom: 6px;
    border-bottom: 2px solid #0052CC;
  }

  /* Quick filters */
  .quick-filters { display: flex; gap: 8px; flex-wrap: wrap; margin-bottom: 14px; }
  .stButton > button {
    border-radius: 20px !important; font-size: 12px !important;
    font-weight: 600 !important; padding: 4px 14px !important;
    border: 1px solid #DFE1E6 !important; background: white !important;
    color: #42526E !important; transition: all 0.15s !important;
  }
  .stButton > button:hover { background: #DEEBFF !important; border-color: #B3D4FF !important; color: #0052CC !important; }
  .stButton > button:focus { outline: none !important; box-shadow: none !important; }

  /* Board */
  .board-col-header {
    border-radius: 4px; padding: 8px 12px; margin-bottom: 8px;
    font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.5px;
    display: flex; align-items: center; justify-content: space-between;
  }
  .board-count { background: rgba(0,0,0,0.12); border-radius: 10px; padding: 1px 8px; font-size: 11px; }
  .board-card {
    background: white; border-radius: 4px; padding: 10px 12px;
    margin-bottom: 6px; cursor: pointer;
    box-shadow: 0 1px 2px rgba(0,0,0,0.06);
    border: 1px solid #DFE1E6;
    transition: box-shadow 0.15s, border-color 0.15s;
  }
  .board-card:hover { box-shadow: 0 3px 8px rgba(0,0,0,0.12); border-color: #B3D4FF; }
  .board-card.selected { border: 2px solid #0052CC; box-shadow: 0 0 0 3px rgba(0,82,204,0.15); }

  /* Badges */
  .badge { display: inline-block; padding: 3px 9px; border-radius: 3px; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px; }
  .badge-new      { background: #DFE1E6; color: #42526E; }
  .badge-progress { background: #DEEBFF; color: #0052CC; }
  .badge-verify   { background: #EAE6FF; color: #403294; }
  .badge-rcca     { background: #FFF0B3; color: #7A5200; }
  .badge-hold     { background: #FFEBE6; color: #BF2600; }
  .badge-done     { background: #E3FCEF; color: #006644; }
  .badge-close    { background: #E3FCEF; color: #006644; }
  .badge-rtc      { background: #E3FCEF; color: #006644; }

  /* Detail panel */
  .detail-header { font-size: 20px; font-weight: 700; color: #172B4D; margin-bottom: 10px; line-height: 1.4; }
  .detail-meta-table { width: 100%; font-size: 13px; border-collapse: collapse; }
  .detail-meta-table tr { border-bottom: 1px solid #F4F5F7; }
  .detail-meta-table td { padding: 7px 4px; vertical-align: top; }
  .detail-meta-label { color: #6B778C; font-weight: 600; font-size: 12px; width: 110px; }
  .detail-section-title { font-size: 11px; font-weight: 700; color: #6B778C; text-transform: uppercase; letter-spacing: 0.6px; margin: 14px 0 8px 0; padding-bottom: 4px; border-bottom: 1px solid #DFE1E6; }

  /* Breadcrumb */
  .breadcrumb { font-size: 12px; color: #6B778C; margin-bottom: 12px; display: flex; align-items: center; gap: 6px; }
  .breadcrumb a { color: #0052CC; text-decoration: none; cursor: pointer; }
  .breadcrumb .sep { color: #97A0AF; }

  /* Text boxes */
  .desc-box { background: #F4F5F7; border-radius: 4px; border: 1px solid #DFE1E6; padding: 14px; font-size: 13px; color: #172B4D; line-height: 1.7; white-space: pre-wrap; word-break: break-word; max-height: 320px; overflow-y: auto; }
  .field-box { background: #F4F5F7; border-radius: 4px; border-left: 3px solid #DFE1E6; padding: 10px 14px; font-size: 13px; color: #172B4D; line-height: 1.6; white-space: pre-wrap; word-break: break-word; margin-bottom: 10px; }
  .field-box.expected { border-left-color: #36B37E; }
  .field-box.actual   { border-left-color: #FF5630; }
  .field-box.trigger  { border-left-color: #0052CC; }

  /* RCCA */
  .rcca-step { background: #F8F9FA; border: 1px solid #DFE1E6; border-radius: 4px; padding: 10px 14px; margin-bottom: 6px; }
  .rcca-step-label { font-size: 10px; font-weight: 700; color: #0052CC; text-transform: uppercase; letter-spacing: 0.6px; margin-bottom: 5px; }
  .rcca-step-value { font-size: 13px; color: #172B4D; line-height: 1.6; white-space: pre-wrap; word-break: break-word; }

  /* Comments */
  .comment-bubble { background: #F8F9FA; border: 1px solid #DFE1E6; border-radius: 6px; padding: 12px 14px; margin-bottom: 10px; }
  .comment-avatar { width: 28px; height: 28px; border-radius: 50%; background: #0052CC; color: white; font-size: 11px; font-weight: 700; display: inline-flex; align-items: center; justify-content: center; flex-shrink: 0; }
  .comment-author { font-weight: 600; font-size: 13px; color: #172B4D; }
  .comment-date   { font-size: 11px; color: #6B778C; }
  .comment-body   { font-size: 13px; color: #344563; line-height: 1.65; white-space: pre-wrap; word-break: break-word; margin-top: 6px; }

  /* Attachments */
  .attach-chip { display: inline-flex; align-items: center; gap: 6px; background: #F4F5F7; border: 1px solid #DFE1E6; border-radius: 4px; padding: 6px 12px; margin: 3px; font-size: 12px; color: #172B4D; text-decoration: none; font-weight: 500; }
  .attach-chip:hover { background: #DEEBFF; border-color: #B3D4FF; color: #0052CC; }

  /* List rows */
  .list-row { display: flex; align-items: center; padding: 9px 12px; border-bottom: 1px solid #F4F5F7; background: white; font-size: 13px; gap: 0; transition: background 0.1s; }
  .list-row:hover { background: #F4F5F7; }
  .list-row.selected { background: #EBF2FF; border-left: 3px solid #0052CC; }
  .list-header { display: flex; align-items: center; padding: 8px 12px; background: #F4F5F7; font-size: 11px; font-weight: 700; color: #5E6C84; text-transform: uppercase; letter-spacing: 0.5px; border-bottom: 2px solid #DFE1E6; border-radius: 4px 4px 0 0; }

  /* Pagination */
  .page-info { font-size: 12px; color: #6B778C; }

  /* Search */
  [data-testid="stTextInput"] input { border: 2px solid #DFE1E6; border-radius: 6px; background: white; font-size: 14px; }
  [data-testid="stTextInput"] input:focus { border-color: #0052CC; box-shadow: 0 0 0 2px rgba(0,82,204,0.12); }

  #MainMenu { visibility: hidden; }
  footer     { visibility: hidden; }
  header     { visibility: hidden; }
  [data-testid="stDecoration"] { display: none; }
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_data
def load_data(path) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    for col in ["Created", "Updated", "Due date", "Resolved"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    for col in ["Summary", "Assignee", "Reporter", "Status", "Priority",
                "Issue Type", "Project name", "Resolution"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unassigned" if col == "Assignee" else "").astype(str).str.strip()
    return df

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS
# ══════════════════════════════════════════════════════════════════════════════
def status_badge(s):
    cls = {"New":"badge-new","In Progress":"badge-progress","Verify":"badge-verify",
           "RCCA":"badge-rcca","On Hold":"badge-hold","Done":"badge-done",
           "Close":"badge-close","Ready to Close":"badge-rtc"}.get(str(s),"badge-new")
    return f'<span class="badge {cls}">{s}</span>'

def priority_icon(p):
    icon = {"Critical":"🔴","Highest":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}.get(str(p),"⚪")
    return f'{icon} {p}'

def type_icon(t):
    icon = {"Bug":"🐛","Task":"✅","Epic":"⚡","Sub-task":"↳","VA/VE":"🔧"}.get(str(t),"📋")
    return f'{icon} {t}'

def fmt_date(val):
    try:
        ts = pd.Timestamp(val)
        return "—" if pd.isna(ts) else ts.strftime("%b %d, %Y  %H:%M")
    except:
        return "—"

def fmt_date_short(val):
    try:
        ts = pd.Timestamp(val)
        return "—" if pd.isna(ts) else ts.strftime("%b %d, %Y")
    except:
        return "—"

def clean_jira_markup(text):
    text = str(text or "")
    text = re.sub(r'\[~accountid:[^\]]+\]', '@user', text)
    text = re.sub(r'\[([^\|]+)\|[^\]]+\|smart-link\]', r'\1', text)
    text = re.sub(r'\[([^\|]+)\|[^\]]+\]', r'\1', text)
    text = re.sub(r'\{color[^}]*\}', '', text)
    text = re.sub(r'\{[^}]+\}', '', text)
    return text.strip()

def parse_comments(row, comment_cols):
    comments = []
    for col in comment_cols:
        val = str(row.get(col, "") or "")
        if val.strip() in ("", "nan"):
            continue
        parts = val.split(";", 2)
        body = clean_jira_markup(parts[2].strip() if len(parts) > 2 else val.strip())
        if body:
            comments.append({
                "date":      parts[0].strip() if len(parts) > 0 else "",
                "author_id": parts[1].strip() if len(parts) > 1 else "",
                "body":      body,
            })
    return comments

def parse_attachments(row, attach_cols):
    attachments = []
    for col in attach_cols:
        val = str(row.get(col, "") or "")
        if val.strip() in ("", "nan"):
            continue
        parts = val.split(";")
        filename = parts[2].strip() if len(parts) > 2 else "file"
        url      = parts[3].strip() if len(parts) > 3 else ""
        if filename and filename != "nan":
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            attachments.append({
                "filename": filename, "url": url,
                "is_image": ext in ("png","jpg","jpeg","gif","webp","bmp"),
                "date": parts[0].strip() if parts else "",
            })
    return attachments

@st.cache_data(show_spinner=False)
def try_load_image(url: str):
    if not url:
        return None
    try:
        resp = requests.get(url, timeout=5)
        if resp.status_code == 200 and "image" in resp.headers.get("Content-Type",""):
            return Image.open(BytesIO(resp.content))
    except:
        pass
    return None

def get_sprint(row, all_cols):
    for col in ["Sprint", "Sprint.1", "Sprint.2", "Sprint.3"]:
        if col in all_cols:
            val = str(row.get(col, "") or "").strip()
            if val and val != "nan":
                return val
    return None

def get_epic(row, all_cols):
    col = "Custom field (Epic Name)"
    if col in all_cols:
        val = str(row.get(col, "") or "").strip()
        if val and val != "nan":
            return val
    return None

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
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
        st.error("⚠️ No data found. Please upload a Jira CSV export using the sidebar.")
        st.stop()

all_cols     = df.columns.tolist()
comment_cols = [c for c in all_cols if c == "Comment" or re.match(r"Comment\.\d+$", c)]
attach_cols  = [c for c in all_cols if c == "Attachment" or re.match(r"Attachment\.\d+$", c)]

RCCA_STEPS = {
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
RCCA_STEPS = {k: v for k, v in RCCA_STEPS.items() if v in all_cols}

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
    view_mode = st.radio("", ["🗂️ Board", "📋 List", "📊 Analytics"], index=1)

# ── Apply filters ──────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_projects: fdf = fdf[fdf["Project name"].isin(sel_projects)]
if sel_status:   fdf = fdf[fdf["Status"].isin(sel_status)]
if sel_priority: fdf = fdf[fdf["Priority"].isin(sel_priority)]
if sel_type:     fdf = fdf[fdf["Issue Type"].isin(sel_type)]
if sel_assignee: fdf = fdf[fdf["Assignee"].isin(sel_assignee)]
if date_from and date_to:
    fdf = fdf[(fdf["Created"].dt.date >= date_from) & (fdf["Created"].dt.date <= date_to)]

# Show live filter count at bottom of sidebar
with st.sidebar:
    st.markdown("---")
    total_all = len(df)
    total_filt = len(fdf)
    pct = int(100 * total_filt / total_all) if total_all else 0
    st.markdown(f"""
    <div style="background:rgba(255,255,255,0.15); border-radius:6px; padding:10px 12px; text-align:center;">
      <div style="font-size:22px; font-weight:700; color:white;">{total_filt:,}</div>
      <div style="font-size:11px; color:#B3D4FF; margin-top:2px;">of {total_all:,} issues ({pct}%)</div>
    </div>
    """, unsafe_allow_html=True)

# ── Session state ──────────────────────────────────────────────────────────────
if "selected_key" not in st.session_state:
    st.session_state.selected_key = None
if "list_page" not in st.session_state:
    st.session_state.list_page = 0

PAGE_SIZE = 50

# ══════════════════════════════════════════════════════════════════════════════
#  TOP BAR + SEARCH + KPIs
# ══════════════════════════════════════════════════════════════════════════════
open_count = len(fdf[~fdf["Status"].isin(["Close","Done","Ready to Close"])])
closed     = len(fdf[fdf["Status"].isin(["Close","Done","Ready to Close"])])
bugs       = len(fdf[fdf["Issue Type"] == "Bug"])
high_pri   = len(fdf[fdf["Priority"].isin(["High","Highest","Critical"])])

st.markdown(f"""
<div class="top-bar">
  <div class="top-bar-left">
    <span style="font-size:28px; line-height:1;">🦈</span>
    <div>
      <h1>SharkNinja · Jira Dashboard</h1>
      <p class="subtitle">Issue tracking &amp; analytics</p>
    </div>
  </div>
  <div>
    <span class="top-bar-badge">{total_filt:,} issues</span>
  </div>
</div>
""", unsafe_allow_html=True)

# ── Search ─────────────────────────────────────────────────────────────────────
search = st.text_input("", placeholder="🔎  Search by summary or ticket key…  (e.g. HD430 or PCOPT-1821)", label_visibility="collapsed")
if search:
    fdf = fdf[
        fdf["Summary"].str.contains(search, case=False, na=False) |
        fdf["Issue key"].str.contains(search, case=False, na=False)
    ]
    st.session_state.list_page = 0

# ── Quick filters ──────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Quick Filters</div>', unsafe_allow_html=True)
qf_cols = st.columns(6)
quick_filters = {
    "🔓 Open Only":      lambda d: d[~d["Status"].isin(["Close","Done","Ready to Close"])],
    "🔴 High Priority":  lambda d: d[d["Priority"].isin(["High","Highest","Critical"])],
    "🐛 Bugs Only":      lambda d: d[d["Issue Type"] == "Bug"],
    "🔬 RCCA Status":    lambda d: d[d["Status"] == "RCCA"],
    "⏳ On Hold":         lambda d: d[d["Status"] == "On Hold"],
    "✅ Verify":          lambda d: d[d["Status"] == "Verify"],
}
for i, (label, fn) in enumerate(quick_filters.items()):
    with qf_cols[i]:
        count = len(fn(fdf))
        if st.button(f"{label}  ({count})", key=f"qf_{i}"):
            fdf = fn(fdf)
            st.session_state.list_page = 0

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">Summary</div>', unsafe_allow_html=True)
total = len(fdf)
open_count = len(fdf[~fdf["Status"].isin(["Close","Done","Ready to Close"])])
closed     = len(fdf[fdf["Status"].isin(["Close","Done","Ready to Close"])])
bugs       = len(fdf[fdf["Issue Type"] == "Bug"])
high_pri   = len(fdf[fdf["Priority"].isin(["High","Highest","Critical"])])

c1,c2,c3,c4,c5,c6 = st.columns(6)
c1.metric("Total Issues",   f"{total:,}")
c2.metric("Open",           f"{open_count:,}", delta=f"{open_count-closed:+,} vs closed", delta_color="inverse")
c3.metric("Closed / Done",  f"{closed:,}")
c4.metric("Bugs",           f"{bugs:,}")
c5.metric("High Priority",  f"{high_pri:,}")
close_rate = int(100 * closed / total) if total else 0
c6.metric("Close Rate",     f"{close_rate}%")

# Export button
st.markdown("")
col_exp, _ = st.columns([1, 5])
with col_exp:
    csv_bytes = fdf[["Issue key","Summary","Status","Priority","Issue Type","Assignee","Reporter","Created","Updated"]].to_csv(index=False).encode("utf-8")
    st.download_button(
        label="⬇️  Export filtered CSV",
        data=csv_bytes,
        file_name="jira_filtered.csv",
        mime="text/csv",
        key="export_csv",
    )

st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET DETAIL PANEL
# ══════════════════════════════════════════════════════════════════════════════
def render_ticket_detail(row, source_view=""):
    comments    = parse_comments(row, comment_cols)
    attachments = parse_attachments(row, attach_cols)
    images      = [a for a in attachments if a["is_image"]]
    files       = [a for a in attachments if not a["is_image"]]
    sprint      = get_sprint(row, all_cols)
    epic        = get_epic(row, all_cols)

    # Breadcrumb
    st.markdown(f"""
    <div class="breadcrumb">
      <span>🦈 SharkNinja</span>
      <span class="sep">›</span>
      <span>{row['Project name']}</span>
      <span class="sep">›</span>
      <strong style="color:#172B4D;">{row['Issue key']}</strong>
    </div>
    """, unsafe_allow_html=True)

    # Header card
    rcca_has_data = any(
        str(row.get(v,"") or "").strip() not in ("","nan")
        for v in RCCA_STEPS.values()
    )
    rcca_indicator = ' <span style="background:#FFF0B3; color:#7A5200; font-size:10px; font-weight:700; padding:2px 7px; border-radius:3px; vertical-align:middle;">RCCA DATA</span>' if rcca_has_data else ''

    st.markdown(f"""
    <div class="card" style="border-left: 5px solid #0052CC;">
      <div class="detail-header">{row['Summary']}{rcca_indicator}</div>
      <div style="display:flex; align-items:center; gap:10px; flex-wrap:wrap; margin-bottom:8px;">
        {status_badge(row['Status'])}
        <span style="font-size:13px; color:#5E6C84;">{type_icon(row['Issue Type'])}</span>
        <span style="font-size:13px; color:#5E6C84;">{priority_icon(row['Priority'])}</span>
        {'<span style="font-size:12px; background:#EAE6FF; color:#403294; padding:2px 8px; border-radius:3px; font-weight:600;">⚡ ' + epic + '</span>' if epic else ''}
        {'<span style="font-size:12px; background:#DEEBFF; color:#0052CC; padding:2px 8px; border-radius:3px; font-weight:600;">🏃 ' + sprint[:30] + '</span>' if sprint else ''}
      </div>
      <div style="font-size:12px; color:#97A0AF; font-family:monospace; font-weight:600;">
        {row['Issue key']} &nbsp;·&nbsp; {row['Project name']}
      </div>
    </div>
    """, unsafe_allow_html=True)

    close_col, _ = st.columns([1, 5])
    with close_col:
        if st.button("✕  Close", key=f"close_{row['Issue key']}", help="Close detail panel"):
            st.session_state.selected_key = None
            st.rerun()

    left, right = st.columns([3, 1])

    with right:
        st.markdown(f"""
        <div class="card" style="background:#F8F9FA;">
          <div class="detail-section-title">Details</div>
          <table class="detail-meta-table">
            <tr><td class="detail-meta-label">Assignee</td>
                <td><strong>{row['Assignee']}</strong></td></tr>
            <tr><td class="detail-meta-label">Reporter</td>
                <td style="color:#344563;">{row['Reporter']}</td></tr>
            <tr><td class="detail-meta-label">Priority</td>
                <td>{priority_icon(row['Priority'])}</td></tr>
            <tr><td class="detail-meta-label">Status</td>
                <td>{status_badge(row['Status'])}</td></tr>
            <tr><td class="detail-meta-label">Resolution</td>
                <td style="color:#6B778C; font-size:12px;">{row.get('Resolution','') or '—'}</td></tr>
            <tr><td class="detail-meta-label">Created</td>
                <td style="color:#6B778C; font-size:12px;">{fmt_date(row['Created'])}</td></tr>
            <tr><td class="detail-meta-label">Updated</td>
                <td style="color:#6B778C; font-size:12px;">{fmt_date(row['Updated'])}</td></tr>
            <tr><td class="detail-meta-label">Due Date</td>
                <td style="color:#6B778C; font-size:12px;">{fmt_date(row.get('Due date'))}</td></tr>
            {'<tr><td class="detail-meta-label">Sprint</td><td style="color:#0052CC; font-size:12px; font-weight:600;">' + (sprint or '—') + '</td></tr>' if sprint else ''}
            {'<tr><td class="detail-meta-label">Epic</td><td style="color:#403294; font-size:12px; font-weight:600;">' + (epic or '—') + '</td></tr>' if epic else ''}
          </table>
        </div>
        """, unsafe_allow_html=True)

        if files:
            st.markdown('<div class="detail-section-title">📄 Files</div>', unsafe_allow_html=True)
            chips = "".join(
                f'<a href="{f["url"]}" target="_blank" class="attach-chip">📄 {f["filename"]}</a>'
                if f["url"] else f'<span class="attach-chip">📄 {f["filename"]}</span>'
                for f in files
            )
            st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{chips}</div>', unsafe_allow_html=True)

    with left:
        tab_labels = [
            "📝  Description",
            f"🔬  RCCA{'  ✓' if rcca_has_data else ''}",
            f"💬  Comments ({len(comments)})",
            f"🖼️  Images ({len(images)})",
        ]
        tab1, tab2, tab3, tab4 = st.tabs(tab_labels)

        with tab1:
            desc = clean_jira_markup(row.get("Description","") or "")
            if desc and desc != "nan":
                st.markdown(f'<div class="desc-box">{desc[:3000]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="desc-box" style="color:#A5ADBA; font-style:italic; text-align:center; padding:30px;">No description provided.</div>', unsafe_allow_html=True)

            for label, field, css_cls in [
                ("✅  Expected Behavior", "Custom field (Expected Behavior)", "expected"),
                ("❌  Actual Behavior",   "Custom field (Actual Behavior)",   "actual"),
                ("🔁  Trigger / Scenario","Custom field (Trigger / Scenario)","trigger"),
            ]:
                if field in all_cols:
                    val = clean_jira_markup(row.get(field,"") or "")
                    if val and val != "nan":
                        st.markdown(f'<div style="font-size:11px; font-weight:700; color:#5E6C84; text-transform:uppercase; letter-spacing:0.5px; margin:12px 0 5px 0;">{label}</div>', unsafe_allow_html=True)
                        st.markdown(f'<div class="field-box {css_cls}">{val[:500]}</div>', unsafe_allow_html=True)

        with tab2:
            d_groups = {
                "🔴  D2 · Problem Definition": [k for k in RCCA_STEPS if k.startswith("D2")],
                "🟠  D3 · Containment":         [k for k in RCCA_STEPS if k.startswith("D3")],
                "🟡  D4 · Root Cause":          [k for k in RCCA_STEPS if k.startswith("D4")],
                "🔵  D5 · Temp Corrective":     [k for k in RCCA_STEPS if k.startswith("D5")],
                "🟢  D6 · Perm Corrective":     [k for k in RCCA_STEPS if k.startswith("D6")],
                "✅  D7–D8 · Close Out":        [k for k in RCCA_STEPS if k.startswith("D7") or k.startswith("D8")],
                "📋  General Fields":           [k for k in RCCA_STEPS if not any(k.startswith(x) for x in ["D2","D3","D4","D5","D6","D7","D8"])],
            }
            has_any = False
            for group_label, keys in d_groups.items():
                populated = []
                for key in keys:
                    val = clean_jira_markup(row.get(RCCA_STEPS[key],"") or "")
                    if val and val != "nan":
                        populated.append((key, val))
                        has_any = True
                if populated:
                    st.markdown(f'<div style="font-size:12px; font-weight:700; color:#344563; margin:14px 0 8px 0;">{group_label}</div>', unsafe_allow_html=True)
                    st.markdown("".join(f'<div class="rcca-step"><div class="rcca-step-label">{k}</div><div class="rcca-step-value">{v[:600]}</div></div>' for k,v in populated), unsafe_allow_html=True)
            if not has_any:
                st.markdown('<div style="text-align:center; padding:50px 20px; color:#A5ADBA;"><div style="font-size:36px; margin-bottom:10px;">🔬</div><div style="font-size:14px; font-weight:600;">No RCCA data for this ticket</div><div style="font-size:12px; margin-top:4px;">D2–D8 fields will appear here when populated.</div></div>', unsafe_allow_html=True)

        with tab3:
            if comments:
                for c in comments:
                    initials = (c["author_id"][:2]).upper() if c["author_id"] else "?"
                    author   = c["author_id"][:16] + "…" if len(c["author_id"]) > 18 else c["author_id"]
                    st.markdown(f"""
                    <div class="comment-bubble">
                      <div style="display:flex; align-items:center; gap:8px; margin-bottom:6px;">
                        <div class="comment-avatar">{initials}</div>
                        <div>
                          <div class="comment-author">{author}</div>
                          <div class="comment-date">{c['date']}</div>
                        </div>
                      </div>
                      <div class="comment-body">{c['body'][:1000]}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center; padding:50px 20px; color:#A5ADBA;"><div style="font-size:36px; margin-bottom:10px;">💬</div><div style="font-size:14px; font-weight:600;">No comments on this ticket</div></div>', unsafe_allow_html=True)

        with tab4:
            if images:
                loaded_any = False
                for att in images:
                    img = try_load_image(att["url"]) if att["url"] else None
                    if img:
                        st.image(img, caption=att["filename"], use_container_width=True)
                        loaded_any = True
                    else:
                        link = f'<a href="{att["url"]}" target="_blank" class="attach-chip">🖼️ {att["filename"]}</a>' if att["url"] else f'<span class="attach-chip">🖼️ {att["filename"]}</span>'
                        st.markdown(link, unsafe_allow_html=True)
                if not loaded_any:
                    st.info("🔐 Images are hosted on Jira and require login to view. Links above open them in your browser.", icon="ℹ️")
            else:
                st.markdown('<div style="text-align:center; padding:50px 20px; color:#A5ADBA;"><div style="font-size:36px; margin-bottom:10px;">🖼️</div><div style="font-size:14px; font-weight:600;">No images attached to this ticket</div></div>', unsafe_allow_html=True)

    st.markdown('<hr style="border:none; border-top:2px solid #DFE1E6; margin:20px 0;">', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "🗂️ Board":
    if st.session_state.selected_key:
        match = fdf[fdf["Issue key"] == st.session_state.selected_key]
        if not match.empty:
            st.markdown('<div class="section-header">Ticket Detail</div>', unsafe_allow_html=True)
            render_ticket_detail(match.iloc[0], source_view="board")

    st.markdown('<div class="section-header">Board</div>', unsafe_allow_html=True)

    STATUS_ORDER = ["New","In Progress","RCCA","Verify","On Hold","Ready to Close","Done","Close"]
    present = [s for s in STATUS_ORDER if s in fdf["Status"].unique()]
    for s in fdf["Status"].unique():
        if s not in present:
            present.append(s)

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
    PRI_COLORS = {"Critical":"#BF2600","Highest":"#BF2600","High":"#FF5630","Medium":"#FF991F","Low":"#36B37E"}

    cols = st.columns(min(len(present), 6))
    for col, status in zip(cols, present[:6]):
        grp = fdf[fdf["Status"] == status].head(25)
        bg, fg = COL_COLORS.get(status, ("#F4F5F7","#42526E"))
        total_in_status = len(fdf[fdf["Status"] == status])
        with col:
            st.markdown(f"""
            <div class="board-col-header" style="background:{bg}; color:{fg};">
              <span>{status.upper()}</span>
              <span class="board-count">{total_in_status}</span>
            </div>""", unsafe_allow_html=True)

            for _, row in grp.iterrows():
                pc = PRI_COLORS.get(row["Priority"], "#97A0AF")
                is_sel = st.session_state.selected_key == row["Issue key"]
                sel_class = "selected" if is_sel else ""
                border = f"border: 2px solid #0052CC; border-left: 3px solid {pc};" if is_sel else f"border: 1px solid #DFE1E6; border-left: 3px solid {pc};"

                st.markdown(f"""
                <div class="board-card {sel_class}" style="{border}">
                  <div style="color:#0052CC; font-weight:700; font-family:monospace; font-size:11px; margin-bottom:5px;">{row['Issue key']}</div>
                  <div style="color:#172B4D; font-size:12px; line-height:1.4; margin-bottom:8px;">{str(row['Summary'])[:80]}{'…' if len(str(row['Summary']))>80 else ''}</div>
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:11px; color:#6B778C;">{type_icon(row['Issue Type'])}</span>
                    <span style="width:22px; height:22px; border-radius:50%; background:{pc}; color:white; font-size:10px; font-weight:700; display:inline-flex; align-items:center; justify-content:center;" title="{row['Assignee']}">{str(row['Assignee'])[:1].upper()}</span>
                  </div>
                </div>""", unsafe_allow_html=True)

                # Invisible full-width button overlaying the card
                if st.button(row["Issue key"], key=f"b_{row['Issue key']}", help=f"Open {row['Issue key']}"):
                    st.session_state.selected_key = row["Issue key"] if not is_sel else None
                    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📋 List":
    if st.session_state.selected_key:
        match = fdf[fdf["Issue key"] == st.session_state.selected_key]
        if not match.empty:
            st.markdown('<div class="section-header">Ticket Detail</div>', unsafe_allow_html=True)
            render_ticket_detail(match.iloc[0], source_view="list")

    st.markdown('<div class="section-header">Issues</div>', unsafe_allow_html=True)

    sc1, sc2, sc3 = st.columns([2, 2, 4])
    with sc1: sort_col = st.selectbox("Sort by", ["Created","Updated","Priority","Status","Issue key"])
    with sc2: sort_dir = st.selectbox("Order",   ["Descending","Ascending"])

    ascending = sort_dir == "Ascending"
    if sort_col == "Priority":
        fdf = fdf.copy()
        fdf["_ps"] = fdf["Priority"].map({"Critical":0,"Highest":1,"High":2,"Medium":3,"Low":4}).fillna(5)
        fdf = fdf.sort_values("_ps", ascending=ascending)
    else:
        fdf = fdf.sort_values(sort_col, ascending=ascending, na_position="last")

    # Pagination
    total_pages = max(1, (len(fdf) + PAGE_SIZE - 1) // PAGE_SIZE)
    page = min(st.session_state.list_page, total_pages - 1)
    page_df = fdf.iloc[page * PAGE_SIZE : (page + 1) * PAGE_SIZE]

    # Header
    h_cols = st.columns([1.4, 4, 1.4, 1.5, 1.3, 2.2, 1.5, 1.5])
    for hcol, label in zip(h_cols, ["KEY","SUMMARY","TYPE","STATUS","PRIORITY","ASSIGNEE","CREATED","UPDATED"]):
        hcol.markdown(f'<div style="font-size:11px; font-weight:700; color:#5E6C84; text-transform:uppercase; letter-spacing:0.5px; padding:8px 0 6px 0; border-bottom:2px solid #DFE1E6;">{label}</div>', unsafe_allow_html=True)

    for _, row in page_df.iterrows():
        cd = fmt_date_short(row["Created"])
        ud = fmt_date_short(row["Updated"])
        is_sel = st.session_state.selected_key == row["Issue key"]
        bg     = "#EBF2FF" if is_sel else "white"
        border = "border-left: 3px solid #0052CC;" if is_sel else "border-left: 3px solid transparent;"
        cell   = f"background:{bg}; {border} padding:8px 4px; border-bottom:1px solid #F4F5F7; font-size:13px;"

        r_cols = st.columns([1.4, 4, 1.4, 1.5, 1.3, 2.2, 1.5, 1.5])
        with r_cols[0]:
            if st.button(row["Issue key"], key=f"l_{row['Issue key']}", help=f"Open {row['Issue key']}"):
                st.session_state.selected_key = row["Issue key"] if not is_sel else None
                st.rerun()
        r_cols[1].markdown(f'<div style="{cell} overflow:hidden; text-overflow:ellipsis; white-space:nowrap; color:#172B4D;" title="{row["Summary"]}">{str(row["Summary"])[:60]}{"…" if len(str(row["Summary"]))>60 else ""}</div>', unsafe_allow_html=True)
        r_cols[2].markdown(f'<div style="{cell} color:#5E6C84;">{type_icon(row["Issue Type"])}</div>', unsafe_allow_html=True)
        r_cols[3].markdown(f'<div style="{cell}">{status_badge(row["Status"])}</div>', unsafe_allow_html=True)
        r_cols[4].markdown(f'<div style="{cell}">{priority_icon(row["Priority"])}</div>', unsafe_allow_html=True)
        r_cols[5].markdown(f'<div style="{cell} color:#5E6C84; overflow:hidden; text-overflow:ellipsis; white-space:nowrap;">{row["Assignee"]}</div>', unsafe_allow_html=True)
        r_cols[6].markdown(f'<div style="{cell} color:#97A0AF; font-size:12px;">{cd}</div>', unsafe_allow_html=True)
        r_cols[7].markdown(f'<div style="{cell} color:#97A0AF; font-size:12px;">{ud}</div>', unsafe_allow_html=True)

    # Pagination controls
    st.markdown("")
    pg1, pg2, pg3, pg4, _ = st.columns([1, 1, 2, 1, 3])
    with pg1:
        if st.button("◀  Prev", disabled=(page == 0), key="prev_page"):
            st.session_state.list_page = max(0, page - 1)
            st.rerun()
    with pg2:
        if st.button("Next  ▶", disabled=(page >= total_pages - 1), key="next_page"):
            st.session_state.list_page = min(total_pages - 1, page + 1)
            st.rerun()
    with pg3:
        start = page * PAGE_SIZE + 1
        end   = min((page + 1) * PAGE_SIZE, len(fdf))
        st.markdown(f'<div style="font-size:12px; color:#6B778C; padding-top:10px;">Showing {start}–{end} of {len(fdf):,} issues &nbsp;·&nbsp; Page {page+1} of {total_pages}</div>', unsafe_allow_html=True)
    with pg4:
        jump = st.number_input("Go to page", min_value=1, max_value=total_pages, value=page+1, step=1, label_visibility="collapsed")
        if jump - 1 != page:
            st.session_state.list_page = jump - 1
            st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "📊 Analytics":
    JB = "#0052CC"
    JC = ["#0052CC","#0065FF","#4C9AFF","#B3D4FF","#172B4D","#36B37E","#FF5630","#FF991F","#6554C0","#00B8D9"]
    BASE = dict(
        paper_bgcolor="white", plot_bgcolor="white",
        font=dict(family="Inter, Arial, sans-serif", size=12, color="#172B4D"),
        margin=dict(t=10, b=10, l=10, r=10),
    )

    r1l, r1r = st.columns(2)
    with r1l:
        st.markdown('<div class="section-header">Issues by Status</div>', unsafe_allow_html=True)
        sc = fdf["Status"].value_counts().reset_index(); sc.columns = ["Status","Count"]
        fig = px.bar(sc, x="Status", y="Count", color="Status", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(**BASE, showlegend=False, height=300, xaxis=dict(gridcolor="#F4F5F7", title=""), yaxis=dict(gridcolor="#F4F5F7", title=""))
        st.plotly_chart(fig, use_container_width=True)

    with r1r:
        st.markdown('<div class="section-header">Issues by Priority</div>', unsafe_allow_html=True)
        pc = fdf["Priority"].value_counts().reset_index(); pc.columns = ["Priority","Count"]
        fig = px.pie(pc, names="Priority", values="Count", hole=0.5, color="Priority",
                     color_discrete_map={"Critical":"#BF2600","Highest":"#FF5630","High":"#FF7452","Medium":"#FF991F","Low":"#36B37E"})
        fig.update_traces(textposition="inside", textinfo="percent+label", marker=dict(line=dict(color="white", width=2)))
        fig.update_layout(**BASE, height=300, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

    r2l, r2r = st.columns(2)
    with r2l:
        st.markdown('<div class="section-header">Issues Created Over Time</div>', unsafe_allow_html=True)
        ts = fdf.dropna(subset=["Created"]).copy()
        ts["Week"] = ts["Created"].dt.to_period("W").dt.start_time
        tsg = ts.groupby("Week").size().reset_index(name="Count")
        fig = px.area(tsg, x="Week", y="Count", color_discrete_sequence=[JB])
        fig.update_traces(fill="tozeroy", line_color=JB, fillcolor="rgba(0,82,204,0.10)", line_width=2)
        fig.update_layout(**BASE, height=300, xaxis=dict(gridcolor="#F4F5F7", title=""), yaxis=dict(gridcolor="#F4F5F7", title=""))
        st.plotly_chart(fig, use_container_width=True)

    with r2r:
        st.markdown('<div class="section-header">Top Assignees</div>', unsafe_allow_html=True)
        ac = fdf[fdf["Assignee"] != "Unassigned"]["Assignee"].value_counts().head(12).reset_index(); ac.columns = ["Assignee","Count"]
        fig = px.bar(ac, x="Count", y="Assignee", orientation="h", color="Count",
                     color_continuous_scale=["#DEEBFF", JB], text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(**BASE, coloraxis_showscale=False, height=360,
                          xaxis=dict(gridcolor="#F4F5F7", title=""),
                          yaxis=dict(gridcolor="#F4F5F7", title="", categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    # Open vs Closed trend
    st.markdown('<div class="section-header">Open vs Closed Over Time</div>', unsafe_allow_html=True)
    ts2 = fdf.dropna(subset=["Created"]).copy()
    ts2["Week"]   = ts2["Created"].dt.to_period("W").dt.start_time
    ts2["Is Open"] = ~ts2["Status"].isin(["Close","Done","Ready to Close"])
    oc = ts2.groupby(["Week","Is Open"]).size().reset_index(name="Count")
    oc["Type"] = oc["Is Open"].map({True:"Open", False:"Closed"})
    fig = px.bar(oc, x="Week", y="Count", color="Type",
                 color_discrete_map={"Open":"#FF5630","Closed":"#36B37E"},
                 barmode="stack")
    fig.update_layout(**BASE, height=280, xaxis=dict(gridcolor="#F4F5F7", title=""), yaxis=dict(gridcolor="#F4F5F7", title=""),
                      legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)

    r3l, r3r = st.columns(2)
    with r3l:
        st.markdown('<div class="section-header">Issue Type Breakdown</div>', unsafe_allow_html=True)
        tc = fdf["Issue Type"].value_counts().reset_index(); tc.columns = ["Type","Count"]
        fig = px.bar(tc, x="Type", y="Count", color="Type", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(**BASE, showlegend=False, height=280, xaxis=dict(gridcolor="#F4F5F7", title=""), yaxis=dict(gridcolor="#F4F5F7", title=""))
        st.plotly_chart(fig, use_container_width=True)

    with r3r:
        st.markdown('<div class="section-header">Resolution Breakdown</div>', unsafe_allow_html=True)
        rc = fdf["Resolution"].replace("","Unresolved").value_counts().head(8).reset_index(); rc.columns = ["Resolution","Count"]
        fig = px.bar(rc, x="Count", y="Resolution", orientation="h", color="Count",
                     color_continuous_scale=["#DEEBFF", JB], text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(**BASE, coloraxis_showscale=False, height=280,
                          xaxis=dict(gridcolor="#F4F5F7", title=""),
                          yaxis=dict(gridcolor="#F4F5F7", title="", categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Status × Priority Heatmap</div>', unsafe_allow_html=True)
    heat  = fdf.groupby(["Status","Priority"]).size().reset_index(name="Count")
    pivot = heat.pivot(index="Status", columns="Priority", values="Count").fillna(0)
    fig = go.Figure(go.Heatmap(
        z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
        colorscale=[[0,"#F0F4FF"],[0.5,"#4C9AFF"],[1,JB]],
        text=pivot.values.astype(int), texttemplate="%{text}",
        showscale=True, xgap=2, ygap=2,
    ))
    fig.update_layout(**BASE, height=300)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div style="text-align:center; color:#97A0AF; font-size:11px; margin-top:32px; padding-top:16px; border-top:1px solid #DFE1E6;">🦈 SharkNinja Jira Dashboard &nbsp;·&nbsp; Powered by Streamlit</div>', unsafe_allow_html=True)
