import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="SharkNinja Jira Dashboard",
    page_icon="🦈",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS (Jira-like styling) ─────────────────────────────────────────────
st.markdown("""
<style>
  /* Global */
  [data-testid="stAppViewContainer"] { background: #F4F5F7; }
  [data-testid="stSidebar"] { background: #0052CC; }
  [data-testid="stSidebar"] * { color: white !important; }
  [data-testid="stSidebar"] .stSelectbox label,
  [data-testid="stSidebar"] .stMultiSelect label,
  [data-testid="stSidebar"] .stTextInput label { color: #B3D4FF !important; font-size: 12px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; }
  [data-testid="stSidebar"] h1, [data-testid="stSidebar"] h2, [data-testid="stSidebar"] h3 { color: white !important; }

  /* Metric cards */
  [data-testid="metric-container"] {
    background: white;
    border-radius: 4px;
    padding: 16px;
    border: 1px solid #DFE1E6;
    box-shadow: 0 1px 2px rgba(0,0,0,0.05);
  }
  [data-testid="stMetricValue"] { color: #172B4D; font-size: 28px; font-weight: 700; }
  [data-testid="stMetricLabel"] { color: #6B778C; font-size: 12px; font-weight: 600; text-transform: uppercase; }

  /* Section headers */
  .section-header {
    font-size: 16px;
    font-weight: 600;
    color: #172B4D;
    margin: 16px 0 8px 0;
    padding-bottom: 8px;
    border-bottom: 2px solid #0052CC;
  }

  /* Status badges */
  .badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 3px;
    font-size: 11px;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
  .badge-new        { background:#DFE1E6; color:#42526E; }
  .badge-progress   { background:#DEEBFF; color:#0052CC; }
  .badge-verify     { background:#EAE6FF; color:#403294; }
  .badge-rcca       { background:#FFF0B3; color:#974F0C; }
  .badge-hold       { background:#FFEBE6; color:#BF2600; }
  .badge-done       { background:#E3FCEF; color:#006644; }
  .badge-close      { background:#E3FCEF; color:#006644; }
  .badge-rtc        { background:#E3FCEF; color:#006644; }

  /* Priority icons text */
  .pri-critical  { color:#BF2600; font-weight:700; }
  .pri-highest   { color:#BF2600; font-weight:700; }
  .pri-high      { color:#FF5630; font-weight:600; }
  .pri-medium    { color:#FF991F; font-weight:600; }
  .pri-low       { color:#36B37E; font-weight:600; }

  /* Table-like issue rows */
  .issue-table { width:100%; border-collapse:collapse; }
  .issue-table th {
    background:#F4F5F7;
    color:#5E6C84;
    font-size:11px;
    font-weight:700;
    text-transform:uppercase;
    padding:8px 12px;
    border-bottom:2px solid #DFE1E6;
    text-align:left;
  }
  .issue-table td {
    padding:10px 12px;
    border-bottom:1px solid #F4F5F7;
    font-size:13px;
    color:#172B4D;
    vertical-align:middle;
  }
  .issue-table tr:hover td { background:#FAFBFC; }
  .issue-key { color:#0052CC; font-weight:600; font-family:monospace; }
  .issue-summary { max-width:400px; overflow:hidden; text-overflow:ellipsis; white-space:nowrap; }

  /* Top nav bar */
  .top-bar {
    background: #0052CC;
    padding: 10px 20px;
    border-radius: 4px;
    margin-bottom: 20px;
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .top-bar h1 { color: white; margin: 0; font-size: 20px; }

  /* Card container */
  .card {
    background: white;
    border-radius: 4px;
    border: 1px solid #DFE1E6;
    padding: 16px;
    margin-bottom: 16px;
  }

  /* Search box */
  [data-testid="stTextInput"] input {
    border: 2px solid #DFE1E6;
    border-radius: 4px;
    background: white;
  }
  [data-testid="stTextInput"] input:focus { border-color: #0052CC; }

  /* Hide streamlit branding */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  header { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# ── Load Data ──────────────────────────────────────────────────────────────────
@st.cache_data
def load_data(path: str) -> pd.DataFrame:
    df = pd.read_csv(path, low_memory=False)
    # Parse dates
    for col in ["Created", "Updated", "Due date", "Resolved"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    # Clean up text fields
    for col in ["Summary", "Assignee", "Reporter", "Status", "Priority", "Issue Type", "Project name", "Resolution"]:
        if col in df.columns:
            df[col] = df[col].fillna("Unassigned" if col == "Assignee" else "").astype(str).str.strip()
    return df

# Allow user to upload CSV or use default
with st.sidebar:
    st.markdown("## 🦈 SharkNinja")
    st.markdown("### Jira Dashboard")
    st.markdown("---")
    uploaded = st.file_uploader("📂 Upload Jira CSV", type="csv")

if uploaded:
    df_raw = pd.read_csv(uploaded, low_memory=False)
    for col in ["Created", "Updated", "Due date", "Resolved"]:
        if col in df_raw.columns:
            df_raw[col] = pd.to_datetime(df_raw[col], errors="coerce")
    for col in ["Summary", "Assignee", "Reporter", "Status", "Priority", "Issue Type", "Project name", "Resolution"]:
        if col in df_raw.columns:
            df_raw[col] = df_raw[col].fillna("Unassigned" if col == "Assignee" else "").astype(str).str.strip()
    df = df_raw
else:
    try:
        df = load_data("Jira_-_SharkNinja__22_.csv")
    except:
        st.error("Please upload a Jira CSV export to get started.")
        st.stop()

# ── Sidebar Filters ────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🔍 Filters")

    # Project
    projects = sorted(df["Project name"].dropna().unique().tolist())
    sel_projects = st.multiselect("Project", options=projects, default=[])

    # Status
    statuses = sorted(df["Status"].dropna().unique().tolist())
    sel_status = st.multiselect("Status", options=statuses, default=[])

    # Priority
    priorities = sorted(df["Priority"].dropna().unique().tolist())
    sel_priority = st.multiselect("Priority", options=priorities, default=[])

    # Issue Type
    types = sorted(df["Issue Type"].dropna().unique().tolist())
    sel_type = st.multiselect("Issue Type", options=types, default=[])

    # Assignee
    assignees = sorted(df["Assignee"].dropna().unique().tolist())
    sel_assignee = st.multiselect("Assignee", options=assignees, default=[])

    # Date range
    st.markdown("### 📅 Date Range")
    min_date = df["Created"].min()
    max_date = df["Created"].max()
    if pd.notna(min_date) and pd.notna(max_date):
        date_from = st.date_input("From", value=min_date.date(), min_value=min_date.date(), max_value=max_date.date())
        date_to   = st.date_input("To",   value=max_date.date(), min_value=min_date.date(), max_value=max_date.date())
    else:
        date_from, date_to = None, None

    st.markdown("---")
    st.markdown("### 📊 View")
    view_mode = st.radio("Layout", ["Board", "List", "Analytics"], index=1)

# ── Apply Filters ──────────────────────────────────────────────────────────────
fdf = df.copy()
if sel_projects:  fdf = fdf[fdf["Project name"].isin(sel_projects)]
if sel_status:    fdf = fdf[fdf["Status"].isin(sel_status)]
if sel_priority:  fdf = fdf[fdf["Priority"].isin(sel_priority)]
if sel_type:      fdf = fdf[fdf["Issue Type"].isin(sel_type)]
if sel_assignee:  fdf = fdf[fdf["Assignee"].isin(sel_assignee)]
if date_from and date_to and "Created" in fdf.columns:
    fdf = fdf[(fdf["Created"].dt.date >= date_from) & (fdf["Created"].dt.date <= date_to)]

# ── Top bar ────────────────────────────────────────────────────────────────────
st.markdown("""
<div class="top-bar">
  <span style="font-size:24px">🦈</span>
  <h1>SharkNinja · Jira Dashboard</h1>
</div>
""", unsafe_allow_html=True)

# ── Search bar ─────────────────────────────────────────────────────────────────
search = st.text_input("🔎  Search issues by summary or key...", placeholder="e.g. HD430 or PCOPT-1821")
if search:
    mask = (
        fdf["Summary"].str.contains(search, case=False, na=False) |
        fdf["Issue key"].str.contains(search, case=False, na=False)
    )
    fdf = fdf[mask]

# ── KPI Metrics ────────────────────────────────────────────────────────────────
st.markdown('<div class="section-header">📌 Summary</div>', unsafe_allow_html=True)

total      = len(fdf)
open_count = len(fdf[~fdf["Status"].isin(["Close", "Done", "Ready to Close"])])
closed     = len(fdf[fdf["Status"].isin(["Close", "Done", "Ready to Close"])])
bugs       = len(fdf[fdf["Issue Type"] == "Bug"])
high_pri   = len(fdf[fdf["Priority"].isin(["High", "Highest", "Critical"])])

c1, c2, c3, c4, c5 = st.columns(5)
c1.metric("Total Issues",   f"{total:,}")
c2.metric("Open",           f"{open_count:,}",  delta=f"{open_count - closed:+,} vs closed", delta_color="inverse")
c3.metric("Closed / Done",  f"{closed:,}")
c4.metric("Bugs",           f"{bugs:,}")
c5.metric("High Priority",  f"{high_pri:,}")

st.markdown("")

# ── Helper: status badge HTML ──────────────────────────────────────────────────
def status_badge(s: str) -> str:
    s = str(s)
    cls_map = {
        "New": "badge-new",
        "In Progress": "badge-progress",
        "Verify": "badge-verify",
        "RCCA": "badge-rcca",
        "On Hold": "badge-hold",
        "Done": "badge-done",
        "Close": "badge-close",
        "Ready to Close": "badge-rtc",
    }
    cls = cls_map.get(s, "badge-new")
    return f'<span class="badge {cls}">{s}</span>'

def priority_icon(p: str) -> str:
    icons = {"Critical": "🔴", "Highest": "🔴", "High": "🟠", "Medium": "🟡", "Low": "🟢"}
    return icons.get(str(p), "⚪") + f" {p}"

def type_icon(t: str) -> str:
    icons = {"Bug": "🐛", "Task": "✅", "Epic": "⚡", "Sub-task": "↳", "VA/VE": "🔧"}
    return icons.get(str(t), "📋") + f" {t}"

# ══════════════════════════════════════════════════════════════════════════════
# BOARD VIEW
# ══════════════════════════════════════════════════════════════════════════════
if view_mode == "Board":
    st.markdown('<div class="section-header">🗂️ Board View</div>', unsafe_allow_html=True)

    status_order = ["New", "In Progress", "RCCA", "Verify", "On Hold", "Ready to Close", "Done", "Close"]
    present_statuses = [s for s in status_order if s in fdf["Status"].unique()]
    # Add any not in our order list
    for s in fdf["Status"].unique():
        if s not in present_statuses:
            present_statuses.append(s)

    # Show up to 5 columns at a time for readability
    display_statuses = present_statuses[:6]
    cols = st.columns(len(display_statuses))

    col_colors = {
        "New": "#DFE1E6", "In Progress": "#DEEBFF", "RCCA": "#FFF0B3",
        "Verify": "#EAE6FF", "On Hold": "#FFEBE6", "Done": "#E3FCEF",
        "Close": "#E3FCEF", "Ready to Close": "#E3FCEF",
    }

    for col, status in zip(cols, display_statuses):
        grp = fdf[fdf["Status"] == status].head(20)
        color = col_colors.get(status, "#F4F5F7")
        with col:
            st.markdown(f"""
            <div style="background:{color}; border-radius:4px; padding:8px 12px; margin-bottom:8px;">
              <strong style="color:#172B4D; font-size:12px; text-transform:uppercase;">{status}</strong>
              <span style="background:rgba(0,0,0,0.1); border-radius:10px; padding:1px 7px; font-size:11px; margin-left:6px;">{len(grp)}</span>
            </div>
            """, unsafe_allow_html=True)
            for _, row in grp.iterrows():
                pri_color = {"Critical":"#BF2600","Highest":"#BF2600","High":"#FF5630","Medium":"#FF991F","Low":"#36B37E"}.get(row["Priority"], "#6B778C")
                st.markdown(f"""
                <div style="background:white; border:1px solid #DFE1E6; border-left:3px solid {pri_color};
                     border-radius:3px; padding:10px; margin-bottom:6px; font-size:12px;">
                  <div style="color:#0052CC; font-weight:600; font-family:monospace; margin-bottom:4px;">{row['Issue key']}</div>
                  <div style="color:#172B4D; margin-bottom:6px; line-height:1.3;">{str(row['Summary'])[:80]}{'...' if len(str(row['Summary'])) > 80 else ''}</div>
                  <div style="display:flex; justify-content:space-between; align-items:center;">
                    <span style="font-size:10px; color:#6B778C;">{type_icon(row['Issue Type'])}</span>
                    <span style="font-size:10px; background:#DFE1E6; border-radius:50%; width:22px; height:22px;
                         display:inline-flex; align-items:center; justify-content:center;"
                         title="{row['Assignee']}">{str(row['Assignee'])[:1].upper()}</span>
                  </div>
                </div>
                """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# LIST VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "List":
    st.markdown('<div class="section-header">📋 Issue List</div>', unsafe_allow_html=True)

    # Sort controls
    sc1, sc2, sc3 = st.columns([2, 2, 4])
    with sc1:
        sort_col = st.selectbox("Sort by", ["Created", "Updated", "Priority", "Status", "Issue key"], index=0)
    with sc2:
        sort_dir = st.selectbox("Order", ["Descending", "Ascending"])

    ascending = sort_dir == "Ascending"
    if sort_col == "Priority":
        pri_order = {"Critical": 0, "Highest": 1, "High": 2, "Medium": 3, "Low": 4}
        fdf = fdf.copy()
        fdf["_pri_sort"] = fdf["Priority"].map(pri_order).fillna(5)
        fdf = fdf.sort_values("_pri_sort", ascending=ascending)
    else:
        fdf = fdf.sort_values(sort_col, ascending=ascending, na_position="last")

    display_cols = ["Issue key", "Summary", "Issue Type", "Status", "Priority", "Assignee", "Reporter", "Created", "Updated"]
    display_df = fdf[display_cols].copy()

    # Build HTML table
    rows_html = ""
    for _, row in display_df.head(200).iterrows():
        created_str = row["Created"].strftime("%b %d, %Y") if pd.notna(row["Created"]) else ""
        updated_str = row["Updated"].strftime("%b %d, %Y") if pd.notna(row["Updated"]) else ""
        rows_html += f"""
        <tr>
          <td><span class="issue-key">{row['Issue key']}</span></td>
          <td><span class="issue-summary" title="{str(row['Summary'])}">{str(row['Summary'])[:70]}{'...' if len(str(row['Summary'])) > 70 else ''}</span></td>
          <td>{type_icon(row['Issue Type'])}</td>
          <td>{status_badge(row['Status'])}</td>
          <td>{priority_icon(row['Priority'])}</td>
          <td style="color:#6B778C; font-size:12px;">{row['Assignee']}</td>
          <td style="color:#6B778C; font-size:12px;">{row['Reporter']}</td>
          <td style="color:#6B778C; font-size:12px; white-space:nowrap;">{created_str}</td>
          <td style="color:#6B778C; font-size:12px; white-space:nowrap;">{updated_str}</td>
        </tr>"""

    table_html = f"""
    <div class="card" style="overflow-x:auto; padding:0;">
      <table class="issue-table">
        <thead>
          <tr>
            <th>Key</th><th>Summary</th><th>Type</th><th>Status</th>
            <th>Priority</th><th>Assignee</th><th>Reporter</th><th>Created</th><th>Updated</th>
          </tr>
        </thead>
        <tbody>{rows_html}</tbody>
      </table>
      <div style="padding:10px 12px; color:#6B778C; font-size:12px; border-top:1px solid #DFE1E6;">
        Showing {min(200, len(fdf))} of {len(fdf)} issues
      </div>
    </div>
    """
    st.markdown(table_html, unsafe_allow_html=True)

    # Detail panel for selected ticket
    st.markdown('<div class="section-header">🔍 Issue Detail</div>', unsafe_allow_html=True)
    keys = fdf["Issue key"].dropna().unique().tolist()
    sel_key = st.selectbox("Select issue to view details", options=[""] + sorted(keys))
    if sel_key:
        row = fdf[fdf["Issue key"] == sel_key].iloc[0]
        d1, d2 = st.columns([2, 1])
        with d1:
            st.markdown(f"""
            <div class="card">
              <div style="font-size:20px; font-weight:700; color:#172B4D; margin-bottom:8px;">{str(row['Summary'])}</div>
              <div style="margin-bottom:16px;">{status_badge(row['Status'])} &nbsp; {type_icon(row['Issue Type'])}</div>
              <div style="color:#172B4D; font-size:13px; line-height:1.6; background:#F4F5F7; padding:12px; border-radius:4px;">
                {str(row.get('Description','No description available.'))[:800]}
              </div>
            </div>
            """, unsafe_allow_html=True)
        with d2:
            created_str = row["Created"].strftime("%b %d, %Y %H:%M") if pd.notna(row["Created"]) else "—"
            updated_str = row["Updated"].strftime("%b %d, %Y %H:%M") if pd.notna(row["Updated"]) else "—"
            due_str     = row["Due date"].strftime("%b %d, %Y") if pd.notna(row.get("Due date")) else "None"
            st.markdown(f"""
            <div class="card">
              <table style="width:100%; font-size:13px;">
                <tr><td style="color:#6B778C; padding:4px 0; width:45%;">Priority</td><td>{priority_icon(row['Priority'])}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Assignee</td><td><strong>{row['Assignee']}</strong></td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Reporter</td><td>{row['Reporter']}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Project</td><td>{row['Project name']}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Created</td><td>{created_str}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Updated</td><td>{updated_str}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Due Date</td><td>{due_str}</td></tr>
                <tr><td style="color:#6B778C; padding:4px 0;">Resolution</td><td>{row.get('Resolution','Unresolved')}</td></tr>
              </table>
            </div>
            """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# ANALYTICS VIEW
# ══════════════════════════════════════════════════════════════════════════════
elif view_mode == "Analytics":
    st.markdown('<div class="section-header">📊 Analytics</div>', unsafe_allow_html=True)

    JIRA_BLUE   = "#0052CC"
    JIRA_COLORS = ["#0052CC","#0065FF","#4C9AFF","#B3D4FF","#172B4D","#36B37E","#FF5630","#FF991F","#6554C0","#00B8D9"]

    row1_l, row1_r = st.columns(2)

    # ── Status distribution ──
    with row1_l:
        st.markdown('<div class="section-header">Issues by Status</div>', unsafe_allow_html=True)
        status_counts = fdf["Status"].value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]
        fig_status = px.bar(
            status_counts, x="Status", y="Count", color="Status",
            color_discrete_sequence=JIRA_COLORS,
            text="Count"
        )
        fig_status.update_traces(textposition="outside", marker_line_width=0)
        fig_status.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Arial", size=12, color="#172B4D"),
            xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"),
            height=300
        )
        st.plotly_chart(fig_status, use_container_width=True)

    # ── Priority distribution ──
    with row1_r:
        st.markdown('<div class="section-header">Issues by Priority</div>', unsafe_allow_html=True)
        pri_counts = fdf["Priority"].value_counts().reset_index()
        pri_counts.columns = ["Priority", "Count"]
        pri_color_map = {"Critical":"#BF2600","Highest":"#FF5630","High":"#FF7452","Medium":"#FF991F","Low":"#36B37E","":"#DFE1E6"}
        fig_pri = px.pie(
            pri_counts, names="Priority", values="Count",
            color="Priority",
            color_discrete_map=pri_color_map,
            hole=0.45
        )
        fig_pri.update_traces(textposition="inside", textinfo="percent+label")
        fig_pri.update_layout(
            paper_bgcolor="white", margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Arial", size=12, color="#172B4D"),
            showlegend=True, height=300
        )
        st.plotly_chart(fig_pri, use_container_width=True)

    row2_l, row2_r = st.columns(2)

    # ── Issues over time ──
    with row2_l:
        st.markdown('<div class="section-header">Issues Created Over Time</div>', unsafe_allow_html=True)
        ts = fdf.dropna(subset=["Created"]).copy()
        ts["Week"] = ts["Created"].dt.to_period("W").dt.start_time
        ts_grp = ts.groupby("Week").size().reset_index(name="Count")
        fig_ts = px.area(
            ts_grp, x="Week", y="Count",
            color_discrete_sequence=[JIRA_BLUE]
        )
        fig_ts.update_traces(fill="tozeroy", line_color=JIRA_BLUE, fillcolor="rgba(0,82,204,0.15)")
        fig_ts.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Arial", size=12, color="#172B4D"),
            xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"),
            height=300
        )
        st.plotly_chart(fig_ts, use_container_width=True)

    # ── Top assignees ──
    with row2_r:
        st.markdown('<div class="section-header">Top Assignees by Issue Count</div>', unsafe_allow_html=True)
        asgn = fdf[fdf["Assignee"] != "Unassigned"]["Assignee"].value_counts().head(15).reset_index()
        asgn.columns = ["Assignee", "Count"]
        fig_asgn = px.bar(
            asgn, x="Count", y="Assignee", orientation="h",
            color="Count", color_continuous_scale=["#B3D4FF", "#0052CC"],
            text="Count"
        )
        fig_asgn.update_traces(textposition="outside")
        fig_asgn.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            margin=dict(t=10, b=10, l=10, r=10),
            coloraxis_showscale=False,
            font=dict(family="Arial", size=12, color="#172B4D"),
            xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7", categoryorder="total ascending"),
            height=350
        )
        st.plotly_chart(fig_asgn, use_container_width=True)

    # ── Issue type breakdown ──
    row3_l, row3_r = st.columns(2)
    with row3_l:
        st.markdown('<div class="section-header">Issue Type Breakdown</div>', unsafe_allow_html=True)
        type_counts = fdf["Issue Type"].value_counts().reset_index()
        type_counts.columns = ["Type", "Count"]
        fig_type = px.bar(
            type_counts, x="Type", y="Count",
            color="Type", color_discrete_sequence=JIRA_COLORS,
            text="Count"
        )
        fig_type.update_traces(textposition="outside", marker_line_width=0)
        fig_type.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            showlegend=False, margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Arial", size=12, color="#172B4D"),
            xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7"),
            height=280
        )
        st.plotly_chart(fig_type, use_container_width=True)

    # ── Resolution rate ──
    with row3_r:
        st.markdown('<div class="section-header">Resolution Status</div>', unsafe_allow_html=True)
        res = fdf["Resolution"].replace("", "Unresolved")
        res_counts = res.value_counts().head(8).reset_index()
        res_counts.columns = ["Resolution", "Count"]
        fig_res = px.bar(
            res_counts, x="Count", y="Resolution", orientation="h",
            color="Count", color_continuous_scale=["#B3D4FF", "#0052CC"],
            text="Count"
        )
        fig_res.update_traces(textposition="outside")
        fig_res.update_layout(
            paper_bgcolor="white", plot_bgcolor="white",
            coloraxis_showscale=False,
            margin=dict(t=10, b=10, l=10, r=10),
            font=dict(family="Arial", size=12, color="#172B4D"),
            xaxis=dict(gridcolor="#F4F5F7"), yaxis=dict(gridcolor="#F4F5F7", categoryorder="total ascending"),
            height=280
        )
        st.plotly_chart(fig_res, use_container_width=True)

    # ── Status × Priority heatmap ──
    st.markdown('<div class="section-header">Status × Priority Heatmap</div>', unsafe_allow_html=True)
    heat_data = fdf.groupby(["Status", "Priority"]).size().reset_index(name="Count")
    heat_pivot = heat_data.pivot(index="Status", columns="Priority", values="Count").fillna(0)
    fig_heat = go.Figure(data=go.Heatmap(
        z=heat_pivot.values,
        x=heat_pivot.columns.tolist(),
        y=heat_pivot.index.tolist(),
        colorscale=[[0, "#DEEBFF"], [0.5, "#4C9AFF"], [1, "#0052CC"]],
        text=heat_pivot.values.astype(int),
        texttemplate="%{text}",
        showscale=True
    ))
    fig_heat.update_layout(
        paper_bgcolor="white", plot_bgcolor="white",
        margin=dict(t=10, b=10, l=10, r=10),
        font=dict(family="Arial", size=12, color="#172B4D"),
        height=300
    )
    st.plotly_chart(fig_heat, use_container_width=True)

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; color:#6B778C; font-size:11px; margin-top:24px; padding-top:16px; border-top:1px solid #DFE1E6;">
  SharkNinja Jira Dashboard · Powered by Streamlit
</div>
""", unsafe_allow_html=True)
