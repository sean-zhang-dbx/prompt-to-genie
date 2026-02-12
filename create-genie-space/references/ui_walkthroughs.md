# UI Walkthrough Templates

Step-by-step instructions for common changes in the Genie space UI. Use these when guiding users through Mode B (Guided Walkthrough) in the Manage workflow.

---

## Enable Prompt Matching for a Column

"Prompt matching" includes two features: **Format assistance** (provides representative values) and **Entity matching** (maps user terms to actual data values like "California" → "CA"). Both are enabled by default when tables are added but can be toggled per-column.

> **Important:** Entity matching requires format assistance. Turning off format assistance automatically disables entity matching.

1. Open your Genie space → click **Configure > Data**
2. Click the table containing the `{column_name}` column
3. Click the **pencil icon** next to the column name
4. Click **Advanced settings**
5. Toggle **Format assistance** ON (if not already)
6. Toggle **Entity matching** ON
7. Click **Save**
8. **Verify:** Ask a question using a natural-language value (e.g., "North America" instead of "AMER") and confirm Genie maps it correctly

> **Limits:** Entity matching supports up to 120 columns per space, with up to 1,024 distinct values per column (max 127 chars each). Tables with row filters or column masks are excluded.

## Hide an Irrelevant Column

Hiding columns reduces ambiguity and helps Genie focus on relevant data. Use this for internal IDs, ETL timestamps, or any columns that aren't useful for business questions.

1. Open your Genie space → click **Configure > Data**
2. Click the table containing the `{column_name}` column
3. Click the **eye icon** next to the column to hide it (or select multiple columns and use **Actions > Hide selected columns**)
4. **Verify:** The column should no longer appear in Genie's generated SQL

> **Tip:** Via the API, set `"exclude": true` in `column_configs` to hide a column programmatically.

## Add Column Synonyms / Descriptions

1. Open your Genie space → click **Configure > Data**
2. Click the table containing the column you want to annotate
3. Click the **pencil icon** next to the column name
4. Edit the **Description** and/or add **Synonyms** (business terms and keywords that help match user language to column names)
5. Click **Save**
6. **Verify:** Ask a question using the synonym and confirm Genie resolves it correctly

## Add a Benchmark Question

1. Open your Genie space → click the **Benchmarks** tab
2. Click **Add benchmark** → enter the question text
3. Add a SQL ground truth answer
4. Optionally add 2-4 alternate phrasings with the same SQL answer
5. **Verify:** Run the benchmark and check the rating

## Refresh Prompt Matching Data

If new values have been added to a column (e.g., a new region code), refresh the stored values so entity matching can recognize them.

1. Open your Genie space → click **Configure > Data**
2. Click the table containing the column
3. Click the **kebab menu** (three dots) next to the column
4. Click **Refresh prompt matching**
5. **Verify:** Ask a question using the new value and confirm Genie matches it correctly

## Add a SQL Expression in the Knowledge Store

1. Open your Genie space → click **Configure > Instructions > SQL Expressions**
2. Click **Add** → choose the type: **Measure**, **Filter**, or **Dimension**
3. Enter the **Name**, **SQL Code**, optional **Synonyms**, and optional **Instructions**
4. Click **Save**
5. **Verify:** Ask a question referencing the expression name and confirm Genie uses it
