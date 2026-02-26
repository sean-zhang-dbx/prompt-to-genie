# Diagnose and Optimize an Existing Space

Use this workflow when a user has an existing Genie space and wants to review, fix, or improve it. Ask the user for their **space ID** to get started.

## Step 1: Retrieve Current Configuration

Fetch the existing space configuration and parse it into a human-readable summary.

**Important:** The GET space API does **not** return `serialized_space` by default. You must pass the query parameter `include_serialized_space=true` to include it in the response. This requires at least **CAN EDIT** permission on the space.

**Reference script:** See `scripts/manage_space.py` (Part 1) for the complete retrieval and summary code. It displays all tables, sample questions, example SQL queries, SQL functions, text instructions, and the instruction count audit.


After retrieving the config, present the summary to the user and ask what they'd like to do: audit, diagnose a specific issue, or optimize.

## Step 2: Audit Against Best Practices

Work through this checklist automatically after retrieving the configuration. Flag any issues and present findings to the user.

### Data Source Audit

**Reference script:** Use `scripts/discover_resources.py` (Part 2) to automate this audit. It checks all of the following and produces a quality score with actionable recommendations.

- [ ] **Table count**: Are there ≤5 tables? (ideal) Are there ≤25? (maximum)
- [ ] **Table comments**: Does each table have a descriptive comment?
- [ ] **Column descriptions**: For each table, check if columns have descriptions. Flag tables with missing or unclear descriptions.
- [ ] **Column count**: Tables with 30+ columns may cause ambiguity — recommend hiding irrelevant columns or creating focused views.
- [ ] **Overlapping columns**: Check if multiple tables have columns with similar names that could cause ambiguity. Recommend hiding or removing duplicates.
- [ ] **Foreign keys / join relationships**: Check if tables have foreign key constraints defined. If not, recommend defining join relationships in the knowledge store.

### Instruction Audit
- [ ] **Example SQL queries present?** If none exist, strongly recommend adding them — they are the most effective way to improve accuracy.
- [ ] **Parameterized queries?** If there are example SQL queries but none use parameters, recommend converting recurring filter-based queries to parameterized versions for trusted asset labeling.
- [ ] **Text instruction quality**: Review text instructions for:
  - Vagueness (e.g., "handle sales questions appropriately" — flag and suggest specific rewording)
  - Excessive length (>2000 characters — suggest moving specific metrics to SQL expressions)
  - Missing clarification question instructions for ambiguous topics
- [ ] **Instruction consistency**: Check for conflicts between text instructions and example SQL (e.g., different rounding, different date conventions).
- [ ] **Instruction count**: Calculate total (each SQL query + each function + 1 for text block). Warn if approaching the 100 limit.

### Configuration Audit
- [ ] **Sample questions**: Are there at least 3? Do they cover the space's stated purpose?
- [ ] **Description quality**: Is the space description clear and informative?
- [ ] **Prompt matching**: Verify that **format assistance** and **entity matching** are enabled for key filter columns (Configure > Data > column > Advanced settings). These are auto-enabled via UI but **off by default for API-created spaces** — check especially if the space was created programmatically.
- [ ] **Cross-section consistency**: Do `text_instructions`, `example_question_sqls`, and `sql_snippets` all align? No stale or contradictory guidance?

**Present findings** to the user as a prioritized list, starting with the highest-impact improvements.

## Step 3: Diagnose Reported Issues

If the user reports a specific problem, use this decision tree to triage:

**"Genie uses the wrong table or column"**
1. Check table/column descriptions — do they match user terminology?
2. Look for overlapping column names across tables
3. Recommend: Add example SQL queries showing correct usage, hide confusing columns

**"Genie misunderstands our terminology"**
1. Check if the term is defined in text instructions or SQL expressions
2. Check column synonyms in the knowledge store
3. Recommend: Add a SQL expression or text instruction mapping the term to the correct data concept

**"Genie filters on wrong values"** (e.g., "California" vs "CA")
1. Check if **entity matching** and **format assistance** are enabled for the relevant column (Configure > Data > column > Advanced settings)
2. Check if prompt matching data is up to date (kebab menu > Refresh prompt matching)
3. Recommend: Enable entity matching (requires format assistance), refresh values if data changed

**"Genie joins tables incorrectly"**
1. Check for foreign key constraints in Unity Catalog
2. Check join relationships in the knowledge store
3. Recommend: Define join relationships or add example SQL queries with correct joins

**"Metric calculations are wrong"**
1. Check if the metric is defined as a SQL expression
2. Check if there's an example SQL query computing it correctly
3. Check for pre-aggregated tables that might be double-counted
4. Recommend: Add SQL expressions for metrics, or example SQL for complex calculations

**"Timezone/date calculations are wrong"**
1. Check text instructions for timezone guidance
2. Recommend: Add explicit instructions like "Time zones are in UTC. Convert using convert_timezone('UTC', 'America/Los_Angeles', <column>)."

**"Genie ignores my instructions"**
1. Check for conflicting instructions across types
2. Check if the instruction count is high (noise drowns out signal)
3. Recommend: Add example SQL (most effective), hide irrelevant columns, simplify instruction set, start a new chat for testing

**"Responses are slow or timing out"**
1. Check query history for slow queries
2. Recommend: Use trusted assets for complex logic, reduce example SQL length, start new chat

**"Token limit warning"**
1. Audit column count and descriptions for bloat
2. Recommend: Hide unnecessary columns, streamline descriptions, prune redundant example SQL

## Step 4: Recommend Optimizations

After auditing the config and/or diagnosing issues, proactively suggest improvements. Frame recommendations as specific, actionable changes with clear rationale.

**Example recommendations:**

- "You have 5 example SQL queries but none use parameters. Consider converting the 2 queries that filter by region to use `:region` parameters — this gives users trusted asset labeling and lets them change the filter value."
- "Your text instructions are 1800 characters with 6 metric definitions inline. Consider moving those metrics to SQL expressions in the knowledge store — they're more precise and reduce text instruction length."
- "Tables `orders` and `order_details` both have a `total` column. This likely causes ambiguity. Recommend hiding `order_details.total` or renaming via a view."
- "No benchmark questions found. Recommend adding 10-20 benchmarks covering the sample questions (with 2-4 phrasings each) to track accuracy as you iterate."
- "You have 18 tables — this is above the recommended 5. Consider prejoining related dimension tables into views to reduce complexity."
- "Column `forecastcategory` in `opportunity` has no description. Genie may misinterpret it. Add a description like 'Forecast stage: Pipeline, Best Case, Commit, Closed.'"

**Always present a summary** of proposed changes before applying them.

## Step 5: Apply Updates

After the user approves changes, apply them via the PATCH API.

### Review All Config Sections Before Updating

When making changes to any part of the configuration, **review all related sections for consistency**. Common mistakes:

- Updating `example_question_sqls` but leaving stale `text_instructions` that contradict the new SQL
- Adding new SQL expressions but forgetting to update `text_instructions` that define the same terms differently
- Fixing filter logic in example SQL but not updating the corresponding `sql_snippets.filters`
- Changing table structure but not updating `join_specs` or `sql_snippets` that reference old columns

**Before applying the PATCH**, verify that `text_instructions`, `example_question_sqls`, `sql_snippets`, `join_specs`, and `sql_functions` are all consistent with each other and with the current state of the underlying tables.

### Update API Reference

**Endpoint:** `PATCH /api/2.0/genie/spaces/{space_id}`

**Parameters:**
- `serialized_space`: Updated JSON configuration (required)
- `title`: New title (optional)
- `description`: New description (optional)

**Note:** You cannot change the `warehouse_id` or `parent_path` after creation. To use a different warehouse or location, create a new space.

### Validate Before Updating

**Reference script:** Run `scripts/validate_config.py` on the modified config **before** calling the PATCH API. This catches sorting errors, duplicate IDs, invalid formats, concatenated questions, malformed SQL, snippet table reference mismatches, and suggests parameterization opportunities.

### Test New or Modified SQL Queries

If you are adding or changing `example_question_sqls`, **execute each new/modified query** before calling the PATCH API. Join the `sql` array into a single string, run it via `spark.sql(query).show()`, and confirm it returns valid results. Do not apply updates with untested SQL.

### Python Example

**Reference script:** See `scripts/manage_space.py` (Part 2) for the complete update code. It shows how to add example SQL queries, sort all ID-based collections, and call the PATCH API.

**After updating the space**, display the link to the user:

```
https://<workspace-url>/genie/rooms/<space_id>
```


### Example SQL Query Format

When adding `example_question_sqls`, each example should include:

- `id`: Unique 32-character hex ID
- `question`: Array with a single natural language question string
- `sql`: Array of strings representing the SQL query (split by lines)

```json
{
  "id": "c3d4e5f6a7b80000000000000000000c",
  "question": ["What are total sales by product category?"],
  "sql": [
    "SELECT\n",
    "  p.category,\n",
    "  SUM(o.quantity * o.unit_price) as total_sales\n",
    "FROM sales.gold.orders o\n",
    "JOIN sales.gold.products p ON o.product_id = p.product_id\n",
    "GROUP BY p.category\n",
    "ORDER BY total_sales DESC"
  ]
}
```


## Step 6: Benchmark and Verify

After applying updates, recommend that the user runs benchmarks to verify improvements.

1. **If benchmarks exist:** Re-run all benchmarks (or the subset related to the changes) from the **Benchmarks** tab and compare accuracy to the previous run.
2. **If no benchmarks exist:** Recommend creating 10-20 benchmark questions covering the space's core use cases, with 2-4 phrasings each and SQL ground truth answers.
3. **Manual testing:** Ask the user to test the specific questions that were previously failing, using a **new chat** to avoid influence from prior conversation context.
4. **Clone for safe testing:** For significant changes, recommend cloning the space first, applying changes to the clone, and benchmarking there before updating production.

---

## Error Handling

### HTTP Status Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | BAD_REQUEST | Request is invalid. |
| 401 | UNAUTHORIZED | The request does not have valid authentication credentials for the operation. |
| 403 | PERMISSION_DENIED | Caller does not have permission to execute the specified operation. |
| 404 | FEATURE_DISABLED | If a given user/entity is trying to use a feature which has been disabled. |
| 500 | INTERNAL_ERROR | Internal error. |

### Common Error Scenarios

| Error | Likely Cause | Solution |
|-------|--------------|----------|
| 400 BAD_REQUEST - Invalid JSON | Invalid JSON in serialized_space | Validate JSON structure |
| 400 BAD_REQUEST - "data_sources.tables must be sorted by identifier" | Tables array not sorted alphabetically | Sort tables by identifier field |
| 400 BAD_REQUEST - "config.sample_questions must be sorted by id" | Sample questions not sorted alphabetically | Sort questions by id field |
| 400 BAD_REQUEST - Invalid ID format | IDs not 32-char hex | Use secrets.token_hex(16) for 32-char IDs |
| 400 BAD_REQUEST - Invalid parent path | Parent folder doesn't exist | Use existing folder or user home directory |
| 400 BAD_REQUEST - Invalid warehouse | Warehouse is not pro or serverless | Use a pro or serverless SQL warehouse |
| 401 UNAUTHORIZED | Missing or invalid authentication token | Check authentication credentials |
| 403 PERMISSION_DENIED | No access to warehouse or tables | Check permissions on resources |
| 404 FEATURE_DISABLED | Genie not enabled in workspace | Enable AI/BI Genie in workspace settings |
| 500 INTERNAL_ERROR | Server-side error | Retry the request or contact support |

## Troubleshooting Common Issues

If users report problems with their Genie space after creation, use this reference to diagnose and fix common issues.

### Misunderstood Business Jargon
**Symptom:** Genie misinterprets domain-specific terms (e.g., "year" should mean fiscal year starting in February).
**Fix:** Add text instructions that explicitly map business jargon to data concepts. For example: "When users refer to 'year', always use fiscal year. Fiscal year 26 (FY26) is February 1, 2026 through January 31, 2027."

### Incorrect Table or Column Usage
**Symptom:** Genie pulls data from the wrong table or column.
**Fix:**
- Verify that table/column descriptions match the terminology users use in their questions
- Add example SQL queries showing the correct tables and columns to use
- Hide unnecessary or overlapping columns in the Genie space UI
- Remove redundant tables that could cause ambiguity

### Filtering Errors (Wrong Values)
**Symptom:** `WHERE` clause filters on "California" instead of "CA", or similar value mismatches.
**Fix:** Ensure relevant columns have **format assistance** and **entity matching** enabled (Configure > Data > column > Advanced settings). Refresh prompt matching data if new values have been added to the column.

### Incorrect Joins
**Symptom:** Genie joins tables incorrectly or doesn't know how to join them.
**Fix:**
1. Define foreign key references in Unity Catalog
2. Define join relationships in the Genie space's knowledge store
3. Provide example SQL queries with correct joins
4. Pre-join tables into views as a last resort

### Metric Calculation Errors
**Symptom:** Metrics are calculated incorrectly or rolled up improperly.
**Fix:**
- Define metrics as **SQL expressions** in the knowledge store
- Provide example SQL queries computing each roll-up value
- For pre-aggregated tables, explain this in table comments and specify which aggregations are valid
- For very complex metrics, create views that pre-compute the aggregations

### Incorrect Time-Based Calculations
**Symptom:** Timezone or date conversions produce wrong results.
**Fix:** Add explicit text instructions for timezone handling:
- "Time zones in the tables are in `UTC`."
- "Convert all timezones using: `convert_timezone('UTC', 'America/Los_Angeles', <column>)`"
- "To reference _today_ for users in Los Angeles, use `date(convert_timezone('UTC', 'America/Los_Angeles', current_timestamp()))`"

### Genie Ignoring Instructions
**Symptom:** Genie doesn't follow provided instructions consistently.
**Fix:**
- Add example SQL queries that demonstrate correct usage (most effective)
- Hide irrelevant columns to reduce noise
- Simplify tables by creating focused views
- Review instructions for conflicts — remove irrelevant or contradictory ones
- Start a new chat to test (previous interactions influence responses within a conversation)

### Performance Issues / Timeouts
**Symptom:** Genie takes too long or times out during query generation.
**Fix:**
- Check query history for slow-running queries and optimize the generated SQL
- Use trusted assets (parameterized queries or UDFs) to encapsulate complex logic
- Reduce the length of example SQL queries
- Start a new chat if responses become consistently slow

### Token Limit Warning
**Symptom:** A warning appears about approaching the token limit, or messages can no longer be sent.
**Fix:**
- Remove unnecessary columns from tables (or hide them in the space)
- Streamline column descriptions — don't duplicate info already conveyed by column names
- Prune overlapping or redundant example SQL queries
- Simplify text instructions — avoid unnecessary words
