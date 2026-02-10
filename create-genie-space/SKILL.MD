---
name: create-genie-space
description: Guide users through creating Databricks AI/BI Genie spaces using natural language. Helps gather requirements, configure data sources, define sample questions, and generate the space configuration. Use when the user wants to create, build, or set up a new Genie space, or asks about configuring AI/BI dashboards.
---

# Create Genie Space

Guide users through creating a Databricks AI/BI Genie space by gathering requirements conversationally and generating the proper configuration.

## Workflow Overview

1. **Gather Requirements** - Understand the user's data and use case
2. **Identify Data Sources** - Determine which Unity Catalog tables to include
3. **Define Sample Questions** - Create starter questions for business users
4. **Configure Instructions** - Add domain-specific guidance for Genie
5. **Generate Configuration** - Build the serialized_space JSON
6. **Create the Space** - Call the Genie API to create the space
7. **Update the Space (Optional)** - Modify existing space configuration based on user requests

## Step 1: Gather Requirements

Ask the user about:

- [ ] **Purpose**: What business questions should this space answer?
- [ ] **Audience**: Who will use this space? (analysts, executives, etc.)
- [ ] **Data Domain**: What area does the data cover? (sales, finance, operations, etc.)

**Example prompt:**
> "What kind of questions do you want users to be able to ask in this Genie space? For example: sales analytics, customer insights, inventory tracking?"

## Step 2: Identify Data Sources

Determine which Unity Catalog tables to include:

- [ ] **Catalog name**: Which catalog contains the data?
- [ ] **Schema name**: Which schema?
- [ ] **Table names**: Which specific tables?

**Example prompt:**
> "Which Unity Catalog tables should this Genie space have access to? Please provide the full path (catalog.schema.table)."

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

## Step 4: Configure Instructions (Optional)

Add domain-specific instructions to help Genie understand the data better:

- Define business terminology and acronyms
- Specify calculation rules (e.g., "revenue = quantity * unit_price")
- Note important relationships between tables
- Clarify date/time conventions

**Example instructions:**

- "Active customer" means a customer with at least one order in the last 90 days
- Revenue should always be calculated as quantity * unit_price * (1 - discount)
- Fiscal year starts April 1st


## Step 4.5: Discover Available Resources

### Find SQL Warehouses

If the user doesn't know their warehouse ID, help them discover available serverless warehouses:

python
import requests

# Get workspace URL
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()

# Get authentication token
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# List SQL warehouses
response = requests.get(
    f"{workspace_url}/api/2.0/sql/warehouses",
    headers={"Authorization": f"Bearer {token}"}
)

warehouses = response.json().get("warehouses", [])
for wh in warehouses:
    # Filter for serverless warehouses only (required for Genie)
    if wh.get("enable_serverless_compute", False):
        print(f"Name: {wh['name']}, ID: {wh['id']}, State: {wh['state']}")


**Important:** Serverless SQL warehouses are required for Genie spaces. The code above filters to show only serverless warehouses.

### Get Workspace URL

The workspace URL can be obtained programmatically:

python
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
print(f"Workspace URL: {workspace_url}")


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
- `question`: Must be an array of strings. You can include multiple phrasings of the same question:
  - Single phrasing: `["What were total sales last month?"]`
  - Multiple phrasings: `["What were total sales last month?", "Show me last month's sales", "Total sales for previous month"]`
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


### Python Example
python
import json
import requests
import secrets

# Get authentication credentials
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# Generate unique 32-character hex IDs for sample questions and instructions
question_id_1 = secrets.token_hex(16)  # 32 chars
question_id_2 = secrets.token_hex(16)  # 32 chars
instruction_id = secrets.token_hex(16)  # 32 chars

# Sort IDs alphabetically (required by API)
question_ids = sorted([
    (question_id_1, "What were total sales last month?"),
    (question_id_2, "Show me top 10 products by revenue")
])

# Build configuration
config = {
    "version": 2,  # Use version 2 for new spaces
    "config": {
        "sample_questions": [
            {"id": question_ids[0][0], "question": [question_ids[0][1]]},
            {"id": question_ids[1][0], "question": [question_ids[1][1]]}
        ]
    },
    "data_sources": {
        "tables": [
            {"identifier": "sales.gold.customers"},  # Sorted alphabetically
            {"identifier": "sales.gold.orders"}
        ]
    },
    "instructions": {
        "text_instructions": [
            {
                "id": instruction_id,
                "content": [
                    "Revenue = quantity * unit_price. ",
                    "Fiscal year starts April 1st."
                ]
            }
        ]
    }
}

# Create the Genie space
response = requests.post(
    f"{workspace_url}/api/2.0/genie/spaces",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "serialized_space": json.dumps(config),
        "warehouse_id": "your_serverless_warehouse_id",  # Must be a serverless warehouse
        "parent_path": "/Users/your.email@company.com",  # Must exist in workspace
        "title": "Sales Analytics",
        "description": "Analyze sales performance and customer trends"
    }
)

# Handle response
if response.status_code == 200:
    space_data = response.json()
    space_id = space_data.get("space_id")
    print(f"✓ Successfully created Genie space!")
    print(f"  Space ID: {space_id}")
    print(f"  URL: {workspace_url}/genie/rooms/{space_id}")
else:
    print(f"✗ Failed to create space: {response.status_code}")
    print(f"  Error: {response.text}")


**Authentication Notes:**
- `workspace_url`: Automatically retrieved from notebook context (e.g., `https://adb-1234567890.11.azuredatabricks.net`)
- `token`: Automatically retrieved from notebook context (uses your current session)
- For scripts outside notebooks, use a Personal Access Token from User Settings → Developer → Access Tokens

## Step 7: Update the Space (Optional)

After creating a Genie space, you can update its configuration based on user requests. Common updates include:

- Adding or removing tables from data sources
- Adding new sample questions
- Adding example SQL queries to guide Genie's query generation
- Updating instructions with new business rules
- Modifying the space title or description

### When to Update

Use the update API when users request changes like:
- "Add example SQL queries to help Genie understand complex joins"
- "Include the products table in the space"
- "Add more sample questions about customer retention"
- "Update the instructions to clarify our revenue calculation"

### Get Current Space Configuration

First, retrieve the existing space configuration to modify:

python
import requests
import json

# Get authentication credentials
workspace_url = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiUrl().get()
token = dbutils.notebook.entry_point.getDbutils().notebook().getContext().apiToken().get()

# Get space details
space_id = "your_space_id"
response = requests.get(
    f"{workspace_url}/api/2.0/genie/spaces/{space_id}",
    headers={"Authorization": f"Bearer {token}"}
)

if response.status_code == 200:
    space_data = response.json()
    current_config = json.loads(space_data.get("serialized_space", "{}"))
    print("Current configuration retrieved successfully")
else:
    print(f"Failed to get space: {response.status_code}")
    print(response.text)


### Update Space Configuration

Modify the configuration and send an update request:

python
import json
import requests
import secrets

# Modify the configuration (example: adding example SQL queries)
current_config["instructions"] = current_config.get("instructions", {})

# Add example_question_sqls to instructions
example_sql_id = secrets.token_hex(16)
current_config["instructions"]["example_question_sqls"] = [
    {
        "id": example_sql_id,
        "question": ["What are total sales by product category?"],
        "sql": [
            "SELECT ",
            "  p.category,",
            "  SUM(o.quantity * o.unit_price) as total_sales",
            "FROM sales.gold.orders o",
            "JOIN sales.gold.products p ON o.product_id = p.product_id",
            "GROUP BY p.category",
            "ORDER BY total_sales DESC"
        ]
    }
]

# Sort all ID-based collections (required)
if "sample_questions" in current_config.get("config", {}):
    current_config["config"]["sample_questions"] = sorted(
        current_config["config"]["sample_questions"],
        key=lambda x: x["id"]
    )

if "example_question_sqls" in current_config.get("instructions", {}):
    current_config["instructions"]["example_question_sqls"] = sorted(
        current_config["instructions"]["example_question_sqls"],
        key=lambda x: x["id"]
    )

# Update the space
response = requests.patch(
    f"{workspace_url}/api/2.0/genie/spaces/{space_id}",
    headers={"Authorization": f"Bearer {token}"},
    json={
        "serialized_space": json.dumps(current_config)
    }
)

# Handle response
if response.status_code == 200:
    print(f"✓ Successfully updated Genie space!")
    print(f"  Space ID: {space_id}")
    print(f"  URL: {workspace_url}/genie/rooms/{space_id}")
else:
    print(f"✗ Failed to update space: {response.status_code}")
    print(f"  Error: {response.text}")


### Example SQL Query Format

When adding `example_question_sqls` to instructions, each example should include:

- `id`: Unique 32-character hex ID
- `question`: Array of natural language phrasings
- `sql`: Array of strings representing the SQL query (split by lines for readability)

json
{
  "id": "c3d4e5f6a7b80000000000000000000c",
  "question": [
    "What are total sales by product category?",
    "Show me sales broken down by category"
  ],
  "sql": [
    "SELECT ",
    "  p.category,",
    "  SUM(o.quantity * o.unit_price) as total_sales",
    "FROM sales.gold.orders o",
    "JOIN sales.gold.products p ON o.product_id = p.product_id",
    "GROUP BY p.category",
    "ORDER BY total_sales DESC"
  ]
}


**Benefits of Example SQL Queries:**
- Helps Genie understand complex table relationships and joins
- Demonstrates preferred calculation methods
- Improves query generation accuracy for similar questions
- Provides templates for common analytical patterns

### Update API Reference

**Endpoint:** `PATCH /api/2.0/genie/spaces/{space_id}`

**Parameters:**
- `serialized_space`: Updated JSON configuration (required)
- `title`: New title (optional)
- `description`: New description (optional)

**Note:** You cannot change the `warehouse_id` or `parent_path` after creation. To use a different warehouse or location, create a new space.

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

- [ ] At least one valid Unity Catalog table is specified
- [ ] Tables exist and user has SELECT permission
- [ ] Warehouse ID is valid and is a serverless SQL warehouse
- [ ] Parent path exists in workspace
- [ ] Sample questions are business-friendly
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

## Additional Resources

- [Genie API Reference](https://docs.databricks.com/api/workspace/genie)
- [Create Genie Space API](https://docs.databricks.com/api/workspace/genie/createspace)