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

## Contents

- **Create a New Space** (Steps 1-7) — below
- **Diagnose and Optimize an Existing Space** — [references/diagnose_optimize_space.md](references/diagnose_optimize_space.md)
- **JSON Schema Reference** — [references/schema.md](references/schema.md)
- **UI Walkthroughs** — [references/ui_walkthroughs.md](references/ui_walkthroughs.md)
- **Validation Checklist** — [references/validation_checklist.md](references/validation_checklist.md)
- **Example Conversation** — [references/example_conversation.md](references/example_conversation.md)

## Workflow Overview

### Create a New Space

Copy this checklist and track progress:

- [ ] Step 1: Requirements gathered — **STOP: wait for user**
- [ ] Step 2: Tables profiled — **STOP: ask about business logic**
- [ ] Step 3: Sample questions defined
- [ ] Step 4: Instructions configured (4a-4g) — **STOP: present plan for user review**
- [ ] Step 5: Config generated and validated
- [ ] Step 6: Space created
- [ ] Step 7: Benchmarks run, feedback gathered

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
- **Never hide columns without explicit approval.** After profiling tables, you may suggest columns that look irrelevant (e.g., ETL timestamps, internal IDs), but you **must ask the user and get confirmation** before excluding anything. Do not set `exclude: true` on any column that the user has not explicitly approved for hiding.

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

**Column-level configuration via API:** Set per-column metadata directly in the `serialized_space` using `column_configs` on each table. **Important: prompt matching (format assistance + entity matching) is only auto-enabled when tables are added via the UI. When creating spaces via the API, prompt matching is OFF by default.** You must explicitly include `column_configs` entries with `enable_format_assistance: true` and `enable_entity_matching: true` for every string/category column that users will filter on. Columns not listed in `column_configs` will not have prompt matching enabled. Entity matching requires format assistance — turning off format assistance automatically disables entity matching. To hide columns, set `exclude: true` — but **only after confirming with the user** which columns to exclude. See `references/schema.md` → "Prompt matching overview" for limits and "Field Reference → data_sources" for all fields.

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

Add parameters using `:parameter_name` syntax. Parameterized queries become **trusted assets** (labeled "Trusted" in responses). Use for recurring questions where users specify different filter values (e.g., by region, by quarter). Parameter types: String (default), Date, Date and Time, Numeric. Use **static** queries for questions that don't vary or to teach Genie general patterns.


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

Register **Unity Catalog SQL functions (UDFs)** as trusted assets for logic too complex for a single query. Genie calls these functions with user-supplied parameters, and responses are labeled **Trusted**. Use when the same function can serve multiple spaces or you want to encapsulate business logic that shouldn't be modified.

**Tips for writing UDFs:**
- **Include detailed function and parameter comments** — these tell Genie when to invoke the function and what values to pass (e.g., `COMMENT 'List of regions. Values: ["AF", "EU", "NA"]'`)
- **Use `DEFAULT NULL` for optional parameters** — check for `NULL` in the `WHERE` clause: `WHERE (isnull(min_date) OR created_date >= min_date)`
- **Store functions in a dedicated schema** for easier permission management

**Permissions:** Users need `EXECUTE` on the function and `CAN USE` on the containing catalog/schema.

### Instruction Limits

A Genie space supports up to **100 instructions total**, counted as:
- Each example SQL query = 1 instruction
- Each SQL function = 1 instruction
- The entire text instructions block = 1 instruction

Keep this budget in mind when adding instructions — prioritize quality over quantity.

### 4g: Plan Benchmarks (Required)

Every new space **must** include benchmarks in its initial configuration. Benchmarks are organized into two categories:

**Core benchmarks** (high expected accuracy):
- For each **example SQL query** from Step 4b, include the **original question** as a smoke test plus **2-3 alternate phrasings**.
- Ground truth SQL = the **exact same SQL** from the corresponding `example_question_sqls` entry. Do not rewrite or adapt it — reuse it verbatim so the ground truth matches the pattern Genie learned.

**Stretch benchmarks** (lower expected accuracy):
- New questions covering **sample questions** or other use cases that have no corresponding example SQL.
- Ground truth SQL = independently written, but following the same conventions as the example SQL (same rounding, aliases, join patterns).

**Benchmark questions must be unambiguous.** If a question could reasonably be answered by multiple different SQL queries, make it more specific. Include the exact metric, grouping, count, and scope so the ground truth SQL is the only reasonable interpretation. Bad: "Show me the most lethal cancers" (how many? what metric?). Good: "What are the top 5 cancer types ranked by average mortality rate?"

**Ground truth SQL must be minimal.** Only include columns and clauses directly implied by the question. Do not add helpful extras — if the question asks about mortality rate, do not include survival rate or death counts in the SELECT. Extra columns cause benchmark failures because Genie may return different "helpful" columns or none at all.

**Target:** 10-20 total benchmark questions.

**At creation time:** validate all benchmark SQL by executing it (same as example SQL). Only verify the SQL runs without errors — do not run benchmark accuracy evaluations during creation. Include benchmarks in the `serialized_space` JSON under the `benchmarks` key — see [references/schema.md](references/schema.md) for the schema.

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
> - *Join specs: [list table relationships]*
> - *Hidden columns: [list columns to exclude, or "none"]*
> - *Benchmarks: [count] Core (original + rephrased example SQL questions, reusing exact ground truth SQL) + [count] Stretch (new questions testing generalization)*"
>
> **Only proceed to generate the configuration after the user confirms.** This is your last checkpoint before building — any corrections here are easy, but corrections after creation require the diagnose and optimize workflow.

## Step 5: Generate Configuration

Build the `serialized_space` JSON using the schema and examples in [references/schema.md](references/schema.md). Include only sections relevant to the user's space.

**Critical formatting rules** (these cause API rejection if wrong):
- `version`: **Required**. Use `2` for new spaces
- All IDs: exactly 32 lowercase hex characters — generate with `secrets.token_hex(16)`
- All arrays with `id` fields must be **sorted alphabetically by `id`**. Tables sorted by `identifier`. `column_configs` sorted by `column_name`.
- `sql` fields are **string arrays** — each SQL clause is a separate element with `\n`: `["SELECT\n", "  col\n", "FROM table"]`
- `sql_snippets` require **table-qualified column references** (`table_name.column`) — bare column names are rejected by the UI
- Filters must **NOT** include the `WHERE` keyword — only the boolean condition
- `join_specs.sql` requires **two elements**: (1) backtick-quoted join condition, (2) `"--rt=FROM_RELATIONSHIP_TYPE_...--"` annotation
- `text_instructions.content` elements must end with `\n` — the API concatenates without separators
- `benchmarks` section is **required** — include at least one benchmark per example SQL query with 2-3 alternate phrasings each. Benchmark IDs must be unique across both `sample_questions` and `benchmarks.questions`.
- **NEVER set `exclude: true`** on any column unless the user explicitly approved it in the plan review. If no columns were approved for exclusion, do not exclude any. This is a hard rule — do not infer which columns to hide based on column names like `_id`, `etl_`, etc.
- Include only what's needed for other sections — omit sections that don't apply (e.g., skip `metric_views` if none)


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

**After creating the space**, display a clickable link: `https://{w.config.host}/genie/rooms/{space_id}`

> **Important post-creation step:** Prompt matching (format assistance + entity matching) is **not auto-enabled when creating via the API**. After the space is created, remind the user:
>
> *"Your space is live! One important step: prompt matching (which helps Genie match user terms like 'California' to actual values like 'CA') is only auto-enabled when tables are added via the UI. Since we created this space via the API, please open the space, go to Configure > Data, and verify that Format assistance and Entity matching are enabled for your key filter columns (under each column's Advanced settings). The `column_configs` I included cover [list columns], but any other string/category columns may need to be enabled manually."*


**Notes:** All scripts use `WorkspaceClient()` which auto-authenticates in notebook context. The creating user's compute credentials are embedded into the space. Rate limits: 20 questions/minute (UI), 5 questions/minute (API free tier).

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

Your space ships with Core and Stretch benchmarks from Step 4g. After creation, run them from the **Benchmarks** tab:

**Interpreting results:**
- **Core benchmarks:** Expected accuracy is **high** (80-100%). These reuse exact example SQL as ground truth, so failures indicate a real problem — ambiguous columns, conflicting instructions, or missing metadata. Fix the root cause in the space.
- **Stretch benchmarks:** Expected accuracy is **naturally lower**. These test generalization with independently written SQL. Low scores here are not a failure — they show where Genie needs more guidance. Add example SQL queries for low-scoring question patterns.

| Rating | Condition |
|--------|-----------|
| **Good** | Generated SQL or result set matches ground truth (including different sort order or numeric values matching to 4 significant digits) |
| **Bad** | Empty result set, error, extra columns, or different single-cell result |
| **Manual review** | Genie couldn't assess, or no SQL answer was provided |

For the full evaluation workflow, see [Use benchmarks in a Genie space](https://docs.databricks.com/aws/en/genie/benchmarks).

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

See [references/example_conversation.md](references/example_conversation.md) for a full multi-turn example demonstrating the pause-heavy, conversational pattern.

## Validation Checklist

See [references/validation_checklist.md](references/validation_checklist.md) — run through this before creating the space.

## Error Handling, Troubleshooting, and Additional Resources

For error handling, troubleshooting, the diagnose/optimize workflow, and links to official Databricks documentation, see [references/diagnose_optimize_space.md](references/diagnose_optimize_space.md).
