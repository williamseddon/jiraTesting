from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Iterable

import numpy as np
import pandas as pd


@dataclass(frozen=True)
class DashboardFilters:
    base_skus: tuple[str, ...] = ()
    issue_types: tuple[str, ...] = ()
    failure_modes: tuple[str, ...] = ()
    components: tuple[str, ...] = ()
    investigation_view: str = "All"
    min_comments: int = 0
    latest_activity_range: tuple[date, date] | None = None
    search_query: str = ""


def unique_non_empty(series: pd.Series) -> list[str]:
    return sorted({str(value).strip() for value in series.dropna().tolist() if str(value).strip()})


def split_tag_values(series: pd.Series) -> list[str]:
    values: set[str] = set()
    for value in series.fillna(""):
        for part in str(value).split(" | "):
            part = part.strip()
            if part:
                values.add(part)
    return sorted(values)


def _contains_any_tag(cell_value: object, selected_tags: Iterable[str]) -> bool:
    if not selected_tags:
        return True
    tags = {tag.strip() for tag in str(cell_value or "").split(" | ") if tag.strip()}
    return bool(tags.intersection(selected_tags))


def _matches_search(search_text: str, query: str) -> bool:
    if not query.strip():
        return True
    haystack = str(search_text or "")
    tokens = [token.lower() for token in query.split() if token.strip()]
    return all(token in haystack for token in tokens)


def filter_issues(issues: pd.DataFrame, filters: DashboardFilters) -> pd.DataFrame:
    filtered = issues.copy()

    if filters.base_skus:
        filtered = filtered[filtered["base_sku"].isin(filters.base_skus)]
    if filters.issue_types:
        filtered = filtered[filtered["issue_type"].isin(filters.issue_types)]
    if filters.failure_modes:
        filtered = filtered[filtered["failure_modes"].map(lambda value: _contains_any_tag(value, filters.failure_modes))]
    if filters.components:
        filtered = filtered[filtered["components"].map(lambda value: _contains_any_tag(value, filters.components))]

    view = filters.investigation_view
    if view == "Has root cause":
        filtered = filtered[filtered["has_root_cause"]]
    elif view == "Missing root cause":
        filtered = filtered[~filtered["has_root_cause"]]
    elif view == "Has corrective action":
        filtered = filtered[filtered["has_corrective_action"]]
    elif view == "Missing corrective action":
        filtered = filtered[~filtered["has_corrective_action"]]
    elif view == "Missing both":
        filtered = filtered[filtered["investigation_status"] == "Missing both"]
    elif view == "Root cause + action":
        filtered = filtered[filtered["investigation_status"] == "Root cause + action"]

    filtered = filtered[filtered["comment_count"] >= filters.min_comments]

    if filters.latest_activity_range and filtered["latest_comment_at"].notna().any():
        start_date, end_date = filters.latest_activity_range
        latest_activity = pd.to_datetime(filtered["latest_comment_at"]).dt.date
        filtered = filtered[(latest_activity >= start_date) & (latest_activity <= end_date)]

    if filters.search_query.strip():
        filtered = filtered[filtered["search_text"].map(lambda value: _matches_search(value, filters.search_query))]

    return filtered.reset_index(drop=True)


def filter_comments(comments: pd.DataFrame, filtered_issues: pd.DataFrame) -> pd.DataFrame:
    if comments.empty or filtered_issues.empty:
        return comments.iloc[0:0].copy()
    return comments[comments["issue_key"].isin(filtered_issues["issue_key"])].copy().reset_index(drop=True)


def build_kpis(issues: pd.DataFrame, comments: pd.DataFrame) -> dict[str, float | int]:
    issue_count = int(len(issues))
    comment_count = int(len(comments))
    base_sku_count = int(issues["base_sku"].replace("", np.nan).dropna().nunique()) if issue_count else 0
    root_cause_coverage = float(issues["has_root_cause"].mean()) if issue_count else 0.0
    corrective_action_coverage = float(issues["has_corrective_action"].mean()) if issue_count else 0.0
    median_comments = float(issues["comment_count"].median()) if issue_count else 0.0
    high_discussion_missing_rc = int(((issues["comment_count"] >= 5) & (~issues["has_root_cause"])).sum()) if issue_count else 0

    return {
        "issue_count": issue_count,
        "comment_count": comment_count,
        "base_sku_count": base_sku_count,
        "root_cause_coverage": root_cause_coverage,
        "corrective_action_coverage": corrective_action_coverage,
        "median_comments": median_comments,
        "high_discussion_missing_rc": high_discussion_missing_rc,
    }


def build_completeness_frame(issues: pd.DataFrame) -> pd.DataFrame:
    coverage_rows = [
        ("Description present", issues["has_description"].mean()),
        ("Root cause present", issues["has_root_cause"].mean()),
        ("Corrective action present", issues["has_corrective_action"].mean()),
        ("SKU present", issues["has_skus"].mean()),
        ("Serial number present", issues["has_serial_number"].mean()),
        ("Symptom present", issues["has_symptom"].mean()),
        ("Has comments", issues["has_comments"].mean()),
    ]
    completeness = pd.DataFrame(coverage_rows, columns=["field", "coverage"])
    completeness["coverage_pct"] = (completeness["coverage"] * 100).round(1)
    return completeness.sort_values("coverage", ascending=True).reset_index(drop=True)


def build_sku_rollup(issues: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    sku_rollup = (
        issues[issues["base_sku"].fillna("").str.strip() != ""]
        .groupby("base_sku", dropna=False)
        .agg(
            issues=("issue_key", "count"),
            root_cause_coverage=("has_root_cause", "mean"),
            corrective_action_coverage=("has_corrective_action", "mean"),
            avg_comments=("comment_count", "mean"),
            median_comments=("comment_count", "median"),
        )
        .reset_index()
        .sort_values("issues", ascending=False)
        .head(top_n)
    )
    for column in ["root_cause_coverage", "corrective_action_coverage", "avg_comments", "median_comments"]:
        sku_rollup[column] = sku_rollup[column].round(3 if "coverage" in column else 1)
    return sku_rollup


def build_issue_table(issues: pd.DataFrame) -> pd.DataFrame:
    columns = [
        "issue_key",
        "issue_type",
        "base_sku",
        "primary_failure_mode",
        "primary_component",
        "comment_count",
        "investigation_status",
        "latest_comment_at",
        "description_clean",
    ]
    table = issues[columns].copy()
    table["description_clean"] = table["description_clean"].fillna("").astype(str).str.slice(0, 180)
    return table.rename(columns={"description_clean": "description_preview"})


def build_activity_series(comments: pd.DataFrame) -> pd.DataFrame:
    if comments.empty:
        return pd.DataFrame(columns=["month", "comments"])
    activity = (
        comments.dropna(subset=["comment_timestamp"])
        .assign(month=lambda frame: frame["comment_timestamp"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", dropna=False)
        .size()
        .reset_index(name="comments")
    )
    return activity.sort_values("month").reset_index(drop=True)


def build_issue_first_seen_series(issues: pd.DataFrame) -> pd.DataFrame:
    if issues["first_comment_at"].notna().sum() == 0:
        return pd.DataFrame(columns=["month", "issues_first_seen"])
    first_seen = (
        issues.dropna(subset=["first_comment_at"])
        .assign(month=lambda frame: frame["first_comment_at"].dt.to_period("M").dt.to_timestamp())
        .groupby("month", dropna=False)
        .size()
        .reset_index(name="issues_first_seen")
    )
    return first_seen.sort_values("month").reset_index(drop=True)


def build_author_rollup(comments: pd.DataFrame, top_n: int = 15) -> pd.DataFrame:
    if comments.empty:
        return pd.DataFrame(columns=["comment_author_id", "comments", "issues_touched"])
    author_rollup = (
        comments[comments["comment_author_id"].fillna("").str.strip() != ""]
        .groupby("comment_author_id", dropna=False)
        .agg(comments=("comment_index", "count"), issues_touched=("issue_key", "nunique"))
        .reset_index()
        .sort_values(["comments", "issues_touched"], ascending=False)
        .head(top_n)
    )
    return author_rollup


def build_risk_queue(issues: pd.DataFrame, min_comments: int = 5, top_n: int = 25) -> pd.DataFrame:
    risk_queue = issues[(issues["comment_count"] >= min_comments) & (~issues["has_root_cause"])].copy()
    if risk_queue.empty:
        return risk_queue[["issue_key"]].iloc[0:0]

    risk_queue["priority_score"] = (
        risk_queue["comment_count"]
        + risk_queue["activity_window_days"].clip(upper=90) / 10
        + risk_queue["comments_with_images"]
    )
    columns = [
        "issue_key",
        "base_sku",
        "issue_type",
        "comment_count",
        "activity_window_days",
        "comments_with_images",
        "latest_comment_at",
        "primary_failure_mode",
        "priority_score",
        "description_clean",
    ]
    risk_queue = risk_queue[columns].sort_values(["priority_score", "comment_count"], ascending=False).head(top_n)
    risk_queue["priority_score"] = risk_queue["priority_score"].round(1)
    risk_queue["description_clean"] = risk_queue["description_clean"].fillna("").astype(str).str.slice(0, 180)
    return risk_queue.rename(columns={"description_clean": "description_preview"})
