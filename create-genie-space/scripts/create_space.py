"""
Create a new Databricks AI/BI Genie space via the API.

This is a template script — adapt the tables, sample questions,
instructions, and parameters to match the user's requirements.

Usage: Run this script in a Databricks notebook cell after
gathering requirements from the user.
"""

import json
import secrets

from databricks.sdk import WorkspaceClient

w = WorkspaceClient()

# --- CONFIGURE THESE VALUES ---

# Tables to include (sorted alphabetically by identifier)
# Optional "description" field overrides the Unity Catalog description for this space only
tables = sorted([
    {"identifier": "catalog.schema.table1", "description": ["Description of table1"]},
    {"identifier": "catalog.schema.table2"},
], key=lambda x: x["identifier"])

# Metric views (optional) — pre-defined metrics, dimensions, and aggregations
# metric_views = sorted([
#     {"identifier": "catalog.schema.metric_view1", "description": ["Revenue metrics"]},
# ], key=lambda x: x["identifier"])

# Sample questions for business users (one question per entry)
sample_questions_text = [
    "What were total sales last month?",
    "Show me top 10 products by revenue",
]

# Text instructions (domain-specific guidance)
text_instruction_lines = [
    "Revenue = quantity * unit_price.",
    "Fiscal year starts April 1st.",
]

# Example SQL queries (one question per SQL entry)
example_sqls = [
    {
        "question": ["What are total sales by product category?"],
        "sql": [
            "SELECT\n",
            "  p.category,\n",
            "  SUM(o.quantity * o.unit_price) as total_sales\n",
            "FROM catalog.schema.orders o\n",
            "JOIN catalog.schema.products p ON o.product_id = p.product_id\n",
            "GROUP BY p.category\n",
            "ORDER BY total_sales DESC",
        ],
    },
]

# SQL expressions — measures, filters, dimensions
sql_snippet_measures = [
    {"alias": "total_revenue", "sql": ["SUM(amount)"]},
]
sql_snippet_filters = [
    {"display_name": "high value", "sql": ["amount > 1000"]},
]
sql_snippet_expressions = [
    {"alias": "order_year", "sql": ["YEAR(order_date)"]},
]

# Join specifications (optional)
# join_specs = [
#     {
#         "left": {"identifier": "catalog.schema.orders"},
#         "right": {"identifier": "catalog.schema.customers"},
#         "sql": ["orders.customer_id = customers.customer_id"],
#     },
# ]

# SQL functions (Unity Catalog UDFs, optional)
# sql_functions = [
#     {"identifier": "catalog.schema.fiscal_quarter"},
# ]

# Space metadata
warehouse_id = "your_serverless_warehouse_id"
parent_path = "/Users/your.email@company.com"
title = "Sales Analytics"
description = "Analyze sales performance and customer trends"

# --- BUILD CONFIGURATION ---

# Generate unique 32-character hex IDs (sorted alphabetically)
question_ids = sorted([secrets.token_hex(16) for _ in sample_questions_text])
example_sql_ids = sorted([secrets.token_hex(16) for _ in example_sqls])
instruction_id = secrets.token_hex(16)

# Add IDs to sql_snippets
for item in sql_snippet_measures + sql_snippet_filters + sql_snippet_expressions:
    item["id"] = secrets.token_hex(16)

config = {
    "version": 2,
    "config": {
        "sample_questions": sorted(
            [
                {"id": question_ids[i], "question": [sample_questions_text[i]]}
                for i in range(len(sample_questions_text))
            ],
            key=lambda x: x["id"],
        )
    },
    "data_sources": {
        "tables": tables,
        # "metric_views": metric_views,  # Uncomment if using metric views
    },
    "instructions": {
        "text_instructions": [
            {
                "id": instruction_id,
                "content": text_instruction_lines,
            }
        ],
        "example_question_sqls": sorted(
            [
                {
                    "id": example_sql_ids[i],
                    "question": example_sqls[i]["question"],
                    "sql": example_sqls[i]["sql"],
                }
                for i in range(len(example_sqls))
            ],
            key=lambda x: x["id"],
        ),
        "sql_snippets": {
            "measures": sorted(sql_snippet_measures, key=lambda x: x["id"]),
            "filters": sorted(sql_snippet_filters, key=lambda x: x["id"]),
            "expressions": sorted(sql_snippet_expressions, key=lambda x: x["id"]),
        },
        # "join_specs": sorted(
        #     [{"id": secrets.token_hex(16), **js} for js in join_specs],
        #     key=lambda x: x["id"],
        # ),
        # "sql_functions": sorted(
        #     [{"id": secrets.token_hex(16), **sf} for sf in sql_functions],
        #     key=lambda x: x["id"],
        # ),
    },
}

# --- CREATE THE SPACE ---

response = w.api_client.do(
    "POST",
    "/api/2.0/genie/spaces",
    body={
        "serialized_space": json.dumps(config),
        "warehouse_id": warehouse_id,
        "parent_path": parent_path,
        "title": title,
        "description": description,
    },
)

space_id = response.get("space_id")
host = w.config.host.rstrip("/")
print(f"Successfully created Genie space!")
print(f"  Space ID: {space_id}")
print(f"  URL: {host}/genie/rooms/{space_id}")
