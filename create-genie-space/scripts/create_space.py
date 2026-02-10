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
tables = sorted([
    {"identifier": "catalog.schema.table1"},
    {"identifier": "catalog.schema.table2"},
], key=lambda x: x["identifier"])

# Sample questions for business users
sample_questions_text = [
    "What were total sales last month?",
    "Show me top 10 products by revenue",
]

# Text instructions (domain-specific guidance)
text_instruction_lines = [
    "Revenue = quantity * unit_price.",
    "Fiscal year starts April 1st.",
]

# Example SQL queries (for complex questions)
example_sqls = [
    {
        "question": ["What are total sales by product category?"],
        "sql": [
            "SELECT ",
            "  p.category,",
            "  SUM(o.quantity * o.unit_price) as total_sales",
            "FROM catalog.schema.orders o",
            "JOIN catalog.schema.products p ON o.product_id = p.product_id",
            "GROUP BY p.category",
            "ORDER BY total_sales DESC",
        ],
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

config = {
    "version": 2,
    "config": {
        "sample_questions": [
            {"id": question_ids[i], "question": [sample_questions_text[i]]}
            for i in range(len(sample_questions_text))
        ]
    },
    "data_sources": {
        "tables": tables
    },
    "instructions": {
        "text_instructions": [
            {
                "id": instruction_id,
                "content": text_instruction_lines,
            }
        ],
        "example_question_sqls": [
            {
                "id": example_sql_ids[i],
                "question": example_sqls[i]["question"],
                "sql": example_sqls[i]["sql"],
            }
            for i in range(len(example_sqls))
        ],
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
print(f"Successfully created Genie space!")
print(f"  Space ID: {space_id}")
print(f"  URL: {w.config.host}/genie/rooms/{space_id}")
