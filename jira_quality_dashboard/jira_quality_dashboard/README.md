# Jira Quality Command Center

A clean Streamlit dashboard starter built around the uploaded SharkNinja Jira export.

The project does three things first:
1. normalizes the raw Jira CSV into an issue table and a long-form comment table,
2. adds practical rule-based tags for failure modes, components, and evidence signals,
3. surfaces the data in a polished Streamlit app designed to be extended with AI later.

## What is included

```text
jira_quality_dashboard/
├── app.py
├── README.md
├── requirements.txt
├── .streamlit/
│   └── config.toml
├── data/
│   ├── raw/
│   │   └── Jira - SharkNinja (20).csv
│   └── processed/
│       ├── issues_clean.csv
│       ├── comments_long.csv
│       └── metadata.json
└── jira_dashboard/
    ├── __init__.py
    ├── charts.py
    ├── insights.py
    ├── preprocess.py
    └── styles.py
```

## Dashboard sections

### Executive overview
- KPI strip for issues, comments, coverage, and discussion volume
- issue mix by type
- top base SKUs by issue count
- monthly comment activity
- extracted failure mode concentration

### Quality drivers
- failure mode and component concentration
- base SKU quality scatter
- investigation status by base SKU
- evidence and test-signal tags
- issue first-seen proxy based on the first dated comment

### Investigation health
- missing root-cause and corrective-action counts
- completeness coverage chart
- issue discussion vs activity-window heat map
- discussion-heavy queue with no root cause yet captured

### Issue explorer
- clean single-issue view
- structured fields
- normalized comment timeline

### AI-ready foundation
- shows the fields already prepared for semantic search, summarization, clustering, and duplicate detection

## Run locally

```bash
cd jira_quality_dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Refresh the processed data

If you replace the raw CSV file, rebuild the processed data with:

```bash
python -m jira_dashboard.preprocess
```

Or just upload a new CSV inside the app from the sidebar.

## Notes about the source export

- The raw CSV stores comments across many repeated columns (`Comments`, `Comments.1`, `Comments.2`, ...). The preprocessing step reshapes them into `comments_long.csv`.
- The export does **not** include explicit issue created / resolved timestamps, so timeline views use comment timestamps as the operational activity proxy.
- Root-cause and corrective-action fields are already useful enough to track investigation quality.
- Some custom fields are sparse in this export, so the dashboard emphasizes fields that are consistently present.

## AI next steps

The best sequence from here is:
1. validate the dashboard and cleaned schema with the team,
2. add semantic search over `analysis_text` and the comment timeline,
3. add issue summaries and duplicate detection,
4. add guided root-cause and corrective-action copilots.

That keeps the build incremental and avoids over-engineering before the data model is solid.
