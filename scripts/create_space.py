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
# "description" overrides the Unity Catalog description for this space only
# "column_configs" sets per-column metadata (prompt matching):
#   - enable_format_assistance: provides representative values
#   - enable_entity_matching: maps user terms to actual values (requires format_assistance)
#   - exclude: hides columns from Genie (reduces ambiguity)
# IMPORTANT: Prompt matching is NOT auto-enabled when creating via API.
# You must explicitly set enable_format_assistance and enable_entity_matching
# to True for every string/category column users will filter on.
tables = sorted([
    {
        "id": secrets.token_hex(16),
        "identifier": "catalog.schema.orders",
        "description": ["Daily sales transactions with line-item details"],
        "column_configs": sorted([
            {
                "id": secrets.token_hex(16),
                "column_name": "region",
                "description": ["Sales region code: AMER, EMEA, APJ, LATAM"],
                "synonyms": ["area", "territory"],
                "enable_entity_matching": True,
                "enable_format_assistance": True,
            },
            {
                "id": secrets.token_hex(16),
                "column_name": "status",
                "enable_entity_matching": True,
                "enable_format_assistance": True,
            },
            {
                "id": secrets.token_hex(16),
                "column_name": "etl_timestamp",
                "exclude": True,  # Hide irrelevant columns from Genie
            },
        ], key=lambda x: x["column_name"]),
    },
    {
        "id": secrets.token_hex(16),
        "identifier": "catalog.schema.products",
        "description": ["Product catalog with categories and pricing"],
        "column_configs": sorted([
            {
                "id": secrets.token_hex(16),
                "column_name": "category",
                "enable_entity_matching": True,
                "enable_format_assistance": True,
            },
        ], key=lambda x: x["column_name"]),
    },
], key=lambda x: x["identifier"])

# Metric views — pre-defined metrics, dimensions, and aggregations
# Remove this list if not using metric views
metric_views = sorted([
    {"id": secrets.token_hex(16), "identifier": "catalog.schema.revenue_metrics", "description": ["Revenue metrics by product and region"]},
], key=lambda x: x["identifier"])

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
# usage_guidance tells Genie when to apply this query pattern
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
        "usage_guidance": ["Use this pattern for any breakdown of sales metrics by product attribute"],
    },
]

# SQL expressions — measures, filters, dimensions
# IMPORTANT: sql is a plain string (NOT an array) for sql_snippets.
# Optional fields on all types: synonyms, instruction, comment, display_name
sql_snippet_measures = [
    {
        "alias": "total_revenue",
        "display_name": "Total Revenue",
        "sql": "SUM(quantity * unit_price)",
        "synonyms": ["revenue", "sales", "total sales"],
        "instruction": ["Use for any revenue aggregation"],
        "comment": ["Revenue includes all non-cancelled order line items"],
    },
]
sql_snippet_filters = [
    {
        "display_name": "high value",
        "sql": "WHERE amount > 1000",
        "synonyms": ["big deal", "large order"],
        "instruction": ["Apply when users ask about high-value or large orders"],
        "comment": ["Threshold aligned with finance team's definition"],
    },
]
sql_snippet_expressions = [
    {
        "alias": "order_year",
        "display_name": "Order Year",
        "sql": "YEAR(order_date)",
        "synonyms": ["year"],
        "instruction": ["Use for year-based grouping"],
        "comment": ["Standard date dimension for annual reporting"],
    },
]

# Join specifications — how tables relate to each other
# For multi-column joins, create separate join specs (compound AND/OR not supported in sql)
# Remove this list if tables have foreign keys defined in Unity Catalog
join_specs = [
    {
        "left": {"identifier": "catalog.schema.orders", "alias": "o"},
        "right": {"identifier": "catalog.schema.products", "alias": "p"},
        "join_type": "INNER JOIN",
        "sql": ["o.product_id = p.product_id"],
        "comment": ["Link orders to product details"],
        "instruction": ["Use this join for any question about sales by product attribute"],
    },
]

# SQL functions — Unity Catalog UDFs registered as trusted assets
# Remove this list if not using UDFs
sql_functions = [
    {
        "identifier": "catalog.schema.fiscal_quarter",
        "description": "Calculates the fiscal quarter from a date (fiscal year starts April 1)",
    },
]

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
        "metric_views": metric_views,  # Remove if not using metric views
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
                    **({"usage_guidance": example_sqls[i]["usage_guidance"]} if "usage_guidance" in example_sqls[i] else {}),
                    **({"parameters": example_sqls[i]["parameters"]} if "parameters" in example_sqls[i] else {}),
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
        "join_specs": sorted(
            [{"id": secrets.token_hex(16), **js} for js in join_specs],
            key=lambda x: x["id"],
        ),
        "sql_functions": sorted(
            [{"id": secrets.token_hex(16), **sf} for sf in sql_functions],
            key=lambda x: x["id"],
        ),
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
