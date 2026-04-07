import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import re

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SharkNinja Jira Dashboard",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  [data-testid="stAppViewContainer"] { background: #F4F5F7; }
  [data-testid="stSidebar"] { background: #0052CC; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stTextInput label { color: #B3D4FF !important; font-size:12px; font-weight:600; text-transform:uppercase; letter-spacing:0.5px; }
  [data-testid="stSidebar"] h1,[data-testid="stSidebar"] h2,[data-testid="stSidebar"] h3 { color:white !important; }
  [data-testid="metric-container"] { background:white; border-radius:4px; padding:16px; border:1px solid #DFE1E6; box-shadow:0 1px 2px rgba(0,0,0,0.05); }
  [data-testid="stMetricValue"] { color:#172B4D; font-size:28px; font-weight:700; }
  [data-testid="stMetricLabel"] { color:#6B778C; font-size:12px; font-weight:600; text-transform:uppercase; }
  .section-header { font-size:16px; font-weight:600; color:#172B4D; margin:16px 0 8px 0; padding-bottom:8px; border-bottom:2px solid #0052CC; }
  .badge { display:inline-block; padding:2px 8px; border-radius:3px; font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.3px; }
  .badge-new      { background:#DFE1E6; color:#42526E; }
  .badge-progress { background:#DEEBFF; color:#0052CC; }
  .badge-verify   { background:#EAE6FF; color:#403294; }
  .badge-rcca     { background:#FFF0B3; color:#974F0C; }
  .badge-hold     { background:#FFEBE6; color:#BF2600; }
  .badge-done     { background:#E3FCEF; color:#006644; }
  .badge-close    { background:#E3FCEF; color:#006644; }
  .badge-rtc      { background:#E3FCEF; color:#006644; }
  .issue-table { width:100%; border-collapse:collapse; }
  .issue-table th { background:#F4F5F7; color:#5E6C84; font-size:11px; font-weight:700; text-transform:uppercase; padding:8px 12px; border-bottom:2px solid #DFE1E6; text-align:left; }
  .issue-table td { padding:10px 12px; border-bottom:1px solid #F4F5F7; font-size:13px; color:#172B4D; vertical-align:middle; }
  .issue-table tr:hover td { background:#FAFBFC; }
  .issue-key { color:#0052CC; font-weight:600; font-family:monospace; }
  .issue-summary { max-width:400px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }
  .top-bar { background:#0052CC; padding:10px 20px; border-radius:4px; margin-bottom:20px; display:flex; align-items:center; gap:12px; }
  .top-bar h1 { color:white; margin:0; font-size:20px; }
  .card { background:white; border-radius:4px; border:1px solid #DFE1E6; padding:16px; margin-bottom:16px; }
  .detail-header { font-size:22px; font-weight:700; color:#172B4D; margin-bottom:12px; line-height:1.3; }
  .detail-meta-table { width:100%; font-size:13px; }
  .detail-meta-table td { padding:5px 4px; vertical-align:top; }
  .detail-meta-label { color:#6B778C; font-weight:600; width:140px; }
  .detail-section-title { font-size:13px; font-weight:700; color:#172B4D; text-transform:uppercase; letter-spacing:0.5px; margin:16px 0 8px 0; padding-bottom:4px; border-bottom:1px solid #DFE1E6; }
  .desc-box { background:#F4F5F7; border-radius:4px; padding:12px; font-size:13px; color:#172B4D; line-height:1.6; white-space:pre-wrap; word-break:break-word; }
  .rcca-step { background:white; border:1px solid #DFE1E6; border-radius:4px; padding:12px 14px; margin-bottom:8px; }
  .rcca-step-label { font-size:11px; font-weight:700; color:#0052CC; text-transform:uppercase; letter-spacing:0.5px; margin-bottom:4px; }
  .rcca-step-value { font-size:13px; color:#172B4D; line-height:1.5; white-space:pre-wrap; word-break:break-word; }
  .comment-bubble { background:white; border:1px solid #DFE1E6; border-radius:4px; padding:12px 14px; margin-bottom:10px; }
  .comment-author { font-weight:600; font-size:12px; color:#172B4D; }
  .comment-date { font-size:11px; color:#6B778C; margin-left:8px; }
  .comment-body { font-size:13px; color:#172B4D; line-height:1.6; margin-top:6px; white-space:pre-wrap; word-break:break-word; }
  .attach-chip { display:inline-flex; align-items:center; gap:6px; background:#DEEBFF; border:1px solid #B3D4FF; border-radius:3px; padding:5px 10px; margin:4px; font-size:12px; color:#0052CC; text-decoration:none; font-weight:500; }
  .attach-chip:hover { background:#B3D4FF; }
  #MainMenu { visibility:hidden; }
  footer { visibility:hidden; }
  header { visibility:hidden; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
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

# ── Helpers ────────────────────────────────────────────────────────────────────
def status_badge(s):
    cls_map = {"New":"badge-new","In Progress":"badge-progress","Verify":"badge-verify",
               "RCCA":"badge-rcca","On Hold":"badge-hold","Done":"badge-done",
               "Close":"badge-close","Ready to Close":"badge-rtc"}
    return f'<span class="badge {cls_map.get(str(s),"badge-new")}">{s}</span>'

def priority_icon(p):
    return {"Critical":"🔴","Highest":"🔴","High":"🟠","Medium":"🟡","Low":"🟢"}.get(str(p),"⚪") + f" {p}"

def type_icon(t):
    return {"Bug":"🐛","Task":"✅","Epic":"⚡","Sub-task":"↳","VA/VE":"🔧"}.get(str(t),"📋") + f" {t}"

def fmt_date(val):
    if val is None or (hasattr(val, '__class__') and val.__class__.__name__ == 'float'):
        return "—"
    try:
        ts = pd.Timestamp(val)
        if pd.isna(ts):
            return "—"
        return ts.strftime("%b %d, %Y %H:%M")
    except:
        return str(val)

def parse_comments(row, comment_cols):
    comments = []
    for col in comment_cols:
        val = str(row.get(col, "") or "")
        if val.strip() in ("", "nan"):
            continue
        parts = val.split(";", 2)
        date_str  = parts[0].strip() if len(parts) > 0 else ""
        author_id = parts[1].strip() if len(parts) > 1 else ""
        body      = parts[2].strip() if len(parts) > 2 else val.strip()
        body = re.sub(r'\[~accountid:[^\]]+\]', '@user', body)
        body = re.sub(r'\[([^\|]+)\|[^\]]+\|smart-link\]', r'\1', body)
        body = re.sub(r'\[([^\|]+)\|[^\]]+\]', r'\1', body)
        if body:
            comments.append({"date": date_str, "author_id": author_id, "body": body})
    return comments

def parse_attachments(row, attach_cols):
    attachments = []
    for col in attach_cols:
        val = str(row.get(col, "") or "")
        if val.strip() in ("", "nan"):
            continue
        parts = val.split(";")
        date_str = parts[0].strip() if len(parts) > 0 else ""
        filename = parts[2].strip() if len(parts) > 2 else "attachment"
        url      = parts[3].strip() if len(parts) > 3 else ""
        if filename and filename != "nan":
            ext = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
            is_image = ext in ("png","jpg","jpeg","gif","webp","bmp")
            attachments.append({"date": date_str, "filename": filename, "url": url, "is_image": is_image})
    return attachments

# ── Sidebar ────────────────────────────────────────────────────────────────────
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
        st.error("Please upload a Jira CSV export to get started.")
        st.stop()

all_cols      = df.columns.tolist()
comment_cols  = [c for c in all_cols if c == "Comment" or re.match(r"Comment\.\d+$", c)]
attach_cols   = [c for c in all_cols if c == "Attachment" or re.match(r"Attachment\.\d+$", c)]

RCCA_STEPS = {
    "D2 – Problem Description":           "Custom field (D2 - Problem Description)",
    "D2 – Problem Categorization":         "Custom field (D2 - Problem Categorization)",
    "D3 – Containment Actions":            "Custom field (D3 - Initiate Interim Containment Actions)",
    "D3 – Implementation Date":            "Custom field (D3 - Implementation Date)",
    "D4 – Root Cause (Occurred)":          "Custom field (D4 - Define/Verify Root Cause for Problem to Occur)",
    "D4 – Root Cause (Failed to Detect)":  "Custom field (D4 - Define/Verify Root Cause for Failure to Detect the Problem)",
    "D5 – Temp Corrective Action":         "Custom field (D5 \u2013 Define Temporary Corrective Action)",
    "D5 – Acceptance Criteria":            "Custom field (D5 - Acceptance Criteria)",
    "D5 – Disposition":                    "Custom field (D5 - Disposition)",
    "D5 – Verification":                   "Custom field (D5 - Verification of Temporary Corrective Action)",
    "D5 – Verified By":                    "Custom field (D5 - Verified By)",
    "D6 – Permanent Corrective Action":    "Custom field (D6 - Define Permanent Corrective Action)",
    "D6 – ECN Number":                     "Custom field (D6 - ECN Number)",
    "D6 – Implementation Date":            "Custom field (D6 - Implementation Date)",
    "D6 – Verification":                   "Custom field (D6 - Verification of Permanent Corrective Action)",
    "D7 – Prevent Recurrence":             "Custom field (D7 - Actions to prevent Recurrence)",
    "D8 – Recognize Team":                 "Custom field (D8 - Recognize the Team)",
    "Root Cause":                          "Custom field (Root Cause)",
    "Corrective Action":                   "Custom field (Corrective Action)",
    "Containment Action":                  "Custom field (Containment Action)",
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
    view_mode = st.radio("Layout", ["Board","List","Analytics"], index=1)

# ── Filters ────────────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_projects: fdf = fdf[fdf["Project name"].isin(sel_projects)]
if sel_status:   fdf = fdf[fdf["Status"].isin(sel_status)]
if sel_priority: fdf = fdf[fdf["Priority"].isin(sel_priority)]
if sel_type:     fdf = fdf[fdf["Issue Type"].isin(sel_type)]
if sel_assignee: fdf = fdf[fdf["Assignee"].isin(sel_assignee)]
if date_from and date_to:
    fdf = fdf[(fdf["Created"].dt.date >= date_from) & (fdf["Created"].dt.date <= date_to)]

# ── Top bar ────────────────────────────────────────────────────────────────────
st.markdown('<div class="top-bar"><span style="font-size:24px">🦈</span><h1>SharkNinja · Jira Dashboard</h1></div>', unsafe_allow_html=True)

search = st.text_input("🔎  Search issues...", placeholder="e.g. HD430 or PCOPT-1821")
if search:
    fdf = fdf[fdf["Summary"].str.contains(search, case=False, na=False) | fdf["Issue key"].str.contains(search, case=False, na=False)]

# ── KPIs ───────────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📌 Summary</div>', unsafe_allow_html=True)
total      = len(fdf)
open_count = len(fdf[~fdf["Status"].isin(["Close","Done","Ready to Close"])])
closed     = len(fdf[fdf["Status"].isin(["Close","Done","Ready to Close"])])
bugs       = len(fdf[fdf["Issue Type"] == "Bug"])
high_pri   = len(fdf[fdf["Priority"].isin(["High","Highest","Critical"])])
c1,c2,c3,c4,c5 = st.columns(5)
c1.metric("Total Issues",  f"{total:,}")
c2.metric("Open",          f"{open_count:,}", delta=f"{open_count-closed:+,} vs closed", delta_color="inverse")
c3.metric("Closed / Done", f"{closed:,}")
c4.metric("Bugs",          f"{bugs:,}")
c5.metric("High Priority", f"{high_pri:,}")
st.markdown("")

# ══════════════════════════════════════════════════════════════════════════════
#  TICKET DETAIL PANEL
# ══════════════════════════════════════════════════════════════════════════════
def render_ticket_detail(row):
    comments    = parse_comments(row, comment_cols)
    attachments = parse_attachments(row, attach_cols)

    st.markdown(f"""
    <div class="card" style="border-left:4px solid #0052CC;">
      <div class="detail-header">{row['Summary']}</div>
      <div style="margin-bottom:6px;">{status_badge(row['Status'])} &nbsp; {type_icon(row['Issue Type'])} &nbsp; {priority_icon(row['Priority'])}</div>
      <div style="font-size:12px; color:#6B778C; font-family:monospace;">{row['Issue key']} &nbsp;·&nbsp; {row['Project name']}</div>
    </div>
    """, unsafe_allow_html=True)

    left, right = st.columns([3, 1])

    with right:
        st.markdown(f"""
        <div class="card">
          <div class="detail-section-title">Details</div>
          <table class="detail-meta-table">
            <tr><td class="detail-meta-label">Assignee</td><td><strong>{row['Assignee']}</strong></td></tr>
            <tr><td class="detail-meta-label">Reporter</td><td>{row['Reporter']}</td></tr>
            <tr><td class="detail-meta-label">Priority</td><td>{priority_icon(row['Priority'])}</td></tr>
            <tr><td class="detail-meta-label">Status</td><td>{status_badge(row['Status'])}</td></tr>
            <tr><td class="detail-meta-label">Resolution</td><td>{row.get('Resolution','') or '—'}</td></tr>
            <tr><td class="detail-meta-label">Created</td><td style="font-size:12px;">{fmt_date(row['Created'])}</td></tr>
            <tr><td class="detail-meta-label">Updated</td><td style="font-size:12px;">{fmt_date(row['Updated'])}</td></tr>
            <tr><td class="detail-meta-label">Due Date</td><td style="font-size:12px;">{fmt_date(row.get('Due date'))}</td></tr>
          </table>
        </div>
        """, unsafe_allow_html=True)

        if attachments:
            st.markdown('<div class="detail-section-title" style="margin-top:0; padding:0 0 4px 0;">📎 Attachments</div>', unsafe_allow_html=True)
            chips = "".join(
                f'<a href="{a["url"]}" target="_blank" class="attach-chip">{"🖼️" if a["is_image"] else "📄"} {a["filename"]}</a>'
                if a["url"] else
                f'<span class="attach-chip">{"🖼️" if a["is_image"] else "📄"} {a["filename"]}</span>'
                for a in attachments
            )
            st.markdown(f'<div style="display:flex; flex-wrap:wrap;">{chips}</div>', unsafe_allow_html=True)
            st.markdown(f'<div style="font-size:11px; color:#6B778C; margin-top:4px;">{len(attachments)} attachment{"s" if len(attachments)!=1 else ""} · Links require Jira login</div>', unsafe_allow_html=True)

    with left:
        tab1, tab2, tab3 = st.tabs(["📝 Description", "🔬 RCCA", f"💬 Comments ({len(comments)})"])

        with tab1:
            desc = str(row.get("Description","") or "").strip()
            if desc and desc != "nan":
                desc = re.sub(r'\[([^\|]+)\|[^\]]+\|smart-link\]', r'\1', desc)
                desc = re.sub(r'\[([^\|]+)\|[^\]]+\]', r'\1', desc)
                st.markdown(f'<div class="desc-box">{desc[:2000]}</div>', unsafe_allow_html=True)
            else:
                st.markdown('<div class="desc-box" style="color:#A5ADBA; font-style:italic;">No description provided.</div>', unsafe_allow_html=True)

            for label, field in [
                ("✅ Expected Behavior",   "Custom field (Expected Behavior)"),
                ("❌ Actual Behavior",     "Custom field (Actual Behavior)"),
                ("🔁 Trigger / Scenario",  "Custom field (Trigger / Scenario)"),
            ]:
                if field in all_cols:
                    val = str(row.get(field,"") or "").strip()
                    if val and val != "nan":
                        st.markdown(f"**{label}**")
                        st.markdown(f'<div class="desc-box">{val[:500]}</div>', unsafe_allow_html=True)

        with tab2:
            d_groups = {
                "🔴 D2 · Problem Definition": [k for k in RCCA_STEPS if k.startswith("D2")],
                "🟠 D3 · Containment":         [k for k in RCCA_STEPS if k.startswith("D3")],
                "🟡 D4 · Root Cause":          [k for k in RCCA_STEPS if k.startswith("D4")],
                "🔵 D5 · Temp Corrective":     [k for k in RCCA_STEPS if k.startswith("D5")],
                "🟢 D6 · Perm Corrective":     [k for k in RCCA_STEPS if k.startswith("D6")],
                "✅ D7–D8 · Close Out":        [k for k in RCCA_STEPS if k.startswith("D7") or k.startswith("D8")],
                "📋 General":                  [k for k in RCCA_STEPS if not any(k.startswith(x) for x in ["D2","D3","D4","D5","D6","D7","D8"])],
            }
            has_any = False
            for group_label, keys in d_groups.items():
                group_html = ""
                for key in keys:
                    val = str(row.get(RCCA_STEPS[key],"") or "").strip()
                    if val and val != "nan":
                        group_html += f'<div class="rcca-step"><div class="rcca-step-label">{key}</div><div class="rcca-step-value">{val[:600]}</div></div>'
                        has_any = True
                if group_html:
                    st.markdown(f"**{group_label}**")
                    st.markdown(group_html, unsafe_allow_html=True)
            if not has_any:
                st.markdown('<div style="text-align:center; padding:40px; color:#A5ADBA;"><div style="font-size:32px;">🔬</div><div style="margin-top:8px;">No RCCA data for this ticket.</div></div>', unsafe_allow_html=True)

        with tab3:
            if comments:
                for c in comments:
                    author = c["author_id"][:10] + "…" if len(c["author_id"]) > 12 else c["author_id"]
                    st.markdown(f"""
                    <div class="comment-bubble">
                      <span class="comment-author">👤 {author}</span>
                      <span class="comment-date">{c['date']}</span>
                      <div class="comment-body">{c['body'][:800]}</div>
                    </div>""", unsafe_allow_html=True)
            else:
                st.markdown('<div style="text-align:center; padding:40px; color:#A5ADBA;"><div style="font-size:32px;">💬</div><div style="margin-top:8px;">No comments on this ticket.</div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "Board":
    st.markdown('<div class="section-header">🗂️ Board View</div>', unsafe_allow_html=True)
    status_order = ["New","In Progress","RCCA","Verify","On Hold","Ready to Close","Done","Close"]
    present = [s for s in status_order if s in fdf["Status"].unique()]
    for s in fdf["Status"].unique():
        if s not in present: present.append(s)
    col_colors = {"New":"#DFE1E6","In Progress":"#DEEBFF","RCCA":"#FFF0B3","Verify":"#EAE6FF","On Hold":"#FFEBE6","Done":"#E3FCEF","Close":"#E3FCEF","Ready to Close":"#E3FCEF"}
    for col, status in zip(st.columns(min(len(present), 6)), present[:6]):
        grp = fdf[fdf["Status"] == status].head(20)
        with col:
            st.markdown(f'<div style="background:{col_colors.get(status,"#F4F5F7")}; border-radius:4px; padding:8px 12px; margin-bottom:8px;"><strong style="color:#172B4D; font-size:12px; text-transform:uppercase;">{status}</strong><span style="background:rgba(0,0,0,0.1); border-radius:10px; padding:1px 7px; font-size:11px; margin-left:6px;">{len(grp)}</span></div>', unsafe_allow_html=True)
            for _, row in grp.iterrows():
                pc = {"Critical":"#BF2600","Highest":"#BF2600","High":"#FF5630","Medium":"#FF991F","Low":"#36B37E"}.get(row["Priority"],"#6B778C")
                st.markdown(f'<div style="background:white; border:1px solid #DFE1E6; border-left:3px solid {pc}; border-radius:3px; padding:10px; margin-bottom:6px; font-size:12px;"><div style="color:#0052CC; font-weight:600; font-family:monospace; margin-bottom:4px;">{row["Issue key"]}</div><div style="color:#172B4D; margin-bottom:6px; line-height:1.3;">{str(row["Summary"])[:80]}{"..." if len(str(row["Summary"]))>80 else ""}</div><div style="display:flex; justify-content:space-between;"><span style="font-size:10px; color:#6B778C;">{type_icon(row["Issue Type"])}</span><span style="font-size:10px; background:#DFE1E6; border-radius:50%; width:22px; height:22px; display:inline-flex; align-items:center; justify-content:center;" title="{row["Assignee"]}">{str(row["Assignee"])[:1].upper()}</span></div></div>', unsafe_allow_html=True)
    st.markdown("---")
    st.markdown('<div class="section-header">🔍 Ticket Detail</div>', unsafe_allow_html=True)
    sel_key = st.selectbox("Select ticket", [""] + sorted(fdf["Issue key"].dropna().unique().tolist()), key="board_sel")
    if sel_key:
        render_ticket_detail(fdf[fdf["Issue key"] == sel_key].iloc[0])

# ══════════════════════════════════════════════════════════════════════════════
#  LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "List":
    st.markdown('<div class="section-header">📋 Issue List</div>', unsafe_allow_html=True)
    sc1, sc2 = st.columns([2,2])
    with sc1: sort_col = st.selectbox("Sort by", ["Created","Updated","Priority","Status","Issue key"])
    with sc2: sort_dir = st.selectbox("Order",   ["Descending","Ascending"])
    ascending = sort_dir == "Ascending"
    if sort_col == "Priority":
        fdf = fdf.copy()
        fdf["_ps"] = fdf["Priority"].map({"Critical":0,"Highest":1,"High":2,"Medium":3,"Low":4}).fillna(5)
        fdf = fdf.sort_values("_ps", ascending=ascending)
    else:
        fdf = fdf.sort_values(sort_col, ascending=ascending, na_position="last")

    rows_html = ""
    for _, row in fdf.head(200).iterrows():
        cd = row["Created"].strftime("%b %d, %Y") if pd.notna(row["Created"]) else ""
        ud = row["Updated"].strftime("%b %d, %Y") if pd.notna(row["Updated"]) else ""
        rows_html += f'<tr><td><span class="issue-key">{row["Issue key"]}</span></td><td><span class="issue-summary" title="{str(row["Summary"])}">{str(row["Summary"])[:70]}{"..." if len(str(row["Summary"]))>70 else ""}</span></td><td>{type_icon(row["Issue Type"])}</td><td>{status_badge(row["Status"])}</td><td>{priority_icon(row["Priority"])}</td><td style="color:#6B778C; font-size:12px;">{row["Assignee"]}</td><td style="color:#6B778C; font-size:12px; white-space:nowrap;">{cd}</td><td style="color:#6B778C; font-size:12px; white-space:nowrap;">{ud}</td></tr>'

    st.markdown(f'<div class="card" style="overflow-x:auto; padding:0;"><table class="issue-table"><thead><tr><th>Key</th><th>Summary</th><th>Type</th><th>Status</th><th>Priority</th><th>Assignee</th><th>Created</th><th>Updated</th></tr></thead><tbody>{rows_html}</tbody></table><div style="padding:10px 12px; color:#6B778C; font-size:12px; border-top:1px solid #DFE1E6;">Showing {min(200,len(fdf))} of {len(fdf)} issues</div></div>', unsafe_allow_html=True)

    st.markdown('<div class="section-header">🔍 Ticket Detail</div>', unsafe_allow_html=True)
    sel_key = st.selectbox("Select ticket", [""] + sorted(fdf["Issue key"].dropna().unique().tolist()), key="list_sel",
                           help="Choose a ticket to see Description, RCCA D-steps, Comments, and Attachments")
    if sel_key:
        render_ticket_detail(fdf[fdf["Issue key"] == sel_key].iloc[0])

# ══════════════════════════════════════════════════════════════════════════════
#  ANALYTICS VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "Analytics":
    st.markdown('<div class="section-header">📊 Analytics</div>', unsafe_allow_html=True)
    JB = "#0052CC"
    JC = ["#0052CC","#0065FF","#4C9AFF","#B3D4FF","#172B4D","#36B37E","#FF5630","#FF991F","#6554C0","#00B8D9"]
    BASE = dict(paper_bgcolor="white", plot_bgcolor="white", font=dict(family="Arial",size=12,color="#172B4D"))

    r1l,r1r = st.columns(2)
    with r1l:
        st.markdown('<div class="section-header">Issues by Status</div>', unsafe_allow_html=True)
        sc = fdf["Status"].value_counts().reset_index(); sc.columns=["Status","Count"]
        fig = px.bar(sc, x="Status", y="Count", color="Status", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(**BASE, showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=300, xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"))
        st.plotly_chart(fig, use_container_width=True)
    with r1r:
        st.markdown('<div class="section-header">Issues by Priority</div>', unsafe_allow_html=True)
        pc = fdf["Priority"].value_counts().reset_index(); pc.columns=["Priority","Count"]
        fig = px.pie(pc, names="Priority", values="Count", hole=0.45, color="Priority",
                     color_discrete_map={"Critical":"#BF2600","Highest":"#FF5630","High":"#FF7452","Medium":"#FF991F","Low":"#36B37E"})
        fig.update_traces(textposition="inside", textinfo="percent+label")
        fig.update_layout(**BASE, margin=dict(t=10,b=10,l=10,r=10), height=300)
        st.plotly_chart(fig, use_container_width=True)

    r2l,r2r = st.columns(2)
    with r2l:
        st.markdown('<div class="section-header">Issues Created Over Time</div>', unsafe_allow_html=True)
        ts = fdf.dropna(subset=["Created"]).copy()
        ts["Week"] = ts["Created"].dt.to_period("W").dt.start_time
        tsg = ts.groupby("Week").size().reset_index(name="Count")
        fig = px.area(tsg, x="Week", y="Count", color_discrete_sequence=[JB])
        fig.update_traces(fill="tozeroy", line_color=JB, fillcolor="rgba(0,82,204,0.15)")
        fig.update_layout(**BASE, margin=dict(t=10,b=10,l=10,r=10), height=300, xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"))
        st.plotly_chart(fig, use_container_width=True)
    with r2r:
        st.markdown('<div class="section-header">Top Assignees</div>', unsafe_allow_html=True)
        ac = fdf[fdf["Assignee"] != "Unassigned"]["Assignee"].value_counts().head(15).reset_index(); ac.columns=["Assignee","Count"]
        fig = px.bar(ac, x="Count", y="Assignee", orientation="h", color="Count", color_continuous_scale=["#B3D4FF",JB], text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(**BASE, coloraxis_showscale=False, margin=dict(t=10,b=10,l=10,r=10), height=350, xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7", categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    r3l,r3r = st.columns(2)
    with r3l:
        st.markdown('<div class="section-header">Issue Type Breakdown</div>', unsafe_allow_html=True)
        tc = fdf["Issue Type"].value_counts().reset_index(); tc.columns=["Type","Count"]
        fig = px.bar(tc, x="Type", y="Count", color="Type", color_discrete_sequence=JC, text="Count")
        fig.update_traces(textposition="outside", marker_line_width=0)
        fig.update_layout(**BASE, showlegend=False, margin=dict(t=10,b=10,l=10,r=10), height=280, xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"))
        st.plotly_chart(fig, use_container_width=True)
    with r3r:
        st.markdown('<div class="section-header">Resolution Status</div>', unsafe_allow_html=True)
        rc = fdf["Resolution"].replace("","Unresolved").value_counts().head(8).reset_index(); rc.columns=["Resolution","Count"]
        fig = px.bar(rc, x="Count", y="Resolution", orientation="h", color="Count", color_continuous_scale=["#B3D4FF",JB], text="Count")
        fig.update_traces(textposition="outside")
        fig.update_layout(**BASE, coloraxis_showscale=False, margin=dict(t=10,b=10,l=10,r=10), height=280, xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7", categoryorder="total ascending"))
        st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="section-header">Status × Priority Heatmap</div>', unsafe_allow_html=True)
    heat  = fdf.groupby(["Status","Priority"]).size().reset_index(name="Count")
    pivot = heat.pivot(index="Status", columns="Priority", values="Count").fillna(0)
    fig = go.Figure(go.Heatmap(z=pivot.values, x=pivot.columns.tolist(), y=pivot.index.tolist(),
                               colorscale=[[0,"#DEEBFF"],[0.5,"#4C9AFF"],[1,JB]],
                               text=pivot.values.astype(int), texttemplate="%{text}", showscale=True))
    fig.update_layout(**BASE, margin=dict(t=10,b=10,l=10,r=10), height=300)
    st.plotly_chart(fig, use_container_width=True)

st.markdown('<div style="text-align:center; color:#6B778C; font-size:11px; margin-top:24px; padding-top:16px; border-top:1px solid #DFE1E6;">SharkNinja Jira Dashboard · Powered by Streamlit</div>', unsafe_allow_html=True)
