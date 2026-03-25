from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

RAW_COLUMN_MAP = {
    "Issue Type": "issue_type",
    "Issue key": "issue_key",
    "Issue id": "issue_id",
    "Description": "description_raw",
    "Custom field (Serial Number)": "serial_number",
    "Custom field (Symptom)": "symptom",
    "Custom field (Symptom).1": "symptom_secondary",
    "Custom field (Disposition)": "disposition",
    "Custom field (SKU(s))": "skus",
    "Custom field (Region)": "region",
    "Custom field (Base SKU)": "base_sku",
    "Custom field (Root Cause)": "root_cause_raw",
    "Custom field (Corrective Action)": "corrective_action_raw",
}

FAILURE_MODE_PATTERNS = {
    "Cracking / breakage": [
        r"\bcrack(?:ed|ing|s)?\b",
        r"\bbrok(?:e|en|ing)\b",
        r"\bbreak(?:age|ing)?\b",
        r"\bfracture\b",
        r"\bsnap(?:ped)?\b",
    ],
    "Leak / seal": [
        r"\bleak(?:age|ing)?\b",
        r"\bseal\b",
        r"\bgap\b",
        r"\bair leak(?:age)?\b",
        r"\bwater leak(?:age)?\b",
    ],
    "Thermal / overheating": [
        r"\boverheat(?:ing)?\b",
        r"\btemperature\b",
        r"\bthermal\b",
        r"\bheater\b",
        r"\btoo hot\b",
        r"\bheat(?:ing)?\b",
    ],
    "Electrical / power": [
        r"\bpower\b",
        r"\bvoltage\b",
        r"\bshort\b",
        r"\bwire\b",
        r"\bcord\b",
        r"\bplug\b",
        r"\bpcba\b",
        r"\belectrical\b",
    ],
    "Noise / vibration": [
        r"\bnoise\b",
        r"\bvibration\b",
        r"\bbuzz(?:ing)?\b",
        r"\brattle\b",
        r"\bsound\b",
        r"\bshake\b",
    ],
    "Performance / airflow": [
        r"\bperformance\b",
        r"\bairflow\b",
        r"\bflow\b",
        r"\bweak\b",
        r"\blow(?:ing)?\b",
        r"\bpressure\b",
        r"\bfunctionality\b",
    ],
    "Appearance / cosmetic": [
        r"\bcolor\b",
        r"\bcosmetic\b",
        r"\bscratch(?:ed)?\b",
        r"\bmark(?:s)?\b",
        r"\bstain(?:ed)?\b",
        r"\btransfer\b",
        r"\bdiscolor(?:ation|ed)?\b",
    ],
    "Fit / alignment": [
        r"\balign(?:ed|ment)?\b",
        r"\bmisalign(?:ed|ment)?\b",
        r"\bfit\b",
        r"\bconcentric\b",
        r"\binterference\b",
        r"\boffset\b",
    ],
    "Assembly / retention": [
        r"\bassembly\b",
        r"\bloose\b",
        r"\bdetach(?:ed|ment)?\b",
        r"\bfall(?:ing)? off\b",
        r"\bcoming off\b",
        r"\bretention\b",
        r"\bfitment\b",
    ],
    "Packaging / documentation": [
        r"\bbox(?:es)?\b",
        r"\bmanual(?:s)?\b",
        r"\bpackag(?:e|ing)\b",
        r"\blabel\b",
        r"\bcarton\b",
    ],
}

COMPONENT_PATTERNS = {
    "Cord / plug": [
        r"\bcord\b",
        r"\bplug\b",
        r"\bprong\b",
        r"\boutlet\b",
        r"\binsulating sleeve\b",
    ],
    "Motor / fan": [
        r"\bmotor\b",
        r"\bfan\b",
        r"\bshaft\b",
        r"\bimpeller\b",
    ],
    "Heater / thermal path": [
        r"\bheater\b",
        r"\bthermal\b",
        r"\bheat\b",
        r"\bhot wire\b",
    ],
    "Housing / cover": [
        r"\bhousing\b",
        r"\bcover\b",
        r"\bshell\b",
        r"\bcasing\b",
        r"\binlet cover\b",
    ],
    "Buttons / controls": [
        r"\bbutton\b",
        r"\bswitch\b",
        r"\bcontrol\b",
        r"\bslider\b",
    ],
    "Brush / curler": [
        r"\bbrush\b",
        r"\bcurler\b",
        r"\bbarrel\b",
        r"\battachment\b",
        r"\baccessor(?:y|ies)\b",
    ],
    "PCB / electronics": [
        r"\bpcba\b",
        r"\bpcb\b",
        r"\bboard\b",
        r"\bconnector\b",
        r"\bsolder\b",
    ],
    "Packaging / paper": [
        r"\bmanual\b",
        r"\bbox\b",
        r"\bcarton\b",
        r"\binsert\b",
        r"\btray\b",
    ],
}

EVIDENCE_PATTERNS = {
    "CT scan": [r"\bct scan\b", r"\blumafield\b"],
    "Drop test": [r"\bdrop test\b", r"\bdrop\b"],
    "Cycle test": [r"\bcycle(?:s)?\b", r"\bcycled\b"],
    "Temperature test": [r"\btemperature\b", r"\btemp\b"],
    "Airflow test": [r"\bairflow\b", r"\bflow rate\b"],
    "Lab review": [r"\blab\b", r"\banalysis\b", r"\breviewed\b"],
}

_COMMENT_COLUMN_PATTERN = re.compile(r"^Comments(?:\.(\d+))?$")


@dataclass(frozen=True)
class ProcessedJiraData:
    issues: pd.DataFrame
    comments: pd.DataFrame
    metadata: dict


def _stringify(value: object) -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return ""
    return str(value)


def clean_jira_markup(text: object, preserve_linebreaks: bool = False) -> str:
    raw = _stringify(text)
    if not raw:
        return ""

    cleaned = raw.replace("\r\n", "\n").replace("\r", "\n")
    cleaned = re.sub(r"!([^!]+)!", " [image] ", cleaned)
    cleaned = re.sub(r"\[([^\]|]+)\|[^\]]+\]", r"\1", cleaned)
    cleaned = re.sub(r"\[~accountid:[^\]]+\]", "@mention", cleaned)
    cleaned = re.sub(r"\{color:[^}]+\}", "", cleaned)
    cleaned = cleaned.replace("{color}", "")
    cleaned = re.sub(r"h[1-6]\.\s*", "", cleaned)
    cleaned = cleaned.replace("||", " | ")
    cleaned = re.sub(r"\*(.*?)\*", r"\1", cleaned)
    cleaned = re.sub(r"_(.*?)_", r"\1", cleaned)
    cleaned = re.sub(r"\{quote\}|\{panel.*?\}|\{code.*?\}|\{noformat\}|\{status.*?\}", "", cleaned)

    if preserve_linebreaks:
        cleaned = re.sub(r"[ \t]+", " ", cleaned)
        cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
        return cleaned.strip()

    cleaned = re.sub(r"\s+", " ", cleaned)
    return cleaned.strip()


def comment_column_order(column_name: str) -> int:
    match = _COMMENT_COLUMN_PATTERN.match(column_name)
    if not match:
        raise ValueError(f"Not a comment column: {column_name}")
    suffix = match.group(1)
    return 1 if suffix is None else int(suffix) + 1


def parse_comment_cell(cell_value: object) -> dict:
    raw = _stringify(cell_value)
    if not raw:
        return {
            "comment_timestamp": pd.NaT,
            "comment_author_id": "",
            "comment_body_raw": "",
            "comment_body_clean": "",
            "comment_has_image": False,
            "comment_has_link": False,
            "comment_mentions": 0,
            "comment_word_count": 0,
        }

    parts = raw.split(";", 2)
    if len(parts) == 3:
        timestamp_text, author_id, body_raw = parts
    else:
        timestamp_text, author_id, body_raw = "", "", raw

    timestamp = pd.to_datetime(timestamp_text, format="%b/%d/%Y %I:%M %p", errors="coerce")
    if pd.isna(timestamp):
        timestamp = pd.to_datetime(timestamp_text, errors="coerce")

    body_clean = clean_jira_markup(body_raw, preserve_linebreaks=True)

    return {
        "comment_timestamp": timestamp,
        "comment_author_id": author_id.strip(),
        "comment_body_raw": body_raw,
        "comment_body_clean": body_clean,
        "comment_has_image": "!" in body_raw and "image" in body_raw.lower(),
        "comment_has_link": "|http" in body_raw.lower() or body_raw.lower().startswith("http"),
        "comment_mentions": len(re.findall(r"\[~accountid:[^\]]+\]", body_raw)),
        "comment_word_count": len(re.findall(r"\b\w+\b", body_clean)),
    }


def _extract_tags(text: str, pattern_map: dict[str, Iterable[str]]) -> list[str]:
    tags: list[str] = []
    lowered = text.lower()
    for label, patterns in pattern_map.items():
        for pattern in patterns:
            if re.search(pattern, lowered):
                tags.append(label)
                break
    return tags


def _choose_primary_tag(tag_string: str, fallback: str = "Unclassified") -> str:
    if not tag_string:
        return fallback
    return tag_string.split(" | ")[0]


def _join_non_empty(parts: Iterable[object], sep: str = "\n\n") -> str:
    cleaned_parts = [str(part).strip() for part in parts if str(part).strip()]
    return sep.join(cleaned_parts)


def _prepare_issue_frame(df: pd.DataFrame) -> pd.DataFrame:
    issues = df.rename(columns=RAW_COLUMN_MAP).copy()
    issues = issues[[column for column in RAW_COLUMN_MAP.values() if column in issues.columns]]

    text_columns = ["description_raw", "root_cause_raw", "corrective_action_raw"]
    for column in text_columns:
        issues[column] = issues[column].fillna("")
        issues[column.replace("_raw", "_clean")] = issues[column].map(lambda value: clean_jira_markup(value, preserve_linebreaks=True))

    for column in ["issue_key", "issue_type", "serial_number", "symptom", "symptom_secondary", "disposition", "skus", "region", "base_sku"]:
        if column in issues.columns:
            issues[column] = issues[column].fillna("").astype(str).str.strip()

    return issues


def _prepare_comment_frame(df: pd.DataFrame) -> pd.DataFrame:
    comment_columns = sorted((column for column in df.columns if column.startswith("Comments")), key=comment_column_order)
    if not comment_columns:
        return pd.DataFrame(
            columns=[
                "issue_key",
                "comment_slot",
                "comment_index",
                "comment_timestamp",
                "comment_author_id",
                "comment_body_raw",
                "comment_body_clean",
                "comment_has_image",
                "comment_has_link",
                "comment_mentions",
                "comment_word_count",
            ]
        )

    comments_wide = df[["Issue key", *comment_columns]].copy()
    comments_long = comments_wide.melt(id_vars="Issue key", var_name="comment_slot", value_name="comment_cell")
    comments_long = comments_long.dropna(subset=["comment_cell"]).reset_index(drop=True)
    comments_long["comment_index"] = comments_long["comment_slot"].map(comment_column_order)
    parsed = comments_long["comment_cell"].map(parse_comment_cell).apply(pd.Series)

    comments = pd.concat([comments_long[["Issue key", "comment_slot", "comment_index"]], parsed], axis=1)
    comments = comments.rename(columns={"Issue key": "issue_key"})
    comments = comments.sort_values(["issue_key", "comment_index"]).reset_index(drop=True)
    comments["comment_month"] = comments["comment_timestamp"].dt.to_period("M").astype(str)
    return comments


def _build_issue_enrichment(issues: pd.DataFrame, comments: pd.DataFrame) -> pd.DataFrame:
    comment_agg = (
        comments.groupby("issue_key", dropna=False)
        .agg(
            comment_count=("comment_index", "count"),
            first_comment_at=("comment_timestamp", "min"),
            latest_comment_at=("comment_timestamp", "max"),
            unique_comment_authors=("comment_author_id", lambda series: series.replace("", np.nan).dropna().nunique()),
            comments_with_images=("comment_has_image", "sum"),
            comments_with_links=("comment_has_link", "sum"),
            total_comment_words=("comment_word_count", "sum"),
        )
        .reset_index()
    )
    comment_text = (
        comments.groupby("issue_key", dropna=False)["comment_body_clean"]
        .apply(lambda series: "\n\n".join(text for text in series if str(text).strip()))
        .reset_index(name="comments_text_clean")
    )

    issues = issues.merge(comment_agg, on="issue_key", how="left")
    issues = issues.merge(comment_text, on="issue_key", how="left")

    numeric_fill_zero = [
        "comment_count",
        "unique_comment_authors",
        "comments_with_images",
        "comments_with_links",
        "total_comment_words",
    ]
    for column in numeric_fill_zero:
        issues[column] = issues[column].fillna(0).astype(int)

    issues["comments_text_clean"] = issues["comments_text_clean"].fillna("")
    issues["analysis_text"] = issues.apply(
        lambda row: _join_non_empty(
            [
                row.get("description_clean", ""),
                row.get("root_cause_clean", ""),
                row.get("corrective_action_clean", ""),
                row.get("comments_text_clean", ""),
            ]
        ),
        axis=1,
    )

    issues["failure_modes"] = issues["analysis_text"].map(lambda text: " | ".join(_extract_tags(text, FAILURE_MODE_PATTERNS)))
    issues["components"] = issues["analysis_text"].map(lambda text: " | ".join(_extract_tags(text, COMPONENT_PATTERNS)))
    issues["evidence_tags"] = issues["analysis_text"].map(lambda text: " | ".join(_extract_tags(text, EVIDENCE_PATTERNS)))
    issues["primary_failure_mode"] = issues["failure_modes"].map(_choose_primary_tag)
    issues["primary_component"] = issues["components"].map(_choose_primary_tag)

    for column, source in {
        "has_description": "description_clean",
        "has_root_cause": "root_cause_clean",
        "has_corrective_action": "corrective_action_clean",
        "has_serial_number": "serial_number",
        "has_symptom": "symptom",
        "has_skus": "skus",
    }.items():
        issues[column] = issues[source].fillna("").astype(str).str.strip().ne("")

    issues["has_comments"] = issues["comment_count"] > 0
    issues["has_image_evidence"] = issues["comments_with_images"] > 0
    issues["has_link_evidence"] = issues["comments_with_links"] > 0

    issues["investigation_status"] = np.select(
        [
            issues["has_root_cause"] & issues["has_corrective_action"],
            issues["has_root_cause"] & ~issues["has_corrective_action"],
            ~issues["has_root_cause"] & issues["has_corrective_action"],
        ],
        [
            "Root cause + action",
            "Root cause only",
            "Corrective action only",
        ],
        default="Missing both",
    )

    activity_window = (issues["latest_comment_at"] - issues["first_comment_at"]).dt.days
    issues["activity_window_days"] = activity_window.fillna(0).clip(lower=0).astype(int)
    issues["issue_word_count"] = issues["analysis_text"].map(lambda text: len(re.findall(r"\b\w+\b", text)))
    issues["search_text"] = issues.apply(
        lambda row: " ".join(
            part
            for part in [
                row.get("issue_key", ""),
                row.get("issue_type", ""),
                row.get("base_sku", ""),
                row.get("skus", ""),
                row.get("symptom", ""),
                row.get("primary_failure_mode", ""),
                row.get("primary_component", ""),
                row.get("analysis_text", ""),
            ]
            if str(part).strip()
        ).lower(),
        axis=1,
    )

    return issues


def _build_metadata(raw_df: pd.DataFrame, issues: pd.DataFrame, comments: pd.DataFrame) -> dict:
    completeness = {}
    tracked_columns = [
        "description_clean",
        "root_cause_clean",
        "corrective_action_clean",
        "serial_number",
        "symptom",
        "skus",
        "base_sku",
    ]
    for column in tracked_columns:
        if column in issues.columns:
            completeness[column] = round(float(issues[column].fillna("").astype(str).str.strip().ne("").mean()), 4)

    metadata = {
        "row_count_raw": int(len(raw_df)),
        "column_count_raw": int(raw_df.shape[1]),
        "issue_count": int(len(issues)),
        "comment_count": int(len(comments)),
        "distinct_issue_types": sorted(issue for issue in issues["issue_type"].dropna().unique().tolist() if issue),
        "base_sku_count": int(issues["base_sku"].replace("", np.nan).dropna().nunique()),
        "activity_start": None if comments.empty else comments["comment_timestamp"].min().isoformat(),
        "activity_end": None if comments.empty else comments["comment_timestamp"].max().isoformat(),
        "completeness": completeness,
        "comment_columns_detected": int(sum(1 for column in raw_df.columns if column.startswith("Comments"))),
    }
    return metadata


def process_dataframe(raw_df: pd.DataFrame) -> ProcessedJiraData:
    issues = _prepare_issue_frame(raw_df)
    comments = _prepare_comment_frame(raw_df)
    issues = _build_issue_enrichment(issues, comments)

    issue_column_order = [
        "issue_key",
        "issue_id",
        "issue_type",
        "base_sku",
        "skus",
        "serial_number",
        "symptom",
        "symptom_secondary",
        "disposition",
        "region",
        "has_description",
        "has_root_cause",
        "has_corrective_action",
        "has_serial_number",
        "has_symptom",
        "has_skus",
        "has_comments",
        "comment_count",
        "unique_comment_authors",
        "comments_with_images",
        "comments_with_links",
        "activity_window_days",
        "first_comment_at",
        "latest_comment_at",
        "investigation_status",
        "primary_failure_mode",
        "primary_component",
        "failure_modes",
        "components",
        "evidence_tags",
        "has_image_evidence",
        "has_link_evidence",
        "issue_word_count",
        "description_raw",
        "description_clean",
        "root_cause_raw",
        "root_cause_clean",
        "corrective_action_raw",
        "corrective_action_clean",
        "comments_text_clean",
        "analysis_text",
        "search_text",
    ]
    ordered_existing_columns = [column for column in issue_column_order if column in issues.columns]
    remaining_columns = [column for column in issues.columns if column not in ordered_existing_columns]
    issues = issues[ordered_existing_columns + remaining_columns].sort_values("issue_key").reset_index(drop=True)

    metadata = _build_metadata(raw_df, issues, comments)
    return ProcessedJiraData(issues=issues, comments=comments, metadata=metadata)


def process_csv(input_path: Path, output_dir: Path) -> ProcessedJiraData:
    raw_df = pd.read_csv(input_path)
    processed = process_dataframe(raw_df)

    output_dir.mkdir(parents=True, exist_ok=True)
    issues_path = output_dir / "issues_clean.csv"
    comments_path = output_dir / "comments_long.csv"
    metadata_path = output_dir / "metadata.json"

    processed.issues.to_csv(issues_path, index=False)
    processed.comments.to_csv(comments_path, index=False)
    metadata_path.write_text(json.dumps(processed.metadata, indent=2), encoding="utf-8")

    return processed


def process_uploaded_bytes(file_bytes: bytes) -> ProcessedJiraData:
    raw_df = pd.read_csv(BytesIO(file_bytes))
    return process_dataframe(raw_df)


DEFAULT_INPUT = Path(__file__).resolve().parents[1] / "data" / "raw" / "Jira - SharkNinja (20).csv"
DEFAULT_OUTPUT_DIR = Path(__file__).resolve().parents[1] / "data" / "processed"


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize a Jira CSV export for dashboarding.")
    parser.add_argument("--input", type=Path, default=DEFAULT_INPUT)
    parser.add_argument("--output-dir", type=Path, default=DEFAULT_OUTPUT_DIR)
    args = parser.parse_args()

    processed = process_csv(args.input, args.output_dir)
    print(f"Processed {len(processed.issues):,} issues and {len(processed.comments):,} comments.")
    print(f"Outputs written to: {args.output_dir}")


if __name__ == "__main__":
    main()
