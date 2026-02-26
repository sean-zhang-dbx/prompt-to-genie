---
name: prompt-to-genie
description: "Guide users through creating and managing Databricks AI/BI Genie spaces (Genie rooms) using the Genie API and serialized_space JSON configuration. Covers the full lifecycle: gathering requirements, profiling Unity Catalog tables, configuring data sources with column_configs, defining sample questions, writing SQL expressions (sql_snippets - measures, filters, dimensions), example SQL queries, text instructions, join specs (join_specs), SQL functions, and benchmarks. Manages existing spaces by auditing, diagnosing issues, and optimizing configuration via the PATCH API. Use when the user mentions Genie space, Genie room, serialized_space, knowledge store, sql_snippets, join_specs, column_configs, example_question_sqls, text_instructions, sql_functions, Genie API, prompt matching, entity matching, format assistance, or wants to create, build, set up, configure, update, audit, troubleshoot, or optimize a Genie space."
---

# Create, Diagnose, and Optimize Genie Spaces

Guide users through creating new Databricks AI/BI Genie spaces or managing existing ones — auditing configuration, diagnosing issues, and optimizing for accuracy.

**Determine intent first:** If the user wants to create a new space, follow the **Create a New Space** workflow below. If they have an existing space they want to review, fix, or improve, follow the **Diagnose and Optimize an Existing Space** workflow in [references/diagnose_optimize_space.md](references/diagnose_optimize_space.md).

## Critical: Do Not Skip Ahead

**This is a conversational workflow, not a script.** Each step involves asking the user questions and waiting for their response before proceeding. **Never generate configuration or create the space until the user has explicitly reviewed and approved the plan.**

The most common mistake is rushing to build the space after getting table names. Instead, gather business context thoroughly — it is far easier to get the initial room right than to debug it afterward.

## Workflow Overview

### Create a New Space
1. **Gather Requirements** - Define purpose, audience, and scope (start small) — **STOP: wait for user**
2. **Identify & Profile Data Sources** - Select tables, inspect columns/values — **STOP: ask about business logic**
3. **Define Sample Questions** - Create starter questions for business users
4. **Configure Instructions** - Prioritize SQL expressions > example SQL > text instructions — **STOP: present plan for user review**
5. **Generate Configuration** - Build the serialized_space JSON (only after user approves)
6. **Create the Space** - Call the Genie API to create the space
7. **Test and Iterate** - Self-test, benchmark, gather feedback, and refine

### Diagnose and Optimize an Existing Space
See [references/diagnose_optimize_space.md](references/diagnose_optimize_space.md) for the full workflow: retrieve config, audit, diagnose issues, recommend optimizations, apply updates, and benchmark.

---

# Create a New Space

## Step 1: Gather Requirements

A well-defined Genie space should answer questions for a **specific topic and audience**, not general questions across various domains. Start by understanding the user's needs clearly.

Ask the user about:

- [ ] **Title**: What should this space be called? The title is displayed in the UI and helps users identify the space. (e.g., "Sales Analytics", "Customer Support Metrics")
- [ ] **Description**: A one-sentence summary of the space's purpose (shown in the space listing).
- [ ] **Purpose**: What specific business questions should this space answer? Be narrow and focused.
- [ ] **Audience**: Who will use this space? (analysts, executives, etc.) Ideally, a domain expert who understands both the data and the business insights should help define the space.
- [ ] **Data Domain**: What single area does the data cover? (sales, finance, operations, etc.)
- [ ] **Key metrics, filters, and dimensions**: What business terms do users frequently reference? (e.g., "total revenue", "active customer", "fiscal quarter") These will become SQL expressions.
- [ ] **General instructions / business logic**: Are there any domain-specific rules, conventions, or definitions that apply broadly? (e.g., "Fiscal year starts in February", "Revenue = quantity * unit_price", "Active customer means at least one order in the last 90 days", region codes like "AMER = Americas"). These become text instructions and inform all SQL expressions.
- [ ] **Scope**: Start small — aim for a minimal setup with essential tables and basic instructions. It's easier to add more later than to debug an overly complex space.

**Example prompt:**
> "What kind of questions do you want users to be able to ask in this Genie space? For example: sales analytics, customer insights, inventory tracking? Try to keep it focused on one topic — a narrowly scoped space gives more accurate answers. Also, what would you like to name this space?"

**Key principle:** Curating a Genie space is an iterative process. Plan to start small and refine based on real user feedback rather than aiming for perfection on the first pass.

> **STOP.** Do not proceed to Step 2 until the user has answered the questions above — including a **title and description** for the space. If their answers are vague (e.g., "just sales stuff"), ask follow-up questions to get specifics — which metrics matter most, what filters users will apply, what time granularity they need. If they haven't provided a title, ask for one now. The more context you gather now, the better the space will be.

## Step 2: Identify Data Sources

Determine which Unity Catalog tables to include. **Keep the dataset focused** — include only the tables necessary to answer the questions from Step 1.

- [ ] **Catalog name**: Which catalog contains the data?
- [ ] **Schema name**: Which schema?
- [ ] **Table names**: Which specific tables?

**Example prompt:**
> "Which Unity Catalog tables should this Genie space have access to? Please provide the full path (catalog.schema.table)."

### Data Source Best Practices

- **Aim for 5 or fewer tables.** The more focused your selection, the better Genie performs. Limit the number of columns in your included tables to what's actually relevant.
- **Maximum 25 tables per space.** If you need more, prejoin related tables into views or metric views before adding them to the space.
- **Prejoin and de-normalize when possible.** Use views or metric views to resolve column ambiguities and simplify complex relationships. Metric views are particularly effective because they pre-define metrics, dimensions, and aggregations.
- **Build on well-annotated tables.** Genie uses Unity Catalog column names and descriptions to generate responses. Clear column names and descriptions help produce high-quality answers. Advise users to add or review column descriptions in Unity Catalog before creating the space.
- **Hide irrelevant columns.** After adding tables, recommend that users hide any columns that might be confusing or unimportant for the space's purpose. This reduces ambiguity for Genie.

### Table Format

catalog.schema.table_name


**Tip:** If the user is unsure, help them explore their catalog:
```sql
SHOW TABLES IN catalog.schema;
```


### Validate Table Access

Before adding tables to the space, verify the user has access:
```sql
DESCRIBE TABLE catalog.schema.table_name;
```


If successful, the table is accessible and can be included in the Genie space.

### Check Column Quality

Review column names and descriptions to assess annotation quality:
```sql
DESCRIBE TABLE EXTENDED catalog.schema.table_name;
```


If column descriptions are missing or unclear, suggest the user add them in Unity Catalog first — this significantly improves Genie's response accuracy.

**Reference script:** See `scripts/discover_resources.py` (Part 2) for a comprehensive audit that checks table comments, column descriptions, column counts, foreign keys, and generates a Genie-readiness quality score with specific recommendations.

**Column-level configuration via API:** Set per-column metadata directly in the `serialized_space` using `column_configs` on each table. **Important: prompt matching (format assistance + entity matching) is only auto-enabled when tables are added via the UI. When creating spaces via the API, prompt matching is OFF by default.** You must explicitly include `column_configs` entries with `enable_format_assistance: true` and `enable_entity_matching: true` for every string/category column that users will filter on. Columns not listed in `column_configs` will not have prompt matching enabled. Entity matching requires format assistance — turning off format assistance automatically disables entity matching. Hide irrelevant columns with `exclude: true`. See `references/schema.md` → "Prompt matching overview" for limits and "Field Reference → data_sources" for all fields.

### Define Table Relationships

If foreign key references are not defined in Unity Catalog, Genie may not know how to join tables correctly. Recommend users:

1. **Define foreign keys in Unity Catalog** when possible (most reliable)
2. **Define join specs in the `serialized_space`** via the API (see format below)
3. **Define join relationships in the Genie space UI** (Configure > Knowledge store) — useful for complex join scenarios (self-joins, etc.) or when you can't modify the underlying tables
4. **Provide example SQL queries with correct joins** in `example_question_sqls` — effective fallback that also teaches Genie query patterns
5. **Pre-join tables into views** if none of the above work

### Build a Knowledge Store (Post-Creation, in UI)

After creating the space via the API, recommend that users build out the **knowledge store** in the Genie space UI. A knowledge store is a collection of curated semantic definitions scoped to the space:

- **Column metadata and synonyms** — custom descriptions and alternate names to reduce ambiguity
- **SQL expressions** — reusable definitions for metrics, filters, and dimensions
- **Join relationships** — explicit definitions of how tables relate
- **Prompt matching** (format assistance + entity matching) — helps Genie match user values to correct columns (e.g., "California" → "CA"). Auto-enabled when tables are added via the UI, but **NOT auto-enabled when creating via API**. After API creation, verify prompt matching is active in Configure > Data > [column] > Advanced settings.

These enhancements don't require write access to the underlying Unity Catalog tables — they're scoped to the Genie space only.

### Inspect Actual Data Before Writing SQL

Before generating sample questions, SQL expressions, or example SQL queries, **always inspect the actual data** in the tables. Do not assume column names or values based on table names alone.

```sql
-- Check what columns actually exist
DESCRIBE TABLE catalog.schema.table_name;

-- Check distinct values for key filter/category columns
SELECT DISTINCT column_name FROM catalog.schema.table_name LIMIT 20;

-- Check date ranges
SELECT MIN(date_col), MAX(date_col) FROM catalog.schema.table_name;
```

This prevents common errors:
- Referencing columns that don't exist
- Using wrong filter values
- Incorrect date assumptions (e.g., assuming fiscal Q1 = Jan-Mar when it's actually Feb-Apr)

**Always ask the user about domain-specific conventions** like fiscal calendar definitions, internal abbreviations, and product naming conventions before writing SQL.

> **STOP — Business Logic Checkpoint.** Before writing any SQL or generating configuration, pause and ask the user:
>
> *"Before I start building the space, I want to make sure I capture your business logic correctly. Here's what I see in the data: [summarize tables, key columns, sample values, date ranges]. A few questions:*
>
> 1. *Are there any specific business rules, metric definitions, or calculations I should know about? (e.g., how is 'revenue' calculated? what counts as an 'active' customer?)*
> 2. *Any terminology or abbreviations your team uses that differ from the column names? (e.g., 'AMER' means 'Americas', fiscal year starts April 1st)*
> 3. *Are there columns or values that should be excluded or treated specially?*
> 4. *Any common questions your team asks that require complex logic or multi-table joins?*"
>
> **Do not proceed until the user confirms or provides this context.** This is the most impactful checkpoint — missing business logic here leads to incorrect SQL expressions, wrong filter values, and inaccurate answers that are frustrating to debug after the space is created.

## Step 3: Define Sample Questions

Create 3-5 starter questions that demonstrate the space's capabilities:

- Questions should be business-focused, not technical
- Cover common use cases for the target audience
- Use natural language that business users would actually ask

**Good examples:**
- "What were total sales last quarter?"
- "Which products have the highest profit margin?"
- "Show me customer retention trends by region"

**Avoid:**
- "SELECT * FROM sales" (too technical)
- "Get data" (too vague)

## Step 4: Configure Instructions

Instructions help Genie accurately interpret business questions and generate correct SQL. **Prioritize SQL-based instructions over text instructions** — they are more precise and easier for Genie to apply consistently.

### Instruction Priority (Most to Least Effective)

1. **SQL Expressions** — for common business terms (metrics, filters, dimensions)
2. **Example SQL Queries** — for complex, multi-part, or hard-to-interpret questions
3. **Text Instructions** — for general guidance that doesn't fit structured SQL definitions

### 4a: SQL Expressions (Recommended First)

Use SQL expressions to define frequently used business terms as reusable definitions. These are the most efficient way to teach Genie your business logic. SQL expressions are stored in `instructions.sql_snippets` in the configuration.

**Three types of SQL expressions:**

- **Measures** (`sql_snippets.measures`): KPIs and aggregation metrics
  ```json
  {"id": "...", "alias": "total_revenue", "sql": ["SUM(orders.quantity * orders.unit_price)"]}
  ```
- **Filters** (`sql_snippets.filters`): Common filtering conditions (boolean expression — do **not** include the `WHERE` keyword)
  ```json
  {"id": "...", "display_name": "high value", "sql": ["orders.amount > 1000"]}
  ```
- **Dimensions** (`sql_snippets.expressions`): Attributes for grouping and analysis
  ```json
  {"id": "...", "alias": "order_year", "sql": ["YEAR(orders.order_date)"]}
  ```

> **Important:** The `sql` field in `sql_snippets` is a **string array** (`string[]`), the same format as `example_question_sqls[].sql`. Wrap the SQL fragment in an array (e.g., `["SUM(orders.amount)"]`). The API rejects plain strings. **All column references must be table-qualified** (`table_name.column_name`) — the Genie UI rejects bare column names.

**Good candidates for SQL expressions:**
- Metrics: gross margin, conversion rate, revenue
- Filters: "active customer", "recent order", "high-value account"
- Dimensions: fiscal quarter, product category groupings

**Ask the user:**
> "What key metrics, filters, or grouping dimensions do your users frequently reference? For example: 'total revenue' (measure), 'high-value order' (filter), 'fiscal quarter' (dimension). I'll define these as SQL expressions so Genie handles them accurately."

If the user isn't sure, infer SQL expressions from the table metadata — look at column names and types to suggest common measures (SUM, AVG on numeric columns), filters (status/flag columns), and dimensions (date parts, category columns).

**Important:** Always include SQL expressions in the `instructions.sql_snippets` section of the config. Do not just describe them — they must be in the JSON to take effect.

### 4b: Example SQL Queries (Recommended for Complex Questions)

Use complete example SQL queries for hard-to-interpret, multi-part, or complex questions. These show Genie how to handle intricate query patterns and multi-step logic. Queries can be **static** or **parameterized**.

**Good candidates for example SQL queries:**
- Questions requiring complex joins across multiple tables
- Multi-step calculations (e.g., "For customers who joined recently, what products are doing best?")
- Domain-specific aggregations or breakdowns (e.g., "breakdown my team's performance")

**Use one question per SQL entry.** Each example SQL query should map to exactly one natural language question. If you want to cover multiple phrasings of the same question, create separate entries — each with its own question string and the same SQL.

**Critical formatting rule for `sql`:** Each SQL clause should be a **separate string element** in the array with `\n` at the end. Never concatenate SQL clauses into one string.

```json
{
  "question": ["What are total sales by product category?"],
  "sql": [
    "SELECT\n",
    "  p.category,\n",
    "  SUM(o.quantity * o.unit_price) as total_sales\n",
    "FROM catalog.schema.orders o\n",
    "JOIN catalog.schema.products p ON o.product_id = p.product_id\n",
    "GROUP BY p.category\n",
    "ORDER BY total_sales DESC"
  ]
}
```


#### Parameterized Queries

Add parameters to example SQL using the `:parameter_name` syntax. Parameterized queries become **trusted assets** — when Genie uses them, the response is labeled **Trusted**, giving users extra confidence in accuracy. Users can edit parameter values and rerun the query.

**Example:**
```sql
-- Return current pipeline by region for a given forecast category
SELECT
  a.region__c AS `Region`,
  SUM(o.amount) AS `Open Pipeline`
FROM sales.crm.opportunity o
JOIN sales.crm.accounts a ON o.accountid = a.id
WHERE
  o.forecastcategory = :forecast_category AND
  o.stagename NOT ILIKE '%closed%'
GROUP BY ALL;
```


**Parameter types:** String (default), Date, Date and Time, Numeric (Decimal or Integer).

**When to use parameterized vs. static queries:**
- Use **parameterized** queries for recurring questions where users specify different filter values (e.g., by region, by quarter, by product). These produce **trusted** responses.
- Use **static** queries for questions that don't vary, or to teach Genie general query patterns it can learn from.


### 4c: Text Instructions (For General Guidance)

Reserve text instructions for context that doesn't fit SQL definitions. Keep them concise and specific — too many instructions can reduce effectiveness.

**Good text instructions:**
- "Active customer" means a customer with at least one order in the last 90 days
- Revenue should always be calculated as quantity * unit_price * (1 - discount)
- Fiscal year starts April 1st
- All monetary values are in USD unless otherwise specified

**Avoid vague instructions.** Instead of "Ask clarification questions when asked about sales," write:
> "When users ask about sales metrics without specifying product name or sales channel, ask: 'To proceed with sales analysis, please specify your product name and sales channel.'"

**Important:** Ensure consistency across all instruction types. For example, if text instructions specify rounding decimals to two digits, example SQL queries must also round to two digits.

### 4d: Clarification Question Instructions (Optional)

You can instruct Genie to ask clarification questions when user prompts are ambiguous. Structure these instructions with:

- **Trigger condition**: "When users ask about X topic..."
- **Missing details**: "...but don't include Y details..."
- **Required action**: "...you must ask a clarification question first..."
- **Example question**: "Please specify the time range and region."

**Example:**
> "When users ask about sales performance breakdown but don't include time range, sales channel, or which KPIs in their prompt, you must ask a clarification question first. For example: 'Please specify the time range and sales channel you are looking for.'"

Add clarification instructions at the end of your text instructions to help Genie prioritize this behavior.

### 4e: Summary Customization (Optional)

You can customize how Genie generates natural language summaries alongside query results. Add a dedicated section at the end of text instructions with the heading **"Instructions you must follow when providing summaries"**.

**Example:**
> Instructions you must follow when providing summaries:
> - Cite the table and column names used in your analysis
> - Use bullet points to structure multi-part summaries
> - Include the date range covered in the results

**Note:** Only text instructions affect summary generation. SQL expressions and example SQL queries do not influence summaries.

### 4f: Trusted Assets — SQL Functions (Advanced)

For questions involving complex logic that can't be captured with a static or parameterized query, you can register **Unity Catalog SQL functions (UDFs)** as trusted assets. Genie calls these functions with user-supplied parameters, and responses are labeled **Trusted**.

**When to use SQL functions:**
- Logic is too complex for a single SQL query
- You want to encapsulate business logic that shouldn't be modified
- The same function can serve multiple Genie spaces

**Example — creating a UDF for pipeline analysis:**
```sql
CREATE OR REPLACE FUNCTION catalog.schema.open_opps_in_region (
  regions ARRAY<STRING>
  COMMENT 'List of regions. Example: ["APAC", "EMEA"]' DEFAULT NULL
) RETURNS TABLE
COMMENT 'Returns all open pipeline opportunities, optionally filtered by region.
Example questions: "What is the pipeline for APAC?", "Open opportunities in EMEA"'
RETURN
  SELECT
    o.id AS `OppId`,
    a.region__c AS `Region`,
    o.name AS `Opportunity Name`,
    o.amount AS `Opp Amount`
  FROM catalog.schema.opportunity o
  JOIN catalog.schema.accounts a ON o.accountid = a.id
  WHERE o.forecastcategory = 'Pipeline'
    AND o.stagename NOT LIKE '%closed%'
    AND (
      isnull(open_opps_in_region.regions)
      OR array_contains(open_opps_in_region.regions, region__c)
    );
```


**Tips for writing UDFs:**
- **Include detailed function comments** — they tell Genie when to invoke the function
- **Include parameter comments with examples** — e.g., `'List of regions. Values: ["AF", "EU", "NA"]'`
- **Use `DEFAULT NULL` for optional parameters** — and explicitly check for `NULL` in the `WHERE` clause: `WHERE (isnull(min_date) OR created_date >= min_date)`
- **Specify format in comments** — e.g., `'minimum date in yyyy-mm-dd format'`
- **Store functions in a dedicated schema** for easier permission management

**Permissions:** Users need `EXECUTE` permission on the function and `CAN USE` on the containing catalog/schema.

### Instruction Limits

A Genie space supports up to **100 instructions total**, counted as:
- Each example SQL query = 1 instruction
- Each SQL function = 1 instruction
- The entire text instructions block = 1 instruction

Keep this budget in mind when adding instructions — prioritize quality over quantity.

## Step 4.5: Discover Available Resources

If the user doesn't know their warehouse ID or workspace URL, help them discover available resources.

**Reference script:** See `scripts/discover_resources.py` for the complete code. Part 1 lists all eligible SQL warehouses — pro and serverless — (name, ID, type, state, size) and prints the workspace URL. Part 2 audits table metadata quality for Genie-readiness.

**Important:** Genie spaces require a **pro or serverless** SQL warehouse (serverless recommended for performance).

> **STOP — Present the Plan for Review.** Before generating any JSON, present a summary of everything you plan to include in the space. Format it clearly so the user can review and approve:
>
> *"Here's what I plan to include in your Genie space. Please review and let me know if anything needs to change:*
>
> - *Title: [space name]*
> - *Description: [one-sentence summary]*
> - *Warehouse: [ID]*
> - *Tables: [list tables]*
> - *Sample questions: [list 3-5 questions]*
> - *SQL expressions: [list measures, filters, dimensions with their definitions]*
> - *Example SQL queries: [list question + brief description of each]*
> - *Text instructions: [summarize key rules]*
> - *Join specs: [list table relationships]*"
>
> **Only proceed to generate the configuration after the user confirms.** This is your last checkpoint before building — any corrections here are easy, but corrections after creation require the diagnose and optimize workflow.

## Step 5: Generate Configuration

Build the `serialized_space` JSON using the schema and examples in [references/schema.md](references/schema.md). Include only sections relevant to the user's space.

**Critical formatting rules** (these cause API rejection if wrong):
- `version`: **Required**. Use `2` for new spaces
- All IDs: exactly 32 lowercase hex characters — generate with `secrets.token_hex(16)`
- All arrays with `id` fields must be **sorted alphabetically by `id`**. Tables sorted by `identifier`.
- `sql` fields are **string arrays** — each SQL clause is a separate element with `\n`: `["SELECT\n", "  col\n", "FROM table"]`
- `sql_snippets` require **table-qualified column references** (`table_name.column`) — bare column names are rejected by the UI
- Filters must **NOT** include the `WHERE` keyword — only the boolean condition
- `join_specs.sql` requires **two elements**: (1) backtick-quoted join condition, (2) `"--rt=FROM_RELATIONSHIP_TYPE_...--"` annotation
- `text_instructions.content` elements must end with `\n` — the API concatenates without separators
- Include only what's needed — omit sections that don't apply


## Step 6: Create the Space

### Required Parameters
 Parameter | Description |
-----------|-------------|
 `serialized_space` | JSON string from Step 5 |
 `warehouse_id` | Pro or serverless SQL warehouse ID (required) |
 `parent_path` | Workspace folder path (e.g., `/Users/username/genie`) |
 `title` | Display name for the space |
 `description` | Brief description of the space's purpose |

### API Call

POST https://<workspace-url>/api/2.0/genie/spaces

{
  "serialized_space": "<JSON string>",
  "warehouse_id": "<serverless-warehouse-id>",
  "parent_path": "/Users/<username>/genie_spaces",
  "title": "Sales Analytics",
  "description": "Ask questions about sales performance and trends"
}


### Validate Before Creating

**Reference script:** Run `scripts/validate_config.py` on the generated config **before** calling the API. It checks:
- **Errors**: ID format, sorting, uniqueness, required fields, limits, concatenated questions, malformed SQL, `WHERE` keyword in filters, snippet table references not in `data_sources`
- **Warnings**: Table count, instruction budget, formatting issues, bare (non-table-qualified) column names in snippets
- **Parameterization suggestions**: Detects similar queries that could be consolidated into parameterized queries, and flags hardcoded filter values that should use `:parameter` syntax

The validator cross-references table names in `sql_snippets` against `data_sources.tables` — if a snippet references a table that isn't in the space (e.g., typo `orderz.amount` instead of `orders.amount`), it flags an error. This catches the most common snippet mistakes without needing to execute queries.

### Test Example SQL Queries

**Before calling the API**, execute every example SQL query to verify it runs successfully. Do not create the space with untested SQL.

For each `example_question_sqls` entry in the configuration:

1. **Join the `sql` array** into a single string: `query = "".join(sql_parts)`
2. **Execute it**: `spark.sql(query).show()`
3. **Check the result:**
   - If it **errors** (syntax error, missing table/column, permission denied) — fix the SQL before proceeding
   - If it **returns 0 rows** — verify the table has data and that any filter values or date ranges are correct
   - If it **succeeds** — mark as passed
4. **Report a summary** to the user: "X/Y example SQL queries passed"

**Only proceed to create the space after all queries pass.** If any query fails, work with the user to fix the SQL first.

### Python Example

Run this in a Databricks notebook cell (adapt values to match the user's space):

```python
import json
from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# serialized_space JSON from Step 5
serialized_space = { ... }  # The full JSON built in Step 5

response = w.api_client.do(
    method="POST",
    path="/api/2.0/genie/spaces",
    body={
        "title": "Sales Analytics",
        "description": "Ask questions about sales performance and trends",
        "warehouse_id": "abc123def456",          # From scripts/discover_resources.py
        "parent_path": "/Users/username/genie",   # Workspace folder for the space
        "serialized_space": json.dumps(serialized_space),
    },
)

space_id = response["space_id"]
host = w.config.host.rstrip("/")
print(f"Space created! Open it here:\n{host}/genie/rooms/{space_id}")
```

For the full template with column configs and all sections, see `scripts/create_space.py`.

**After creating the space**, always display a clickable link to the user using this format:

```
https://<workspace-url>/genie/rooms/<space_id>
```

Get the workspace URL from `w.config.host` (strip trailing slash) and the space ID from the API response. Example:
`https://adb-984752964297111.11.azuredatabricks.net/genie/rooms/01f0d5be61091b6ea75a6e8438c3bce2`

> **Important post-creation step:** Prompt matching (format assistance + entity matching) is **not auto-enabled when creating via the API**. After the space is created, remind the user:
>
> *"Your space is live! One important step: prompt matching (which helps Genie match user terms like 'California' to actual values like 'CA') is only auto-enabled when tables are added via the UI. Since we created this space via the API, please open the space, go to Configure > Data, and verify that Format assistance and Entity matching are enabled for your key filter columns (under each column's Advanced settings). The `column_configs` I included cover [list columns], but any other string/category columns may need to be enabled manually."*


**Authentication Notes:**
- All scripts use `WorkspaceClient()` from the Databricks SDK (`databricks-sdk`), which auto-authenticates in notebook context
- API calls use `w.api_client.do()` for Genie endpoints and typed methods (e.g., `w.warehouses.list()`) where available
- For scripts outside notebooks, `WorkspaceClient` supports Personal Access Tokens, OAuth, and other authentication methods via environment variables or `~/.databrickscfg`

**Compute and Sharing Notes:**
- Genie spaces require a **pro or serverless** SQL warehouse (serverless recommended for performance)
- The creating user's compute credentials are **embedded** into the space and used for all queries by all users
- End users have their own **data credentials** applied, so they only see data they're authorized to access
- Users need the **Databricks SQL** workspace entitlement and `SELECT` on included tables to use the space
- Each workspace supports up to **20 questions/minute** across all Genie spaces (UI), or **5 questions/minute** via API free tier
- Each space supports up to **10,000 conversations**, each with up to **10,000 messages**

## Step 7: Test and Iterate

After creating the space, **the curator should be the first user**. Testing and iterating is essential — a Genie space gets better over time with real-world feedback.

### Self-Testing

1. **Ask questions** — Start with the sample questions, then try variations and different phrasings.
2. **Examine the SQL** — Click **Show code** on any response to review the generated SQL. Check that it uses the correct tables, joins, filters, and calculations.
3. **Fix misinterpretations** — If Genie misinterprets the data, business jargon, or question intent:
   - Add example SQL queries for the questions Genie got wrong (click **Add as instruction** on a corrected response)
   - Add or refine text instructions to clarify terminology
   - Add column metadata, synonyms, or example values in the knowledge store to reduce ambiguity
   - Check that relevant columns have **format assistance** and **entity matching** enabled (Configure > Data > column > Advanced settings) to correct value/spelling mismatches
4. **Start a new chat** when testing new instructions — previous interactions can influence responses within a conversation.

### Benchmarks

Use **benchmarks** to systematically evaluate accuracy as you refine the space. Each space supports up to **500 benchmark questions**.

**Creating benchmarks:**
- Write benchmark questions that reflect realistic phrasings from real users
- Include a **SQL answer** (ground truth) for each question — only questions with SQL answers can be auto-scored
- Add **2-4 alternate phrasings** of the same question with the same SQL answer to test Genie's robustness
- Click **Add as benchmark** on any response in the chat to add it directly

**Running benchmarks:**
- Run all benchmarks or a selected subset from the **Benchmarks** tab
- Each question runs as a new conversation (no prior context)
- Genie generates SQL and the results are compared against your ground truth

**Interpreting ratings:**

| Rating | Condition |
|--------|-----------|
| **Good** | Generated SQL or result set matches ground truth (including same data in different sort order, or numeric values matching to 4 significant digits) |
| **Bad** | Empty result set, error, extra columns, or different single-cell result |
| **Manual review** | Genie couldn't assess, or no SQL answer was provided |

**Iterate:** After each benchmark run, review low-scoring questions, fix the root cause (add example SQL, refine instructions, improve metadata), then re-run to measure improvement.

### User Testing

Once you're satisfied with self-testing, recruit a business user:

- Set expectations that their job is to help **refine** the space
- Ask them to focus on the specific topic the space is designed for
- Encourage them to **upvote or downvote** responses using the built-in feedback mechanism
- If they get an incorrect response, they can click **Fix it** to flag issues, or **Request review** to flag for the curator
- Collect unresolved questions and use them to add more instructions or example SQL queries

### Ongoing Monitoring

- Use the **Monitoring tab** to see all questions asked across all users, filterable by time, rating, user, or status
- Look for patterns in questions Genie struggles with — these are candidates for new example SQL queries or instructions
- Click any question to see the full chat thread and response details
- Use audit logs to track Genie space feedback and review requests
- Treat the space as a living artifact — small updates based on real usage significantly improve results over time
- Consider **cloning** the space to test significant changes in isolation before applying them to the production space

## Complete Example Conversation

This example demonstrates the multi-turn, pause-heavy pattern. Notice the agent does **not** skip ahead — it asks questions, waits, profiles data, asks about business logic, presents a plan, and only builds after approval.

**User:** "I want to create a Genie space for our sales team"

**Agent:** "I can help you create a Genie space for sales analytics! Before I start building anything, I need to understand your requirements. A few questions:

1. **Title:** What would you like to name this space? (e.g., 'Sales Analytics', 'Revenue Dashboard')
2. **Purpose:** What specific business questions should users be able to ask? (e.g., revenue analysis, product performance, regional comparisons)
3. **Audience:** Who will use this space? (e.g., sales managers, executives, analysts)
4. **Key metrics:** What are the most important metrics your team tracks? (e.g., total revenue, win rate, average deal size)
5. **Common filters:** What do users typically filter by? (e.g., region, product category, time period)
6. **Data:** Which Unity Catalog tables contain your sales data?"

*(Agent waits for user response)*

**User:** "Call it 'Sales Analytics'. Sales managers will use it. They need to analyze revenue by product and region, and track deal pipeline. Key metrics are total revenue, average order value, and conversion rate. They filter by region and product category. The data is in `analytics.sales.orders` and `analytics.sales.products`."

**Agent:** "Great, let me inspect those tables to understand the data structure..."

*(Agent runs DESCRIBE TABLE and SELECT DISTINCT on key columns, then presents findings)*

**Agent:** "Here's what I found in your data:
- `analytics.sales.orders`: 12 columns — including `region` (values: AMER, EMEA, APJ, LATAM), `order_date` (range: 2023-01-01 to 2025-12-31), `amount`, `quantity`, `status` (values: open, closed-won, closed-lost)
- `analytics.sales.products`: 8 columns — including `category` (values: Software, Hardware, Services), `product_name`, `unit_price`

**Before I start building, a few questions about your business logic:**
1. How is 'revenue' calculated? Is it `amount`, or `quantity * unit_price`, or something else?
2. How is 'conversion rate' defined? (e.g., closed-won / total opportunities?)
3. Does your team use a fiscal calendar? If so, when does the fiscal year start?
4. Any abbreviations or terminology I should know? (e.g., does 'AMER' mean 'Americas'?)
5. Should I exclude any columns like `etl_timestamp` or internal IDs?"

*(Agent waits for user response)*

**User:** "Revenue = quantity * unit_price. Conversion rate is closed-won divided by all closed deals. Fiscal year starts April 1st. Yes, AMER = Americas, EMEA = Europe/Middle East/Africa, APJ = Asia Pacific/Japan, LATAM = Latin America. Hide `etl_timestamp` and `internal_batch_id`."

**Agent:** "Thanks — that's really helpful. Here's what I plan to include in your **Sales Analytics** space. Please review:

**Title:** Sales Analytics
**Description:** Analyze sales revenue, pipeline, and performance by product and region
**Tables:** `analytics.sales.orders`, `analytics.sales.products`
**Sample questions:**
- What were total sales last quarter?
- Show me revenue by product category and region
- Which products have the highest average order value?

**SQL expressions:**
- Measure: `total_revenue` = `SUM(quantity * unit_price)`
- Measure: `avg_order_value` = `AVG(quantity * unit_price)`
- Filter: `closed won` = `status = 'closed-won'`
- Dimension: `fiscal_quarter` = `CASE WHEN MONTH(order_date) >= 4 THEN ... END`

**Example SQL queries:**
- 'What is the conversion rate by region?' — with the closed-won / all-closed logic
- 'Show me revenue trend by fiscal quarter' — using the April fiscal year

**Text instructions:**
- Revenue = quantity * unit_price
- Fiscal year starts April 1st
- Region codes: AMER = Americas, EMEA = Europe/Middle East/Africa, APJ = Asia Pacific/Japan, LATAM = Latin America

**Join specs:** orders.product_id = products.product_id (MANY_TO_ONE)
**Hidden columns:** etl_timestamp, internal_batch_id

Does this look right, or would you like to change anything?"

*(Agent waits for user approval)*

**User:** "Looks good! Use warehouse `abc123`, put it in `/Users/sean/genie_spaces`"

**Agent:** *(now generates the configuration, validates, tests SQL, and creates the space)*

## Validation Checklist

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

## Error Handling, Troubleshooting, and Diagnosing Existing Spaces

For error handling (HTTP status codes, common error scenarios), troubleshooting common issues (misunderstood jargon, incorrect joins, filtering errors, etc.), and the full workflow for diagnosing and optimizing existing spaces, see [references/diagnose_optimize_space.md](references/diagnose_optimize_space.md).

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
