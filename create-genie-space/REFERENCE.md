# Genie Space Reference

Reference material for the `create-genie-space` skill. This file contains JSON schemas, error codes, troubleshooting guides, and UI walkthrough templates. The main workflow is in `SKILL.md`.

---

## serialized_space JSON Schema

Complete structure for the `serialized_space` configuration. Include only sections relevant to the user's space.

```json
{
  "version": 2,
  "config": {
    "sample_questions": [
      {
        "id": "a1b2c3d4e5f60000000000000000000a",
        "question": ["What were total sales last month?"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {"identifier": "catalog.schema.table1", "description": ["Description of table1"]},
      {"identifier": "catalog.schema.table2"}
    ],
    "metric_views": [
      {"identifier": "catalog.schema.metric_view1", "description": ["Revenue metrics"]}
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "b2c3d4e5f6a70000000000000000000b",
        "content": ["General instructions for the space."]
      }
    ],
    "example_question_sqls": [
      {
        "id": "c3d4e5f6a7b80000000000000000000c",
        "question": ["Show top 10 customers by revenue"],
        "sql": ["SELECT\n", "  customer_name,\n", "  SUM(amount) as total\n", "FROM catalog.schema.orders\n", "GROUP BY customer_name\n", "ORDER BY total DESC\n", "LIMIT 10"]
      }
    ],
    "sql_functions": [
      {
        "id": "d4e5f6a7b8c90000000000000000000d",
        "identifier": "catalog.schema.fiscal_quarter"
      }
    ],
    "join_specs": [
      {
        "id": "e5f6a7b8c9d00000000000000000000e",
        "left": {"identifier": "catalog.schema.orders"},
        "right": {"identifier": "catalog.schema.customers"},
        "sql": ["orders.customer_id = customers.customer_id"]
      }
    ],
    "sql_snippets": {
      "filters": [
        {"id": "f6a7b8c9d0e10000000000000000000f", "sql": ["amount > 1000"], "display_name": "high value"}
      ],
      "expressions": [
        {"id": "a7b8c9d0e1f20000000000000000000a", "alias": "order_year", "sql": ["YEAR(order_date)"]}
      ],
      "measures": [
        {"id": "b8c9d0e1f2a30000000000000000000b", "alias": "total_revenue", "sql": ["SUM(amount)"]}
      ]
    }
  },
  "benchmarks": {
    "questions": [
      {
        "id": "c9d0e1f2a3b40000000000000000000c",
        "question": ["What is average order value?"],
        "answer": [{"format": "SQL", "content": ["SELECT AVG(amount) FROM catalog.schema.orders"]}]
      }
    ]
  }
}
```

### Field Reference

| Section | Field | Description |
|---------|-------|-------------|
| `config.sample_questions[]` | `id`, `question` | Starter questions shown to users. One question per entry. |
| `data_sources.tables[]` | `identifier`, `description` (optional) | Unity Catalog tables. `description` is a space-scoped override (array of strings). |
| `data_sources.metric_views[]` | `identifier`, `description` (optional) | Metric views with pre-defined metrics, dimensions, and aggregations. |
| `instructions.text_instructions[]` | `id`, `content` | General guidance (max 1 per space). `content` is an array of strings. |
| `instructions.example_question_sqls[]` | `id`, `question`, `sql` | Example SQL queries. One question per entry. `sql` is an array of line strings with `\n`. |
| `instructions.sql_functions[]` | `id`, `identifier` | Unity Catalog UDFs referenced by their full path. |
| `instructions.join_specs[]` | `id`, `left`, `right`, `sql` | Join relationships between tables. `sql` is the join condition. |
| `instructions.sql_snippets.filters[]` | `id`, `sql`, `display_name` | Filter definitions (boolean conditions). |
| `instructions.sql_snippets.expressions[]` | `id`, `sql`, `alias` | Dimension definitions (grouping attributes). |
| `instructions.sql_snippets.measures[]` | `id`, `sql`, `alias` | Measure definitions (aggregation KPIs). |
| `benchmarks.questions[]` | `id`, `question`, `answer` | Benchmark questions with SQL ground truth. |

### Important Notes

- `version`: **Required**. Use `2` for new spaces
- `question`: Must be an array with a **single question string** per entry
- `sql` (in `example_question_sqls`): Must be an array of strings. **Each SQL clause should be a separate element** with `\n` at the end:
  - Correct: `["SELECT\n", "  col1,\n", "  col2\n", "FROM table\n", "WHERE col1 > 0"]`
  - Wrong: `["SELECT col1, col2FROM tableWHERE col1 > 0"]`
- **ID Format**: All IDs must be exactly 32 lowercase hexadecimal characters (no hyphens)
- **Sorting**: All arrays of objects with `id` fields must be sorted alphabetically by `id`. Tables must be sorted by `identifier`.
- **Include only what's needed**: Omit sections that don't apply (e.g., skip `metric_views` if none, skip `benchmarks` if not creating them yet)

### ID Generation

Generate unique 32-character hexadecimal IDs (UUID format without hyphens):

```python
import secrets
question_id = secrets.token_hex(16)  # Generates 32-char hex string
```

**Important ID Requirements:**
- Must be exactly 32 characters long
- Must be lowercase hexadecimal (0-9, a-f)
- No hyphens or other separators
- Must be unique within their collection

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
| 400 BAD_REQUEST - Invalid warehouse | Warehouse is not serverless | Use a serverless SQL warehouse |
| 401 UNAUTHORIZED | Missing or invalid authentication token | Check authentication credentials |
| 403 PERMISSION_DENIED | No access to warehouse or tables | Check permissions on resources |
| 404 FEATURE_DISABLED | Genie not enabled in workspace | Enable AI/BI Genie in workspace settings |
| 500 INTERNAL_ERROR | Server-side error | Retry the request or contact support |

---

## Troubleshooting Common Issues

Use this reference to diagnose and fix common problems with Genie spaces.

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

**Fix:** Ensure relevant columns have **Example values** and **Value dictionaries** enabled in the knowledge store. Refresh values if new data has been added.

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

---

## UI Walkthrough Templates

Step-by-step instructions for common changes in the Genie space UI. Use these when guiding users through Mode B (Guided Walkthrough).

### Enable Prompt Matching for a Column

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table containing the `{column_name}` column
3. Click on the column → toggle **Prompt matching** to ON
4. **Verify:** Ask a question using a natural-language value (e.g., "North America" instead of "AMER") and confirm Genie maps it correctly

### Hide an Irrelevant Column

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table containing the `{column_name}` column
3. Toggle the column's visibility to **hidden**
4. **Verify:** The column should no longer appear in Genie's generated SQL

### Add Column Synonyms / Descriptions

1. Open your Genie space → click the **gear icon** (settings)
2. Find the table and column you want to annotate
3. Click on the column → add a **description** or **synonyms**
4. **Verify:** Ask a question using the synonym and confirm Genie resolves it correctly

### Add a Benchmark Question

1. Open your Genie space → go to the **Benchmarks** tab
2. Click **Add benchmark** → enter the question text
3. Add a SQL ground truth answer
4. Optionally add 2-4 alternate phrasings with the same SQL answer
5. **Verify:** Run the benchmark and check the rating

### Add Example Values / Value Dictionaries

1. Open your Genie space → click the **gear icon** (settings)
2. Find the column → click **Example values**
3. Add common values users might reference, including variations and abbreviations
4. **Verify:** Ask a question using an abbreviation and confirm Genie matches it

### Add a SQL Expression in the Knowledge Store

1. Open your Genie space → click the **gear icon** (settings)
2. Go to **SQL expressions** → click **Add**
3. Choose the type: Measure, Filter, or Dimension
4. Enter the alias/display name and SQL definition
5. **Verify:** Ask a question referencing the expression name and confirm Genie uses it

---

## Additional Resources

- [Set Up and Manage a Genie Space](https://docs.databricks.com/aws/en/genie/set-up)
- [Curate an Effective Genie Space — Best Practices](https://docs.databricks.com/aws/en/genie/best-practices)
- [Use Parameters in SQL Queries](https://docs.databricks.com/aws/en/genie/query-params)
- [Use Trusted Assets in Genie Spaces](https://docs.databricks.com/aws/en/genie/trusted-assets)
- [Use Benchmarks in a Genie Space](https://docs.databricks.com/aws/en/genie/benchmarks)
- [Troubleshoot Genie Spaces](https://docs.databricks.com/aws/en/genie/troubleshooting)
- [Genie API Reference](https://docs.databricks.com/api/workspace/genie)
- [Create Genie Space API](https://docs.databricks.com/api/workspace/genie/createspace)
