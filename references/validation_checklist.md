# Validation Checklist

Before creating the space, verify:

- [ ] **Title** is a clear, descriptive name (not empty, not generic like "Untitled" or "New Space")
- [ ] **Description** is a one-sentence summary of the space's purpose
- [ ] Space has a **clearly defined purpose** for a specific topic and audience
- [ ] At least one valid Unity Catalog table is specified
- [ ] Tables are **focused** — ideally 5 or fewer, maximum 25
- [ ] Tables exist and user has SELECT permission
- [ ] **Actual column names and values have been inspected** (run `DESCRIBE TABLE` and `SELECT DISTINCT` on key columns)
- [ ] Column names and descriptions are clear and well-annotated in Unity Catalog
- [ ] Warehouse ID is valid and is a pro or serverless SQL warehouse
- [ ] Parent path exists in workspace
- [ ] Sample questions are business-friendly and cover common use cases
- [ ] **SQL expressions** (`sql_snippets`) are defined for key metrics, filters, and dimensions, with table-qualified column references that match `data_sources` tables
- [ ] **Example SQL queries** are included for complex or multi-step questions
- [ ] **All example SQL queries have been executed** and return valid results (no errors, non-empty)
- [ ] **Text instructions** are concise, specific, and non-conflicting
- [ ] Instructions across all types are consistent (e.g., same rounding, same date conventions)
- [ ] **`column_configs`** include `enable_format_assistance: true` and `enable_entity_matching: true` for all string/category filter columns (prompt matching is NOT auto-enabled via API)
- [ ] **No columns are excluded** (`exclude: true`) unless the user explicitly approved them
- [ ] **Benchmarks** are included with 10-20 questions and SQL ground truth
