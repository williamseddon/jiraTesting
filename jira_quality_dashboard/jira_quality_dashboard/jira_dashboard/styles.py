from __future__ import annotations

from datetime import datetime
from html import escape


def app_css() -> str:
    return """
    <style>
        .stApp {
            background: linear-gradient(180deg, #f6f8fb 0%, #fbfcfe 100%);
        }
        .block-container {
            padding-top: 1.8rem;
            padding-bottom: 2.2rem;
        }
        .hero-card {
            background: linear-gradient(135deg, #12223a 0%, #1b3c66 100%);
            color: #f7fbff;
            padding: 1.4rem 1.5rem;
            border-radius: 18px;
            box-shadow: 0 14px 36px rgba(18, 34, 58, 0.16);
            margin-bottom: 1rem;
        }
        .hero-card h1 {
            font-size: 1.8rem;
            line-height: 1.2;
            margin: 0 0 0.35rem 0;
            color: #ffffff;
        }
        .hero-card p {
            margin: 0;
            color: rgba(247, 251, 255, 0.9);
            font-size: 0.98rem;
        }
        .section-caption {
            color: #61758a;
            font-size: 0.92rem;
            margin-bottom: 0.55rem;
        }
        .soft-card {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(20, 38, 62, 0.07);
            border-radius: 16px;
            padding: 1rem 1rem 0.8rem 1rem;
            box-shadow: 0 8px 24px rgba(18, 34, 58, 0.06);
        }
        .soft-note {
            background: #ffffff;
            border-left: 4px solid #2d6cdf;
            border-radius: 12px;
            padding: 0.8rem 0.95rem;
            color: #314458;
            margin-bottom: 1rem;
            box-shadow: 0 6px 16px rgba(18, 34, 58, 0.05);
        }
        .tag-row {
            display: flex;
            flex-wrap: wrap;
            gap: 0.45rem;
            margin: 0.3rem 0 0.8rem 0;
        }
        .tag-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.35rem 0.65rem;
            border-radius: 999px;
            background: #edf3ff;
            color: #184f9c;
            font-size: 0.84rem;
            font-weight: 600;
            border: 1px solid rgba(24, 79, 156, 0.1);
        }
        .tag-pill.secondary {
            background: #eef7f3;
            color: #236a4a;
            border-color: rgba(35, 106, 74, 0.12);
        }
        .tag-pill.warning {
            background: #fff5e8;
            color: #9b5a00;
            border-color: rgba(155, 90, 0, 0.12);
        }
        .issue-shell {
            background: #ffffff;
            border: 1px solid rgba(20, 38, 62, 0.08);
            border-radius: 16px;
            padding: 1rem 1rem 0.9rem 1rem;
            box-shadow: 0 10px 24px rgba(18, 34, 58, 0.05);
        }
        .issue-shell h3 {
            margin: 0 0 0.55rem 0;
            color: #14263e;
        }
        .issue-text {
            white-space: pre-wrap;
            color: #24364a;
            line-height: 1.5;
            font-size: 0.96rem;
        }
        .timeline-card {
            background: #ffffff;
            border: 1px solid rgba(20, 38, 62, 0.08);
            border-radius: 14px;
            padding: 0.85rem 0.95rem;
            margin-bottom: 0.7rem;
            box-shadow: 0 8px 20px rgba(18, 34, 58, 0.05);
        }
        .timeline-meta {
            color: #607487;
            font-size: 0.84rem;
            margin-bottom: 0.35rem;
        }
        .small-muted {
            color: #6d8192;
            font-size: 0.83rem;
        }
        [data-testid="stMetricValue"] {
            font-weight: 700;
        }
        [data-testid="stMetric"] {
            background: rgba(255, 255, 255, 0.92);
            border: 1px solid rgba(20, 38, 62, 0.07);
            padding: 0.85rem 0.95rem;
            border-radius: 16px;
            box-shadow: 0 8px 24px rgba(18, 34, 58, 0.06);
        }
        .stTabs [data-baseweb="tab-list"] {
            gap: 0.6rem;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 999px;
            padding-left: 1rem;
            padding-right: 1rem;
            height: 2.5rem;
            background: rgba(255, 255, 255, 0.9);
            border: 1px solid rgba(20, 38, 62, 0.08);
        }
        .stTabs [aria-selected="true"] {
            background: #183a63;
            color: white;
        }
        footer, #MainMenu {
            visibility: hidden;
        }
    </style>
    """


def format_dt(value: object) -> str:
    if value is None:
        return "—"
    try:
        if str(value) == "NaT":
            return "—"
    except Exception:
        pass
    if isinstance(value, str):
        try:
            parsed = datetime.fromisoformat(value)
            return parsed.strftime("%b %d, %Y %I:%M %p")
        except Exception:
            return value
    try:
        return value.strftime("%b %d, %Y %I:%M %p")
    except Exception:
        return str(value)


def pct(value: float) -> str:
    return f"{value * 100:.1f}%"


def badge_row(values: list[tuple[str, str]]) -> str:
    pills = []
    for label, tone in values:
        if not label:
            continue
        pills.append(f'<span class="tag-pill {escape(tone)}">{escape(label)}</span>')
    if not pills:
        pills.append('<span class="small-muted">No tags extracted for this issue.</span>')
    return f'<div class="tag-row">{"".join(pills)}</div>'


def issue_text_block(title: str, content: str) -> str:
    safe_content = escape(content.strip() if content.strip() else "No content in the export for this field.")
    return f"""
    <div class="issue-shell">
        <h3>{escape(title)}</h3>
        <div class="issue-text">{safe_content}</div>
    </div>
    """


def timeline_card(timestamp: str, author_id: str, body: str, index: int) -> str:
    safe_body = escape(body.strip() if body.strip() else "Comment body empty after cleanup.")
    return f"""
    <div class="timeline-card">
        <div class="timeline-meta">Comment {index} • {escape(timestamp)} • {escape(author_id or 'Unknown author')}</div>
        <div class="issue-text">{safe_body}</div>
    </div>
    """
