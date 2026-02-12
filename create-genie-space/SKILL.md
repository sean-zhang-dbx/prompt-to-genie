---
name: create-genie-space
description: Guide users through creating and managing Databricks AI/BI Genie spaces using natural language. Helps gather requirements, configure data sources, define sample questions, generate the space configuration, and manage existing spaces by auditing, diagnosing issues, and optimizing configuration. Use when the user wants to create, build, set up, update, audit, troubleshoot, or optimize a Genie space.
---

# Create and Manage Genie Spaces

Guide users through creating new Databricks AI/BI Genie spaces or managing existing ones — auditing configuration, diagnosing issues, and optimizing for accuracy.

**Determine intent first:** If the user wants to create a new space, follow the **Create a New Space** workflow. If they have an existing space they want to review, fix, or improve, follow the **Manage an Existing Space** workflow.

## Workflow Overview

### Create a New Space
1. **Gather Requirements (Most Important)** - Deep-dive into business context, terminology, conventions, and real user questions
2. **Identify and Profile Data Sources** - Select tables, then profile actual columns and values to confirm business term mappings
3. **Define Sample Questions** - Create starter questions grounded in confirmed data
4. **Configure Instructions** - Prioritize SQL expressions > example SQL > text instructions
5. **Generate Configuration** - Build the serialized_space JSON
6. **Create the Space** - Call the Genie API to create the space
7. **Test and Iterate** - Self-test, benchmark, gather feedback, and refine

### Manage an Existing Space
1. **Retrieve Current Configuration** - Fetch and parse the space's serialized_space JSON
2. **Audit Against Best Practices** - Evaluate tables, instructions, and metadata quality
3. **Diagnose Reported Issues** - Triage specific problems users are experiencing
4. **Recommend Optimizations** - Suggest improvements, tagged as API or UI changes
5. **Apply Updates** - Two modes:
   - **Mode A: Assistant applies** — modify config via the PATCH API
   - **Mode B: Guided walkthrough** — walk the user step-by-step through the Genie UI
6. **Benchmark and Verify** - Run benchmarks to confirm improvements

---

# Create a New Space

## Step 1: Gather Requirements (Most Important Step)

**Getting the initial room right is far more valuable than iterating on a broken one.** Invest time upfront to deeply understand the business context — this is the single biggest factor in whether the space works well out of the box.

A well-defined Genie space answers questions for a **specific topic and audience**, not general questions across various domains. Gather requirements in two phases: first the business context, then the data context.

### Phase 1: Business Context Interview

Ask the user about each of these. **Do not move to Step 2 until you have clear answers.**

- [ ] **Purpose**: What specific business questions should this space answer? Ask for 5-10 real questions that end users actually ask today. Not hypothetical — actual questions from meetings, Slack, emails, etc.
- [ ] **Audience**: Who will use this space? What's their technical level? What decisions do they make with this data?
- [ ] **Data Domain**: What single area does the data cover? (sales, finance, operations, etc.)
- [ ] **Business terminology**: What domain-specific terms do users use? Ask for a glossary of key terms and their exact definitions. For example:
  - "What does 'active customer' mean in your context?"
  - "How do you define 'revenue' — gross, net, ARR?"
  - "What's an 'open pipeline' vs. 'committed pipeline'?"
- [ ] **Calendar and time conventions**: This is a common source of errors. Ask explicitly:
  - "What is your fiscal year calendar? (e.g., Feb-Jan, Apr-Mar, Jan-Dec)"
  - "When someone says 'Q1', what months does that mean?"
  - "Do you use fiscal year or calendar year by default?"
- [ ] **Key metrics, filters, and dimensions**: What business terms do users frequently reference? These become SQL expressions.
  - Metrics: "total revenue", "conversion rate", "average deal size"
  - Filters: "active customer", "EMEA region", "enterprise tier"
  - Dimensions: "fiscal quarter", "product line", "sales stage"
- [ ] **Filtering conventions**: How do users refer to filter values?
  - "When someone says 'Lakebase', which column and value does that correspond to?"
  - "Do your region names use codes (EMEA, NA) or full names (Europe, North America)?"
  - "Are product names stored as codes, display names, or something else?"
- [ ] **Scope**: Start small — essential tables and basic instructions only. It's easier to add more later than to debug an overly complex space.

**Example prompt:**
> "Before I build the Genie space, I need to deeply understand your business context. This upfront investment will make the space much more accurate out of the box. Can you tell me:
> 1. What are 5-10 real questions your team asks about this data today?
> 2. What key business terms does your team use, and what do they mean precisely?
> 3. What is your fiscal calendar? (e.g., when does Q1 start?)
> 4. When users filter by things like region, product, or status — what values do they use, and how are those stored in the data?"

**Key principle:** It's far more frustrating to debug a room that gets things wrong than to spend an extra few minutes gathering context upfront. Push back gently if the user tries to skip this step — the quality of the initial room depends on it.

## Step 2: Identify and Profile Data Sources

Determine which Unity Catalog tables to include, then **profile the actual data** before writing any SQL. This two-part step prevents the most common errors in Genie space creation.

### 2a: Select Tables

- [ ] **Catalog name**: Which catalog contains the data?
- [ ] **Schema name**: Which schema?
- [ ] **Table names**: Which specific tables?

**Example prompt:**
> "Which Unity Catalog tables should this Genie space have access to? Please provide the full path (catalog.schema.table)."

**Data Source Best Practices:**

- **Aim for 5 or fewer tables.** The more focused your selection, the better Genie performs. Limit the number of columns in your included tables to what's actually relevant.
- **Maximum 25 tables per space.** If you need more, prejoin related tables into views or metric views before adding them to the space.
- **Prejoin and de-normalize when possible.** Use views or metric views to resolve column ambiguities and simplify complex relationships. Metric views are particularly effective because they pre-define metrics, dimensions, and aggregations.
- **Build on well-annotated tables.** Genie uses Unity Catalog column names and descriptions to generate responses. Clear column names and descriptions help produce high-quality answers. Advise users to add or review column descriptions in Unity Catalog before creating the space.
- **Hide irrelevant columns.** After adding tables, recommend that users hide any columns that might be confusing or unimportant for the space's purpose. This reduces ambiguity for Genie.

**Table Format:**

catalog.schema.table_name


**Tip:** If the user is unsure, help them explore their catalog:
```sql
SHOW TABLES IN catalog.schema;
```


### 2b: Profile the Data (Required Before Writing Any SQL)

**Do not skip this step.** Before generating sample questions, SQL expressions, or example SQL queries, you must inspect the actual data in the tables. Do not assume column names, values, or date ranges based on table names alone.

**For each table, run:**

```sql
-- 1. What columns exist and what are their types?
DESCRIBE TABLE catalog.schema.table_name;

-- 2. What distinct values exist in key string/category columns?
SELECT DISTINCT column_name FROM catalog.schema.table_name LIMIT 20;

-- 3. What are the date ranges?
SELECT MIN(date_col), MAX(date_col) FROM catalog.schema.table_name;

-- 4. Sample rows to understand the data shape
SELECT * FROM catalog.schema.table_name LIMIT 5;
```

**Reference script:** See `scripts/discover_resources.py` — Part 2 audits table metadata quality, Part 3 (set `enable_profiling = True`) profiles actual column values for string/category and date columns.

**After profiling, cross-reference with the user's business context from Step 1:**

1. **Column mapping**: Present the user with a summary of columns and ask them to confirm which columns map to their business terms. For example:
   > "I see the table has a `use_case_product` column with values like 'AI/BI', 'DWH', 'Unity Catalog'. Is this the column to use when users ask about 'Lakebase' or 'Genie' products? What value should I filter on?"

2. **Value confirmation**: Show the user the actual distinct values for key filter columns and ask them to confirm the mapping. For example:
   > "The `region` column has values: 'AMER', 'EMEA', 'APJ'. When users say 'North America', should I filter on 'AMER'?"

3. **Date range confirmation**: Show the user the date ranges and confirm calendar conventions. For example:
   > "The `order_date` column ranges from 2023-01-15 to 2025-12-31. You mentioned fiscal Q1 is Feb-Apr — so for 'FY25 Q1', I should filter Feb 2025 to Apr 2025. Is that correct?"

**This confirmation step is critical.** The #1 cause of poor initial rooms is the Assistant guessing how business terms map to actual column values. Always confirm with the user.

### 2c: Check Column Quality

Review column names and descriptions to assess annotation quality:
```sql
DESCRIBE TABLE EXTENDED catalog.schema.table_name;
```


If column descriptions are missing or unclear, suggest the user add them in Unity Catalog first — this significantly improves Genie's response accuracy.

**Column-level configuration via API:** You can also set per-column metadata directly in the `serialized_space` using `column_configs` on each table — including descriptions, synonyms, hiding columns, and entity matching. See `references/schema.md` → "Field Reference → data_sources" for all available fields and their types.

### 2d: Define Table Relationships

If foreign key references are not defined in Unity Catalog, Genie may not know how to join tables correctly. Recommend users:

1. **Define foreign keys in Unity Catalog** when possible (most reliable)
2. **Define join relationships via `join_specs`** in the config — include `alias`, `join_type`, `comment` (business context), and `instruction` (when to use). For multi-column joins, create separate join specs with comments indicating they should be used together.
3. **Provide example SQL queries with correct joins** as a fallback
4. **Pre-join tables into views** if none of the above work

## Step 3: Define Sample Questions

Create 3-5 starter questions that demonstrate the space's capabilities. **Base these on the real user questions from Step 1 and the confirmed data mappings from Step 2b** — don't invent questions that reference columns or values you haven't verified.

- Questions should be business-focused, not technical
- Cover common use cases for the target audience
- Use natural language that business users would actually ask
- Only reference data concepts you've confirmed exist in the actual tables

**Good examples:**
- "What were total sales last quarter?"
- "Which products have the highest profit margin?"
- "Show me customer retention trends by region"

**Avoid:**
- "SELECT * FROM sales" (too technical)
- "Get data" (too vague)
- Questions referencing columns or values you haven't verified exist

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
  {"id": "...", "alias": "total_revenue", "display_name": "Total Revenue", "sql": ["SUM(amount)"], "synonyms": ["revenue", "sales"], "instruction": ["Use for any revenue aggregation"]}
  ```
- **Filters** (`sql_snippets.filters`): Common filtering conditions (boolean)
  ```json
  {"id": "...", "display_name": "high value", "sql": ["amount > 1000"], "synonyms": ["big deal", "large order"], "instruction": ["Apply when users ask about high-value orders"]}
  ```
- **Dimensions** (`sql_snippets.expressions`): Attributes for grouping and analysis
  ```json
  {"id": "...", "alias": "order_year", "display_name": "Order Year", "sql": ["YEAR(order_date)"], "synonyms": ["year"], "instruction": ["Use for year-based grouping"]}
  ```

**Optional but recommended fields** on all snippet types: `synonyms`, `instruction`, `comment`. See `references/schema.md` → "sql_snippets" for the full field reference.

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

**Critical:** Follow the SQL formatting rules in `references/schema.md` → "Important Notes" — each SQL clause must be a separate array element with `\n` at the end.

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
  ],
  "usage_guidance": ["Use this pattern for any breakdown of sales metrics by product attribute"]
}
```

**`usage_guidance`** (optional but recommended): Tells Genie when to apply this query pattern. Include it on complex examples so Genie knows which keywords or question types should trigger it.

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

**Critical: Text instructions must reflect the actual data model.** Before writing text instructions:
1. **Inspect actual column names** — don't describe columns that don't exist
2. **Verify filter values** — reference actual values from the data, not assumed ones
3. **Confirm business definitions** with the user (fiscal calendars, product names, abbreviations)
4. **Remove or update stale guidance** — never leave instructions that reference old column names, removed tables, or deprecated business logic

**Good text instructions:**
- "Active customer" means a customer with at least one order in the last 90 days
- Revenue should always be calculated as quantity * unit_price * (1 - discount)
- Fiscal year starts April 1st
- All monetary values are in USD unless otherwise specified
- The `use_case_product` column contains product type values like "AI/BI", "DWH", "Unity Catalog" — use this column to filter by product

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

**Reference script:** See `scripts/discover_resources.py` for the complete code. Part 1 lists all serverless SQL warehouses (name, ID, state, size) and prints the workspace URL. Part 2 audits table metadata quality for Genie-readiness.

**Important:** Genie spaces require a **pro or serverless** SQL warehouse (serverless recommended for performance). The script filters to show only serverless warehouses.


## Step 5: Generate Configuration

Build the `serialized_space` JSON with all gathered information.

- **Full JSON schema, field reference, and formatting rules:** See `references/schema.md`
- **Code template with all sections:** See `scripts/create_space.py`


## Step 6: Create the Space

### Required Parameters
 Parameter | Description |
-----------|-------------|
 `serialized_space` | JSON string from Step 5 |
 `warehouse_id` | Serverless SQL warehouse ID (required) |
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
- **Errors**: ID format, sorting, uniqueness, required fields, limits, concatenated questions, malformed SQL
- **Warnings**: Table count, instruction budget, formatting issues
- **Parameterization suggestions**: Detects similar queries that could be consolidated into parameterized queries, and flags hardcoded filter values that should use `:parameter` syntax

### Test Example SQL Queries

**Before calling the API**, execute every example SQL query to verify it runs successfully and returns the expected results. Do not create the space with untested SQL.

**Verify correctness, not just execution:**
- Does the query filter on the right columns? (Check actual column names via `DESCRIBE TABLE`)
- Do the filter values match what's in the data? (Check via `SELECT DISTINCT`)
- Are date ranges correct for the user's fiscal calendar or business conventions?
- Does the result make business sense?

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

**Reference script:** See `scripts/create_space.py` for the complete template. Adapt the tables, sample questions, instructions, and parameters to match the user's requirements.

**After creating the space**, always display a clickable link to the user using this format:

```
https://<workspace-url>/genie/rooms/<space_id>
```

Get the workspace URL from `w.config.host` (strip trailing slash) and the space ID from the API response. Example:
`https://adb-984752964297111.11.azuredatabricks.net/genie/rooms/01f0d5be61091b6ea75a6e8438c3bce2`


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

### Build a Knowledge Store (Post-Creation, in UI)

After creating the space, recommend that users build out the **knowledge store** in the Genie space UI. A knowledge store is a collection of curated semantic definitions scoped to the space:

- **Column metadata and synonyms** — custom descriptions and alternate names to reduce ambiguity
- **SQL expressions** — reusable definitions for metrics, filters, and dimensions
- **Join relationships** — explicit definitions of how tables relate
- **Prompt matching** — helps Genie match user values to correct columns (e.g., "California" → "CA"), automatically enabled when tables are added

These enhancements don't require write access to the underlying Unity Catalog tables — they're scoped to the Genie space only.

### Self-Testing

1. **Ask questions** — Start with the sample questions, then try variations and different phrasings.
2. **Examine the SQL** — Click **Show code** on any response to review the generated SQL. Check that it uses the correct tables, joins, filters, and calculations.
3. **Fix misinterpretations** — If Genie misinterprets the data, business jargon, or question intent:
   - Add example SQL queries for the questions Genie got wrong (click **Add as instruction** on a corrected response)
   - Add or refine text instructions to clarify terminology
   - Add column metadata, synonyms, or example values in the knowledge store to reduce ambiguity
   - Check that relevant columns have **prompt matching** enabled to correct value/spelling mismatches
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

## Example Conversation Flow

This shows the expected depth of the requirements gathering process:

**User:** "I want to create a Genie space for our sales team"

**Agent:** "I'd love to help. Before building anything, I need to deeply understand your business context — this upfront investment is what makes the space accurate out of the box. Let me start with a few questions:

1. What are 5-10 real questions your team actually asks about sales data today? Not hypothetical — think of what comes up in meetings, Slack, or emails.
2. What key business terms does your team use? For example, how do you define 'revenue' — gross, net, or ARR? What does 'active customer' mean?
3. What is your fiscal calendar? When does Q1 start?
4. When users filter by region or product — what values do they use, and how are those stored in the data?"

**User:** "They ask things like 'What's our pipeline for EMEA this quarter?' and 'Which products have the highest revenue?' Revenue is net revenue after discounts. Our fiscal year starts February 1, so Q1 is Feb-Apr. Regions are stored as codes like AMER, EMEA, APJ. Data is in `analytics.sales.orders` and `analytics.sales.products`."

**Agent:** "Great — let me profile those tables to confirm the column mappings..."

*Agent runs `DESCRIBE TABLE` and `SELECT DISTINCT` on key columns, then presents findings:*

**Agent:** "I see the `orders` table has a `region_code` column with values: AMER, EMEA, APJ, LATAM. And a `net_revenue` column. The `order_date` ranges from 2023-01-15 to 2025-12-31. Can you confirm:
- When users say 'EMEA', I should filter `region_code = 'EMEA'`?
- 'Revenue' means the `net_revenue` column (not `gross_amount`)?
- 'This quarter' as of today means FY26 Q1 = Feb 2026 – Apr 2026?"

**User:** "Yes, all correct."

**Agent:** *Proceeds to build configuration with confirmed mappings, SQL expressions for net revenue and fiscal quarters, and example SQL queries validated against actual data.*

**See `examples/` for complete conversation histories with full notebook output.**

## Validation Checklist

Before creating the space, verify:

- [ ] Space has a **clearly defined purpose** for a specific topic and audience
- [ ] At least one valid Unity Catalog table is specified
- [ ] Tables are **focused** — ideally 5 or fewer, maximum 25
- [ ] Tables exist and user has SELECT permission
- [ ] **Data profiling complete** (Step 2b) — actual columns, values, and date ranges inspected and confirmed with user
- [ ] Column names and descriptions are clear and well-annotated in Unity Catalog
- [ ] Warehouse ID is valid and is a pro or serverless SQL warehouse
- [ ] Parent path exists in workspace
- [ ] Sample questions are business-friendly and cover common use cases
- [ ] **SQL expressions** (`sql_snippets`) are defined for key metrics, filters, and dimensions
- [ ] **Example SQL queries** are included for complex or multi-step questions
- [ ] **All example SQL queries have been executed** and return valid, correct results (right columns, right filter values, business-sensible output)
- [ ] **Text instructions** are concise, specific, non-conflicting, and reference only columns/values that actually exist in the tables
- [ ] **No stale or placeholder text** in instructions (remove draft comments, TODO notes, or instructions referencing old schemas)
- [ ] Instructions across all types are consistent (e.g., same rounding, same date conventions)
- [ ] Title and description are provided

## Error Handling

If the API returns an error, see `references/troubleshooting.md` for the complete status code table and common error scenarios with solutions. The most frequent issues are:
- **400 BAD_REQUEST**: Usually a sorting, ID format, or JSON structure issue — run `scripts/validate_config.py` first
- **403 PERMISSION_DENIED**: Check permissions on the warehouse and tables
- **401 UNAUTHORIZED**: Check authentication credentials

---

# Manage an Existing Space

Use this workflow when a user has an existing Genie space and wants to review, fix, or improve it. Ask the user for their **space ID** to get started.

After diagnosing issues and recommending changes (Steps M1–M4), ask the user how they'd like to proceed:

> "I've identified the changes needed. How would you like to apply them?
> 1. **I'll make the changes for you** — I'll update the configuration via the API directly.
> 2. **Walk me through it** — I'll guide you step-by-step through the Genie UI so you can make the changes yourself."

**Mode A: Assistant Applies Changes** (Step M5-A) — Best for `serialized_space` config changes: adding/editing example SQL queries, SQL expressions, text instructions, sample questions, join specs, and SQL functions. The Assistant modifies the JSON and calls the PATCH API.

**Mode B: Guided Walkthrough** (Step M5-B) — Best for knowledge store and UI-only changes: enabling prompt matching, hiding columns, adding column synonyms, configuring value dictionaries, editing column descriptions, and setting up benchmarks. Also useful when users want to learn how to curate the space themselves.

Many updates involve changes from **both** modes — for example, adding SQL expressions (API) *and* enabling prompt matching on a filter column (UI). In that case, do Mode A first, then walk the user through the remaining UI steps.

## Step M1: Retrieve Current Configuration

Fetch the existing space configuration and parse it into a human-readable summary.

**Important:** The GET space API does **not** return `serialized_space` by default. You must pass the query parameter `include_serialized_space=true` to include it in the response. This requires at least **CAN EDIT** permission on the space.

**Reference script:** See `scripts/manage_space.py` (Part 1) for the complete retrieval and summary code. It displays all tables, sample questions, example SQL queries, SQL functions, text instructions, and the instruction count audit.


After retrieving the config, present the summary to the user and ask what they'd like to do: audit, diagnose a specific issue, or optimize.

## Step M2: Audit Against Best Practices

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
- [ ] **Prompt matching**: Remind users to verify that prompt matching is enabled for key filter columns in the UI.
- [ ] **Cross-section consistency**: Do `text_instructions`, `example_question_sqls`, and `sql_snippets` all align? No stale or contradictory guidance?

**Present findings** to the user as a prioritized list, starting with the highest-impact improvements.

## Step M3: Diagnose Reported Issues

If the user reports a specific problem, use this quick-reference decision tree to triage. For detailed symptom descriptions and step-by-step fixes, see `references/troubleshooting.md`.

| Reported Problem | First Check | Quick Action |
|-----------------|-------------|--------------|
| Wrong table or column | Table/column descriptions match user terms? Overlapping column names? | Add example SQL showing correct usage; hide confusing columns |
| Misunderstood terminology | Term defined in SQL expressions or text instructions? Column synonyms set? | Add SQL expression or text instruction mapping term → data concept |
| Wrong filter values (e.g., "California" vs "CA") | Prompt matching enabled? Example values configured? | Enable prompt matching; add value dictionaries |
| Incorrect joins | Foreign keys defined? Join specs or knowledge store entries? | Define join relationships; add example SQL with correct joins |
| Wrong metric calculations | Metric defined as SQL expression? Example SQL correct? Pre-aggregated tables? | Add SQL expressions for metrics; add example SQL for complex calculations |
| Wrong timezone/date calculations | Text instructions cover timezone? | Add explicit timezone instructions (e.g., `convert_timezone`) |
| Ignoring instructions | Conflicting instructions? Instruction count too high? | Add example SQL (most effective); hide irrelevant columns; simplify instruction set |
| Slow responses / timeouts | Slow queries in query history? | Use trusted assets; reduce example SQL length; start new chat |
| Token limit warning | Too many columns or verbose descriptions? | Hide unnecessary columns; streamline descriptions; prune redundant example SQL |

## Step M4: Recommend Optimizations

After auditing the config and/or diagnosing issues, proactively suggest improvements. Frame recommendations as specific, actionable changes with clear rationale. **Tag each recommendation** with how it's applied so the user can choose their preferred mode.

**Example recommendations:**

- **(API)** "You have 5 example SQL queries but none use parameters. Consider converting the 2 queries that filter by region to use `:region` parameters — this gives users trusted asset labeling and lets them change the filter value."
- **(API)** "Your text instructions are 1800 characters with 6 metric definitions inline. Consider moving those metrics to SQL expressions — they're more precise and reduce text instruction length."
- **(UI)** "Tables `orders` and `order_details` both have a `total` column. This likely causes ambiguity. Recommend hiding `order_details.total` in the space settings."
- **(UI)** "Prompt matching is not enabled for the `region` column. Enable it so Genie can map user input like 'North America' to the actual value 'AMER'."
- **(UI)** "No benchmark questions found. Recommend adding 10-20 benchmarks covering the sample questions (with 2-4 phrasings each) to track accuracy as you iterate."
- **(UI)** "Column `forecastcategory` in `opportunity` has no description. Add a description like 'Forecast stage: Pipeline, Best Case, Commit, Closed.'"
- **(API)** "You have 18 tables — this is above the recommended 5. Consider prejoining related dimension tables into views to reduce complexity."

**Always present a summary** of proposed changes before applying them, grouped by mode:

> **Changes I can apply via API:**
> - Add 3 SQL expressions for revenue, active customer, fiscal quarter
> - Add parameterized example SQL for pipeline by region
> - Update text instructions to remove stale terminology
>
> **Changes to make in the Genie UI:**
> - Enable prompt matching on `region` and `status` columns
> - Hide `internal_id` and `etl_timestamp` columns
> - Add 10 benchmark questions
>
> Would you like me to apply the API changes directly, walk you through both, or something else?

## Step M5-A: Apply Updates (Assistant Applies via API)

After the user approves changes, apply them via the PATCH API. Use this mode for `serialized_space` config changes.

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

**Reference script:** Run `scripts/validate_config.py` on the modified config **before** calling the PATCH API. This catches sorting errors, duplicate IDs, invalid formats, concatenated questions, malformed SQL, and suggests parameterization opportunities.

### Test New or Modified SQL Queries

If you are adding or changing `example_question_sqls`, **execute each new/modified query** before calling the PATCH API. Join the `sql` array into a single string, run it via `spark.sql(query).show()`, and confirm it returns valid results. Do not apply updates with untested SQL.

### Python Example

**Reference script:** See `scripts/manage_space.py` (Part 2) for the complete update code. It shows how to add example SQL queries, sort all ID-based collections, and call the PATCH API.

**After updating the space**, display the link to the user:

```
https://<workspace-url>/genie/rooms/<space_id>
```


**For the example SQL query format**, see Step 4b in the Create workflow above, or the `example_question_sqls` section in `references/schema.md`.


## Step M5-B: Guided Walkthrough (User Applies in UI)

Use this mode when the user wants to make changes themselves, or for changes that can only be made in the Genie space UI. Walk the user through each change step by step.

**For each recommended change, provide:**
1. **Where to go** — exact navigation path in the Genie UI
2. **What to do** — specific action with the exact values to enter
3. **Why** — brief rationale so the user understands the impact
4. **Verification** — how to confirm the change worked

**See `references/ui_walkthroughs.md`** for step-by-step templates covering: prompt matching, hiding columns, column synonyms, benchmarks, example values, and SQL expressions.

**Pacing:** Walk the user through one change at a time. After each change, ask: "Done? Let's move on to the next change." If the user gets stuck, offer to switch to Mode A (Assistant applies) for the API-compatible changes.

## Step M6: Benchmark and Verify

After applying updates, recommend that the user runs benchmarks to verify improvements.

1. **If benchmarks exist:** Re-run all benchmarks (or the subset related to the changes) from the **Benchmarks** tab and compare accuracy to the previous run.
2. **If no benchmarks exist:** Recommend creating 10-20 benchmark questions covering the space's core use cases, with 2-4 phrasings each and SQL ground truth answers.
3. **Manual testing:** Ask the user to test the specific questions that were previously failing, using a **new chat** to avoid influence from prior conversation context.
4. **Clone for safe testing:** For significant changes, recommend cloning the space first, applying changes to the clone, and benchmarking there before updating production.

---

**Reference files:** `references/schema.md` (JSON schema, field reference, formatting rules) · `references/troubleshooting.md` (error codes, troubleshooting) · `references/ui_walkthroughs.md` (UI step-by-step guides)
