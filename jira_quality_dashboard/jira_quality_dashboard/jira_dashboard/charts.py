from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


PLOTLY_TEMPLATE = "plotly_white"


def apply_chart_style(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        template=PLOTLY_TEMPLATE,
        height=height,
        margin=dict(l=16, r=16, t=48, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="#FFFFFF",
        font=dict(size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0),
        hoverlabel=dict(font_size=12),
    )
    fig.update_xaxes(gridcolor="#E7ECF3", zerolinecolor="#E7ECF3")
    fig.update_yaxes(gridcolor="#E7ECF3", zerolinecolor="#E7ECF3")
    return fig


def empty_figure(message: str) -> go.Figure:
    fig = go.Figure()
    fig.add_annotation(text=message, x=0.5, y=0.5, xref="paper", yref="paper", showarrow=False, font=dict(size=16))
    fig.update_xaxes(visible=False)
    fig.update_yaxes(visible=False)
    return apply_chart_style(fig, height=280)


def issue_type_donut(issues: pd.DataFrame) -> go.Figure:
    if issues.empty:
        return empty_figure("No issue data after filters")
    counts = issues.groupby("issue_type", dropna=False).size().reset_index(name="issues")
    fig = px.pie(counts, names="issue_type", values="issues", hole=0.62, title="Issue type mix")
    fig.update_traces(textposition="inside", textinfo="percent+label", hovertemplate="%{label}: %{value}<extra></extra>")
    return apply_chart_style(fig, height=350)


def top_base_sku_bar(issues: pd.DataFrame, top_n: int = 12) -> go.Figure:
    if issues.empty:
        return empty_figure("No base SKU data after filters")
    frame = (
        issues[issues["base_sku"].fillna("").str.strip() != ""]
        .groupby("base_sku", dropna=False)
        .size()
        .reset_index(name="issues")
        .sort_values("issues", ascending=True)
        .tail(top_n)
    )
    fig = px.bar(frame, x="issues", y="base_sku", orientation="h", text="issues", title=f"Top {min(top_n, len(frame))} base SKUs by issue count")
    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x}<extra></extra>")
    return apply_chart_style(fig, height=420)


def activity_line(activity: pd.DataFrame, title: str = "Comment activity by month") -> go.Figure:
    if activity.empty:
        return empty_figure("No dated comments available")
    fig = px.line(activity, x="month", y=activity.columns[-1], markers=True, title=title)
    fig.update_traces(hovertemplate="%{x|%b %Y}: %{y}<extra></extra>")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_chart_style(fig, height=360)


def top_tag_bar(issues: pd.DataFrame, column: str, title: str, top_n: int = 12) -> go.Figure:
    if issues.empty:
        return empty_figure("No data available")
    exploded = (
        issues.assign(_tag=issues[column].fillna("").str.split(" | "))
        .explode("_tag")
        .assign(_tag=lambda frame: frame["_tag"].fillna("").str.strip())
    )
    exploded = exploded[exploded["_tag"] != ""]
    if exploded.empty:
        return empty_figure("No tagged issues for the current filters")
    frame = (
        exploded.groupby("_tag", dropna=False)
        .size()
        .reset_index(name="issues")
        .sort_values("issues", ascending=True)
        .tail(top_n)
    )
    fig = px.bar(frame, x="issues", y="_tag", orientation="h", text="issues", title=title)
    fig.update_traces(textposition="outside", cliponaxis=False, hovertemplate="%{y}: %{x}<extra></extra>")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_chart_style(fig, height=420)


def sku_quality_scatter(sku_rollup: pd.DataFrame) -> go.Figure:
    if sku_rollup.empty:
        return empty_figure("No SKU rollup available")
    fig = px.scatter(
        sku_rollup,
        x="issues",
        y="root_cause_coverage",
        size="avg_comments",
        hover_name="base_sku",
        text="base_sku",
        title="Base SKU quality view",
        labels={"issues": "Issue count", "root_cause_coverage": "Root cause coverage"},
    )
    fig.update_traces(textposition="top center", hovertemplate="%{hovertext}<br>Issues: %{x}<br>Root cause coverage: %{y:.0%}<br>Avg comments: %{marker.size:.1f}<extra></extra>")
    fig.update_yaxes(tickformat=".0%", range=[0, 1])
    return apply_chart_style(fig, height=420)


def stacked_status_by_base_sku(issues: pd.DataFrame, top_n: int = 10) -> go.Figure:
    if issues.empty:
        return empty_figure("No issue data available")
    base = (
        issues[issues["base_sku"].fillna("").str.strip() != ""]
        .groupby("base_sku", dropna=False)
        .size()
        .reset_index(name="issues")
        .sort_values("issues", ascending=False)
        .head(top_n)
    )
    if base.empty:
        return empty_figure("No base SKU values available")
    selected_skus = base["base_sku"].tolist()
    frame = (
        issues[issues["base_sku"].isin(selected_skus)]
        .groupby(["base_sku", "investigation_status"], dropna=False)
        .size()
        .reset_index(name="issues")
    )
    fig = px.bar(frame, x="base_sku", y="issues", color="investigation_status", title="Investigation status by base SKU")
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_chart_style(fig, height=420)


def completeness_bar(completeness: pd.DataFrame) -> go.Figure:
    if completeness.empty:
        return empty_figure("No completeness scores available")
    fig = px.bar(
        completeness,
        x="coverage",
        y="field",
        orientation="h",
        text="coverage_pct",
        title="Data completeness for key fields",
        labels={"coverage": "Coverage", "field": ""},
    )
    fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside", cliponaxis=False)
    fig.update_xaxes(tickformat=".0%", range=[0, 1])
    return apply_chart_style(fig, height=360)


def investigation_status_bar(issues: pd.DataFrame) -> go.Figure:
    if issues.empty:
        return empty_figure("No issue data after filters")
    frame = issues.groupby("investigation_status", dropna=False).size().reset_index(name="issues")
    fig = px.bar(frame, x="investigation_status", y="issues", text="issues", title="Investigation status")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_chart_style(fig, height=340)


def issue_health_scatter(issues: pd.DataFrame) -> go.Figure:
    if issues.empty:
        return empty_figure("No issue data after filters")
    frame = issues.copy()
    frame["hover_text"] = frame["issue_key"] + " | " + frame["base_sku"].fillna("")
    fig = px.scatter(
        frame,
        x="comment_count",
        y="activity_window_days",
        color="investigation_status",
        hover_name="hover_text",
        size="comments_with_images",
        title="Issue heat map: discussion load vs activity window",
        labels={"comment_count": "Comments", "activity_window_days": "Activity window (days)"},
        hover_data={"primary_failure_mode": True, "primary_component": True, "comments_with_images": True},
    )
    return apply_chart_style(fig, height=420)


def author_bar(author_rollup: pd.DataFrame) -> go.Figure:
    if author_rollup.empty:
        return empty_figure("No comment author data available")
    frame = author_rollup.sort_values("comments", ascending=True)
    fig = px.bar(frame, x="comments", y="comment_author_id", orientation="h", text="comments", title="Most active comment authors")
    fig.update_traces(textposition="outside", cliponaxis=False)
    fig.update_xaxes(title_text="")
    fig.update_yaxes(title_text="")
    return apply_chart_style(fig, height=420)
