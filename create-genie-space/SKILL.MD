---
name: create-genie-space
description: Guide users through creating and managing Databricks AI/BI Genie spaces using natural language. Helps gather requirements, configure data sources, define sample questions, generate the space configuration, and manage existing spaces by auditing, diagnosing issues, and optimizing configuration. Use when the user wants to create, build, set up, update, audit, troubleshoot, or optimize a Genie space.
---

# Create and Manage Genie Spaces

Guide users through creating new Databricks AI/BI Genie spaces or managing existing ones — auditing configuration, diagnosing issues, and optimizing for accuracy.

**Determine intent first:** If the user wants to create a new space, follow the **Create a New Space** workflow. If they have an existing space they want to review, fix, or improve, follow the **Manage an Existing Space** workflow.

## Workflow Overview

### Create a New Space
1. **Gather Requirements** - Define purpose, audience, and scope (start small)
2. **Identify Data Sources** - Select focused Unity Catalog tables (aim for ≤5)
3. **Define Sample Questions** - Create starter questions for business users
4. **Configure Instructions** - Prioritize SQL expressions > example SQL > text instructions
5. **Generate Configuration** - Build the serialized_space JSON
6. **Create the Space** - Call the Genie API to create the space
7. **Test and Iterate** - Self-test, benchmark, gather feedback, and refine

### Manage an Existing Space
1. **Retrieve Current Configuration** - Fetch and parse the space's serialized_space JSON
2. **Audit Against Best Practices** - Evaluate tables, instructions, and metadata quality
3. **Diagnose Reported Issues** - Triage specific problems users are experiencing
4. **Recommend Optimizations** - Suggest proactive improvements
5. **Apply Updates** - Modify configuration via the PATCH API
6. **Benchmark and Verify** - Run benchmarks to confirm improvements

---

# Create a New Space

## Step 1: Gather Requirements

A well-defined Genie space should answer questions for a **specific topic and audience**, not general questions across various domains. Start by understanding the user's needs clearly.

Ask the user about:

- [ ] **Purpose**: What specific business questions should this space answer? Be narrow and focused.
- [ ] **Audience**: Who will use this space? (analysts, executives, etc.) Ideally, a domain expert who understands both the data and the business insights should help define the space.
- [ ] **Data Domain**: What single area does the data cover? (sales, finance, operations, etc.)
- [ ] **Scope**: Start small — aim for a minimal setup with essential tables and basic instructions. It's easier to add more later than to debug an overly complex space.

**Example prompt:**
> "What kind of questions do you want users to be able to ask in this Genie space? For example: sales analytics, customer insights, inventory tracking? Try to keep it focused on one topic — a narrowly scoped space gives more accurate answers."

**Key principle:** Curating a Genie space is an iterative process. Plan to start small and refine based on real user feedback rather than aiming for perfection on the first pass.

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
sql
SHOW TABLES IN catalog.schema;


### Validate Table Access

Before adding tables to the space, verify the user has access:
sql
DESCRIBE TABLE catalog.schema.table_name;


If successful, the table is accessible and can be included in the Genie space.

### Check Column Quality

Review column names and descriptions to assess annotation quality:
sql
DESCRIBE TABLE EXTENDED catalog.schema.table_name;


If column descriptions are missing or unclear, suggest the user add them in Unity Catalog first — this significantly improves Genie's response accuracy.

**Reference script:** See `scripts/discover_resources.py` (Part 2) for a comprehensive audit that checks table comments, column descriptions, column counts, foreign keys, and generates a Genie-readiness quality score with specific recommendations.

### Define Table Relationships

If foreign key references are not defined in Unity Catalog, Genie may not know how to join tables correctly. Recommend users:

1. **Define foreign keys in Unity Catalog** when possible (most reliable)
2. **Define join relationships in the Genie space's knowledge store** — useful for complex join scenarios (self-joins, etc.) or when you can't modify the underlying tables
3. **Provide example SQL queries with correct joins** as a fallback
4. **Pre-join tables into views** if none of the above work

### Build a Knowledge Store (Post-Creation, in UI)

After creating the space via the API, recommend that users build out the **knowledge store** in the Genie space UI. A knowledge store is a collection of curated semantic definitions scoped to the space:

- **Column metadata and synonyms** — custom descriptions and alternate names to reduce ambiguity
- **SQL expressions** — reusable definitions for metrics, filters, and dimensions
- **Join relationships** — explicit definitions of how tables relate
- **Prompt matching** — helps Genie match user values to correct columns (e.g., "California" → "CA"), automatically enabled when tables are added

These enhancements don't require write access to the underlying Unity Catalog tables — they're scoped to the Genie space only.

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

Use SQL expressions to define frequently used business terms as reusable definitions. These are the most efficient way to teach Genie your business logic.

**Good candidates for SQL expressions:**
- Metrics: gross margin, conversion rate, revenue
- Filters: "active customer", "recent order", "high-value account"
- Dimensions: fiscal quarter, product category groupings

### 4b: Example SQL Queries (Recommended for Complex Questions)

Use complete example SQL queries for hard-to-interpret, multi-part, or complex questions. These show Genie how to handle intricate query patterns and multi-step logic. Queries can be **static** or **parameterized**.

**Good candidates for example SQL queries:**
- Questions requiring complex joins across multiple tables
- Multi-step calculations (e.g., "For customers who joined recently, what products are doing best?")
- Domain-specific aggregations or breakdowns (e.g., "breakdown my team's performance")

**Include multiple phrasings** for each example to help Genie match variations.

**Critical formatting rule:** Each phrasing must be a **separate string element** in the array. Never concatenate multiple phrasings into one string.

json
{
  "question": [
    "What are total sales by product category?",
    "Show me sales broken down by category",
    "Sales by category"
  ],
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


#### Parameterized Queries

Add parameters to example SQL using the `:parameter_name` syntax. Parameterized queries become **trusted assets** — when Genie uses them, the response is labeled **Trusted**, giving users extra confidence in accuracy. Users can edit parameter values and rerun the query.

**Example:**
sql
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
sql
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

**Important:** Genie spaces require a **serverless** SQL warehouse (pro warehouses also work). The script filters to show only serverless warehouses.


## Step 5: Generate Configuration

Build the `serialized_space` JSON with all gathered information:

json
{
  "version": 2,
  "config": {
    "sample_questions": [
      {
        "id": "a1b2c3d4e5f60000000000000000000a",
        "question": ["<sample question text>"]
      }
    ]
  },
  "data_sources": {
    "tables": [
      {"identifier": "catalog.schema.table1"},
      {"identifier": "catalog.schema.table2"}
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "b2c3d4e5f6a70000000000000000000b",
        "content": [
          "<instruction text line 1>",
          "<instruction text line 2>"
        ]
      }
    ]
  }
}


**Important Notes:**
- `version`: **Required**. Use `2` for new spaces (version 1 exists for backwards compatibility only)
- `question`: Must be an array of strings. **Each phrasing must be a separate element** — never concatenate multiple phrasings into one string:
  - Correct: `["What were total sales last month?", "Show me last month's sales", "Total sales for previous month"]`
  - Wrong: `["What were total sales last month?Show me last month's salesTotal sales for previous month"]`
- `sql`: Must be an array of strings. **Each SQL clause should be a separate element** with `\n` at the end:
  - Correct: `["SELECT\n", "  col1,\n", "  col2\n", "FROM table\n", "WHERE col1 > 0"]`
  - Wrong: `["SELECT col1, col2FROM tableWHERE col1 > 0"]`
- `instructions`: Optional structured object containing:
  - `text_instructions`: Array of instruction objects (maximum 1 text instruction per space), each with a unique 32-char hex `id` and `content` array of strings
  - Can also include `example_question_sqls`, `join_specs`, `sql_snippets`, `sql_functions`, and other advanced configurations
- **ID Format**: All IDs must be exactly 32 lowercase hexadecimal characters (no hyphens)


### ID Generation
Generate unique 32-character hexadecimal IDs (UUID format without hyphens):
python
import secrets
question_id = secrets.token_hex(16)  # Generates 32-char hex string, e.g., "a1b2c3d4e5f60000000000000000000a"


**Important ID Requirements:**
- Must be exactly 32 characters long
- Must be lowercase hexadecimal (0-9, a-f)
- No hyphens or other separators
- Must be unique within their collection


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

**Reference script:** See `scripts/create_space.py` for the complete template. Adapt the tables, sample questions, instructions, and parameters to match the user's requirements.


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

## Complete Example Conversation

**User:** "I want to create a Genie space for our sales team"

**Agent:** "I can help you create a Genie space for sales analytics. Let me gather some information:

1. What specific questions should users be able to ask? (e.g., revenue analysis, product performance, regional comparisons)
2. Which Unity Catalog tables contain your sales data?"

**User:** "They need to analyze revenue by product and region. The data is in `analytics.sales.orders` and `analytics.sales.products`"

**Agent:** "Got it. Here are some sample questions I'll include:
- What is total revenue by product category?
- Show me sales trends by region over the last 12 months
- Which products have the highest profit margin?

What serverless SQL warehouse should this space use, and where in the workspace should I create it?"

**User:** "Use warehouse `abc123`, put it in `/Users/sean/genie_spaces`, call it 'Sales Analytics'"

**Agent generates and creates the space with the configuration**

## Validation Checklist

Before creating the space, verify:

- [ ] Space has a **clearly defined purpose** for a specific topic and audience
- [ ] At least one valid Unity Catalog table is specified
- [ ] Tables are **focused** — ideally 5 or fewer, maximum 25
- [ ] Tables exist and user has SELECT permission
- [ ] Column names and descriptions are clear and well-annotated in Unity Catalog
- [ ] Warehouse ID is valid and is a serverless SQL warehouse
- [ ] Parent path exists in workspace
- [ ] Sample questions are business-friendly and cover common use cases
- [ ] **Example SQL queries** are included for complex or multi-step questions
- [ ] **All example SQL queries have been executed** and return valid results (no errors, non-empty)
- [ ] **Text instructions** are concise, specific, and non-conflicting
- [ ] Instructions across all types are consistent (e.g., same rounding, same date conventions)
- [ ] Title and description are provided

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

# Manage an Existing Space

Use this workflow when a user has an existing Genie space and wants to review, fix, or improve it. Ask the user for their **space ID** to get started.

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

**Present findings** to the user as a prioritized list, starting with the highest-impact improvements.

## Step M3: Diagnose Reported Issues

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
1. Check if prompt matching is enabled for the relevant column
2. Check if example values are configured in the knowledge store
3. Recommend: Enable prompt matching, add value dictionaries, refresh values if data changed

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

## Step M4: Recommend Optimizations

After auditing the config and/or diagnosing issues, proactively suggest improvements. Frame recommendations as specific, actionable changes with clear rationale.

**Example recommendations:**

- "You have 5 example SQL queries but none use parameters. Consider converting the 2 queries that filter by region to use `:region` parameters — this gives users trusted asset labeling and lets them change the filter value."
- "Your text instructions are 1800 characters with 6 metric definitions inline. Consider moving those metrics to SQL expressions in the knowledge store — they're more precise and reduce text instruction length."
- "Tables `orders` and `order_details` both have a `total` column. This likely causes ambiguity. Recommend hiding `order_details.total` or renaming via a view."
- "No benchmark questions found. Recommend adding 10-20 benchmarks covering the sample questions (with 2-4 phrasings each) to track accuracy as you iterate."
- "You have 18 tables — this is above the recommended 5. Consider prejoining related dimension tables into views to reduce complexity."
- "Column `forecastcategory` in `opportunity` has no description. Genie may misinterpret it. Add a description like 'Forecast stage: Pipeline, Best Case, Commit, Closed.'"

**Always present a summary** of proposed changes before applying them.

## Step M5: Apply Updates

After the user approves changes, apply them via the PATCH API.

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


### Example SQL Query Format

When adding `example_question_sqls`, each example should include:

- `id`: Unique 32-character hex ID
- `question`: Array of natural language phrasings
- `sql`: Array of strings representing the SQL query (split by lines)

json
{
  "id": "c3d4e5f6a7b80000000000000000000c",
  "question": [
    "What are total sales by product category?",
    "Show me sales broken down by category"
  ],
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


## Step M6: Benchmark and Verify

After applying updates, recommend that the user runs benchmarks to verify improvements.

1. **If benchmarks exist:** Re-run all benchmarks (or the subset related to the changes) from the **Benchmarks** tab and compare accuracy to the previous run.
2. **If no benchmarks exist:** Recommend creating 10-20 benchmark questions covering the space's core use cases, with 2-4 phrasings each and SQL ground truth answers.
3. **Manual testing:** Ask the user to test the specific questions that were previously failing, using a **new chat** to avoid influence from prior conversation context.
4. **Clone for safe testing:** For significant changes, recommend cloning the space first, applying changes to the clone, and benchmarking there before updating production.

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