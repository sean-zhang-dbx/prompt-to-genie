# Example Conversation

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
5. Are there any columns I should hide? I won't exclude anything unless you tell me to — but columns like `etl_timestamp` or internal IDs are common candidates."

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
**Hidden columns:** etl_timestamp, internal_batch_id (per your request)
**Benchmarks:** 10 questions — Core: original + 2 alternate phrasings per example SQL query (6 total, reusing exact ground truth SQL), Stretch: 4 new questions testing generalization

Does this look right, or would you like to change anything?"

*(Agent waits for user approval)*

**User:** "Looks good! Use warehouse `abc123`, put it in `/Users/sean/genie_spaces`"

**Agent:** *(generates the configuration with benchmarks, validates via `validate_config.py`, executes all example SQL and benchmark SQL queries to verify they return valid results, then creates the space via the API)*
