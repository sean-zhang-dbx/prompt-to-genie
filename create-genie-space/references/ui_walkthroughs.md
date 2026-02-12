# UI Walkthrough Templates

Step-by-step instructions for common changes in the Genie space UI. Use these when guiding users through Mode B (Guided Walkthrough) in the Manage workflow.

---

## Enable Prompt Matching for a Column

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table containing the `{column_name}` column
3. Click on the column → toggle **Prompt matching** to ON
4. **Verify:** Ask a question using a natural-language value (e.g., "North America" instead of "AMER") and confirm Genie maps it correctly

## Hide an Irrelevant Column

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table containing the `{column_name}` column
3. Toggle the column's visibility to **hidden**
4. **Verify:** The column should no longer appear in Genie's generated SQL

## Add Column Synonyms / Descriptions

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table and column you want to annotate
3. Click on the column → add a **description** or **synonyms**
4. **Verify:** Ask a question using the synonym and confirm Genie resolves it correctly

## Add a Benchmark Question

1. Open your Genie space → go to the **Benchmarks** tab
2. Click **Add benchmark** → enter the question text
3. Add a SQL ground truth answer
4. Optionally add 2-4 alternate phrasings with the same SQL answer
5. **Verify:** Run the benchmark and check the rating

## Add Example Values / Value Dictionaries

1. Open your Genie space → click the **gear icon** (settings)
2. Find the column → click **Example values**
3. Add common values users might reference, including variations and abbreviations
4. **Verify:** Ask a question using an abbreviation and confirm Genie matches it

## Add a SQL Expression in the Knowledge Store

1. Open your Genie space → click the **gear icon** (settings)
2. Go to **SQL expressions** → click **Add**
3. Choose the type: Measure, Filter, or Dimension
4. Enter the alias/display name and SQL definition
5. **Verify:** Ask a question referencing the expression name and confirm Genie uses it
