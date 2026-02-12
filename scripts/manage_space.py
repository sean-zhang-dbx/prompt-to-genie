"""
Manage an existing Databricks AI/BI Genie space.

Part 1: Retrieve and summarize the current configuration.
Part 2: Apply updates via the PATCH API.

Usage: Run the relevant section in a Databricks notebook cell.
"""

import json
import secrets

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# --- PART 1: RETRIEVE AND SUMMARIZE CONFIGURATION ---

space_id = "your_space_id"

space_data = w.api_client.do(
    "GET",
    f"/api/2.0/genie/spaces/{space_id}",
    query={"include_serialized_space": "true"},  # Required to get the serialized_space field
)

current_config = json.loads(space_data.get("serialized_space", "{}"))

# Display summary
tables = current_config.get("data_sources", {}).get("tables", [])
metric_views = current_config.get("data_sources", {}).get("metric_views", [])
questions = current_config.get("config", {}).get("sample_questions", [])
instructions = current_config.get("instructions", {})
text_instr = instructions.get("text_instructions", [])
example_sqls = instructions.get("example_question_sqls", [])
sql_functions = instructions.get("sql_functions", [])
join_specs = instructions.get("join_specs", [])
snippets = instructions.get("sql_snippets", {})
snippet_measures = snippets.get("measures", [])
snippet_filters = snippets.get("filters", [])
snippet_expressions = snippets.get("expressions", [])

print(f"Space: {space_data.get('title', 'Untitled')}")
print(f"Description: {space_data.get('description', 'None')}")
print(f"\n{'='*60}")
print(f"Data Sources: {len(tables)} table(s)")
for t in tables:
    print(f"  - {t['identifier']}")
if metric_views:
    print(f"\nMetric Views: {len(metric_views)}")
    for mv in metric_views:
        print(f"  - {mv['identifier']}")
print(f"\nSample Questions: {len(questions)}")
for q in questions:
    print(f"  - {q['question'][0]}")
print(f"\nExample SQL Queries: {len(example_sqls)}")
for eq in example_sqls:
    print(f"  - {eq['question'][0]}")
print(f"\nSQL Functions: {len(sql_functions)}")
if join_specs:
    print(f"\nJoin Specs: {len(join_specs)}")
    for js in join_specs:
        left = js.get("left", {}).get("identifier", "?")
        right = js.get("right", {}).get("identifier", "?")
        jtype = js.get("join_type", "JOIN")
        print(f"  - {left} {jtype} {right}")
total_snippets = len(snippet_measures) + len(snippet_filters) + len(snippet_expressions)
if total_snippets:
    print(f"\nSQL Expressions: {total_snippets} (measures: {len(snippet_measures)}, filters: {len(snippet_filters)}, dimensions: {len(snippet_expressions)})")
    for m in snippet_measures:
        print(f"  - [measure] {m.get('alias', '?')}: {m.get('sql', '?')}")
    for f in snippet_filters:
        print(f"  - [filter] {f.get('display_name', '?')}: {f.get('sql', '?')}")
    for e in snippet_expressions:
        print(f"  - [dimension] {e.get('alias', '?')}: {e.get('sql', '?')}")
print(f"\nText Instructions: {len(text_instr)} block(s)")
if text_instr:
    for line in text_instr[0].get("content", []):
        print(f"  - {line}")

# Instruction count audit
total_instructions = len(example_sqls) + len(sql_functions) + (1 if text_instr else 0)
print(f"\n{'='*60}")
print(f"Total Instruction Count: {total_instructions} / 100")
if total_instructions > 80:
    print("  WARNING: Approaching the 100 instruction limit!")


# --- PART 2: APPLY UPDATES ---
# Uncomment and modify the section below to apply changes.

# # Example: Add a new example SQL query
# example_sql_id = secrets.token_hex(16)
# existing_sqls = current_config.get("instructions", {}).get("example_question_sqls", [])
# existing_sqls.append({
#     "id": example_sql_id,
#     "question": ["What are total sales by product category?"],
#     "sql": [
#         "SELECT\n",
#         "  p.category,\n",
#         "  SUM(o.quantity * o.unit_price) as total_sales\n",
#         "FROM catalog.schema.orders o\n",
#         "JOIN catalog.schema.products p ON o.product_id = p.product_id\n",
#         "GROUP BY p.category\n",
#         "ORDER BY total_sales DESC",
#     ],
# })
# current_config["instructions"]["example_question_sqls"] = sorted(
#     existing_sqls, key=lambda x: x["id"]
# )
#
# # Sort all ID-based collections (required by API)
# if "sample_questions" in current_config.get("config", {}):
#     current_config["config"]["sample_questions"] = sorted(
#         current_config["config"]["sample_questions"],
#         key=lambda x: x["id"]
#     )
#
# # Apply the update
# update_response = w.api_client.do(
#     "PATCH",
#     f"/api/2.0/genie/spaces/{space_id}",
#     body={
#         "serialized_space": json.dumps(current_config)
#     },
# )
#
# print(f"Successfully updated Genie space!")
# host = w.config.host.rstrip("/")
# print(f"  Space ID: {space_id}")
# print(f"  URL: {host}/genie/rooms/{space_id}")
