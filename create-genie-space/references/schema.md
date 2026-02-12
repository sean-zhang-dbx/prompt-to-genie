# serialized_space JSON Schema

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
      {
        "identifier": "catalog.schema.orders",
        "description": ["Daily sales transactions with line-item details"],
        "column_configs": [
          {
            "id": "aa11bb22cc330000000000000000000a",
            "column_name": "region",
            "description": ["Sales region code: AMER, EMEA, APJ, LATAM"],
            "synonyms": ["area", "territory", "sales region"],
            "enable_entity_matching": true,
            "enable_format_assistance": true
          },
          {
            "id": "aa11bb22cc330000000000000000000b",
            "column_name": "etl_timestamp",
            "exclude": true
          }
        ]
      },
      {"identifier": "catalog.schema.products"}
    ],
    "metric_views": [
      {"identifier": "catalog.schema.revenue_metrics", "description": ["Revenue metrics"]}
    ]
  },
  "instructions": {
    "text_instructions": [
      {
        "id": "b2c3d4e5f6a70000000000000000000b",
        "content": ["Revenue = quantity * unit_price.", "Fiscal year starts April 1st."]
      }
    ],
    "example_question_sqls": [
      {
        "id": "c3d4e5f6a7b80000000000000000000c",
        "question": ["Show top 10 customers by revenue"],
        "sql": ["SELECT\n", "  customer_name,\n", "  SUM(amount) as total\n", "FROM catalog.schema.orders\n", "GROUP BY customer_name\n", "ORDER BY total DESC\n", "LIMIT 10"],
        "usage_guidance": ["Use this pattern for any top-N ranking question by a numeric metric"]
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
        "left": {"identifier": "catalog.schema.orders", "alias": "o"},
        "right": {"identifier": "catalog.schema.customers", "alias": "c"},
        "join_type": "LEFT JOIN",
        "sql": ["o.customer_id = c.customer_id"],
        "comment": ["Link orders to customer details; LEFT JOIN includes orders with unknown customers"],
        "instruction": ["Always use this join when relating orders to customer demographics"]
      }
    ],
    "sql_snippets": {
      "filters": [
        {
          "id": "f6a7b8c9d0e10000000000000000000f",
          "display_name": "high value",
          "sql": ["amount > 1000"],
          "synonyms": ["big deal", "large order"],
          "instruction": ["Apply when users ask about high-value or large orders"],
          "comment": ["Threshold aligned with finance team's definition"]
        }
      ],
      "expressions": [
        {
          "id": "a7b8c9d0e1f20000000000000000000a",
          "alias": "order_year",
          "display_name": "Order Year",
          "sql": ["YEAR(order_date)"],
          "synonyms": ["year"],
          "instruction": ["Use for any year-based grouping of orders"]
        }
      ],
      "measures": [
        {
          "id": "b8c9d0e1f2a30000000000000000000b",
          "alias": "total_revenue",
          "display_name": "Total Revenue",
          "sql": ["SUM(amount)"],
          "synonyms": ["revenue", "sales", "total sales"],
          "instruction": ["Use for any revenue aggregation"],
          "comment": ["Revenue includes all non-cancelled order line items"]
        }
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

---

## Field Reference

### config

| Field | Type | Description |
|-------|------|-------------|
| `config.sample_questions[].id` | string | 32-char lowercase hex ID |
| `config.sample_questions[].question` | string[] | Single question string per entry |

### data_sources

| Field | Type | Description |
|-------|------|-------------|
| `data_sources.tables[].identifier` | string | Fully qualified table name (`catalog.schema.table`) |
| `data_sources.tables[].description` | string[] | Space-scoped description override (optional) |
| `data_sources.tables[].column_configs[]` | array | Per-column configuration (optional — set via API or manage flow) |
| `data_sources.tables[].column_configs[].id` | string | 32-char lowercase hex ID |
| `data_sources.tables[].column_configs[].column_name` | string | Column name |
| `data_sources.tables[].column_configs[].description` | string[] | Contextual description beyond the column name |
| `data_sources.tables[].column_configs[].synonyms` | string[] | Alternative names users might use for this column |
| `data_sources.tables[].column_configs[].exclude` | boolean | Hide this column from Genie (default: false) |
| `data_sources.tables[].column_configs[].enable_entity_matching` | boolean | **(v2 only)** Match user terms to column values (e.g., "California" → "CA") |
| `data_sources.tables[].column_configs[].enable_format_assistance` | boolean | **(v2 only)** Fetch sample values to help Genie understand data distribution |
| `data_sources.metric_views[].identifier` | string | Fully qualified metric view name |
| `data_sources.metric_views[].description` | string[] | What the metric view computes |

> **v1 vs v2:** Spaces with `"version": 2` reject v1 fields (`get_example_values`, `build_value_dictionary`). Use the v2 equivalents (`enable_format_assistance`, `enable_entity_matching`) instead. Including v1 fields in a v2 space will cause API errors.

### instructions

| Field | Type | Description |
|-------|------|-------------|
| `instructions.text_instructions[].id` | string | 32-char hex ID |
| `instructions.text_instructions[].content` | string[] | Instruction text segments. Max 1 text instruction per space. |
| `instructions.example_question_sqls[].id` | string | 32-char hex ID |
| `instructions.example_question_sqls[].question` | string[] | Single natural language question |
| `instructions.example_question_sqls[].sql` | string[] | SQL query split by lines with `\n` |
| `instructions.example_question_sqls[].usage_guidance` | string[] | When Genie should apply this pattern (optional but recommended) |
| `instructions.example_question_sqls[].parameters` | array | Parameterized values (optional). Each has `name`, `description`, `type_hint`, `default_value`. |
| `instructions.sql_functions[].id` | string | 32-char hex ID |
| `instructions.sql_functions[].identifier` | string | Fully qualified UDF name |
| `instructions.join_specs[].id` | string | 32-char hex ID |
| `instructions.join_specs[].left` | object | Left table: `identifier` (required), `alias` (optional) |
| `instructions.join_specs[].right` | object | Right table: `identifier` (required), `alias` (optional) |
| `instructions.join_specs[].join_type` | string | Join type: `INNER JOIN`, `LEFT JOIN`, etc. (optional) |
| `instructions.join_specs[].sql` | string[] | Join condition. Each element must be a **single equality** (e.g., `"t1.col = t2.col"`). For multi-column joins, use separate join specs. |
| `instructions.join_specs[].comment` | string[] | Business context for the relationship (optional) |
| `instructions.join_specs[].instruction` | string[] | Guidance on when to use this join (optional) |

### sql_snippets (shared fields)

All three snippet types (`filters`, `expressions`, `measures`) support these optional fields in addition to their required ones:

| Field | Type | Description |
|-------|------|-------------|
| `synonyms` | string[] | Alternative terms that trigger this snippet |
| `instruction` | string[] | When Genie should apply this snippet |
| `comment` | string[] | Additional context or notes |
| `display_name` | string | Human-readable name (required for filters, optional for measures/expressions) |

**Type-specific required fields:**

| Type | Required Fields |
|------|----------------|
| `sql_snippets.filters[]` | `id`, `sql`, `display_name` |
| `sql_snippets.expressions[]` | `id`, `sql`, `alias` |
| `sql_snippets.measures[]` | `id`, `sql`, `alias` |

### benchmarks

| Field | Type | Description |
|-------|------|-------------|
| `benchmarks.questions[].id` | string | 32-char hex ID (must be unique across `sample_questions` and `benchmarks.questions`) |
| `benchmarks.questions[].question` | string[] | Test question |
| `benchmarks.questions[].answer` | array | Expected answers. Find `format: "SQL"` for SQL benchmarks. |
| `benchmarks.questions[].answer[].format` | string | Answer format (typically `"SQL"`) |
| `benchmarks.questions[].answer[].content` | string[] | Expected SQL query segments |

---

## Important Notes

- `version`: **Required**. Use `2` for new spaces
- `question`: Must be an array with a **single question string** per entry
- `sql` (in `example_question_sqls`): Must be an array of strings. **Each SQL clause should be a separate element** with `\n` at the end:
  - Correct: `["SELECT\n", "  col1,\n", "  col2\n", "FROM table\n", "WHERE col1 > 0"]`
  - Wrong: `["SELECT col1, col2FROM tableWHERE col1 > 0"]`
- **ID Format**: All IDs must be exactly 32 lowercase hexadecimal characters (no hyphens)
- **Sorting**: All arrays of objects with `id` fields must be sorted alphabetically by `id`. Tables must be sorted by `identifier`.
- **Include only what's needed**: Omit sections that don't apply (e.g., skip `metric_views` if none, skip `benchmarks` if not creating them yet)
- **Join spec constraints**: Each `sql` element must be a single equality expression. For multi-column joins, create separate join specs with `comment`/`instruction` fields indicating they should be used together.
- **column_configs**: Usually set post-creation via the manage flow or UI. For initial creation, column descriptions and synonyms can be added via `column_configs` in the API, or later through the Genie space UI.

---

## ID Generation

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
