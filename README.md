# Prompt to Genie Space

Leveraging [Databricks Assistant agent skills](https://docs.databricks.com/aws/en/assistant/skills) and [custom instructions](https://docs.databricks.com/aws/en/notebooks/assistant-tips#customize-assistant-responses-by-adding-instructions) that enable you to create and manage [AI/BI Genie](https://docs.databricks.com/aws/en/genie/index.html) spaces using natural language — directly from the Databricks Assistant in agent mode.

Instead of manually configuring Genie spaces through the UI or writing raw API calls, simply describe what you want in plain English and let the Assistant handle the rest.

## What's Included

```
prompt-to-genie/
├── .assistant_instructions.md              # Custom user instructions for the Assistant
├── create-genie-space/
│   ├── SKILL.md                            # Skill: Create & manage Genie spaces (workflows)
│   ├── REFERENCE.md                        # Reference: JSON schema, errors, troubleshooting, UI guides
│   └── scripts/
│       ├── discover_resources.py           # List warehouses + audit table metadata quality
│       ├── validate_config.py              # Validate serialized_space JSON before API calls
│       ├── create_space.py                 # Template: create a new Genie space via API
│       └── manage_space.py                 # Retrieve, summarize, and update an existing space
└── examples/
    ├── create-space/
    │   ├── conversation_history.md         # Conversation: creating a new Genie space
    │   └── generated_notebook.ipynb        # Generated notebook from the create session
    └── review-space/
        ├── conversation_history.md          # Conversation: reviewing & improving an existing space
        └── generated_notebook.ipynb         # Generated notebook from the review session
```

### `create-genie-space` Skill

A conversational skill with two modes:

**Create a New Space:**
1. **Gathering requirements (most important)** — deep-dive into business context, terminology, fiscal calendars, filtering conventions, and real user questions
2. **Identifying and profiling data sources** — select Unity Catalog tables, then profile actual columns and values to confirm business term mappings with the user
3. **Defining sample questions** — business-friendly starter questions grounded in confirmed data
4. **Configuring instructions** — SQL expressions, example SQL queries, parameterized queries, UDFs, and text instructions
5. **Discovering resources** — finding serverless SQL warehouses and workspace URLs
6. **Validating and testing** — validate JSON config, test example SQL queries, check formatting
7. **Creating the space** — generating the `serialized_space` JSON and calling the Genie API
8. **Testing and iterating** — self-testing, benchmarking, user testing, and monitoring

**Manage an Existing Space:**
1. **Retrieving configuration** — fetch and parse the current space setup
2. **Auditing against best practices** — evaluate tables, instructions, and metadata quality
3. **Diagnosing issues** — triage specific problems (wrong columns, bad joins, metric errors, etc.)
4. **Recommending optimizations** — suggest improvements, tagged as API or UI changes
5. **Applying updates** — two modes:
   - **Mode A: Assistant applies** — the Assistant modifies config and calls the PATCH API directly
   - **Mode B: Guided walkthrough** — the Assistant walks the user step-by-step through each change in the Genie UI
6. **Benchmarking** — verify improvements with systematic accuracy testing

The skill is split into two files:
- **`SKILL.md`** — The procedural workflows (create and manage). This is what the Assistant loads and follows step by step.
- **`REFERENCE.md`** — Reference material: `serialized_space` JSON schema, error codes, troubleshooting guide, and UI walkthrough templates. Referenced from `SKILL.md` when needed.

### `.assistant_instructions.md`

Custom user instructions that tell the Databricks Assistant to automatically load the `create-genie-space` skill whenever you're working with Genie spaces.

### `examples/`

Real-world examples showing the skill in action:

- **`create-space/`** — End-to-end example of creating a new Genie space from scratch. Includes a conversation transcript showing the requirements gathering, warehouse discovery, table exploration, and space creation flow, plus the generated notebook with all code cells.
- **`review-space/`** — End-to-end example of reviewing and improving an existing Genie space. Includes a conversation transcript showing the audit, column description updates, parameterized query creation, spacing issue detection and fixes, and space recreation, plus the generated notebook with all code cells.

## Getting Started

### Prerequisites

- A Databricks workspace with [AI/BI Genie](https://docs.databricks.com/aws/en/genie/index.html) enabled
- Access to Databricks Assistant in **agent mode**
- A **serverless SQL warehouse** (required for Genie spaces)
- SELECT permissions on the Unity Catalog tables you want to include

### Installation

1. **Copy the skill to your workspace**

   Upload the `create-genie-space/` folder to your user skills directory:

   ```
   /Users/{your-username}/.assistant/skills/create-genie-space/SKILL.md
   ```

   You can create the skills folder by opening the Assistant panel, clicking **Settings**, then clicking **Open skills folder**.

2. **Add the custom instructions**

   Copy the contents of `.assistant_instructions.md` into your user instructions file:

   ```
   /Users/{your-username}/.assistant_instructions.md
   ```

   You can create or open this file from the Assistant panel under **Settings** > **User instructions** > **Add instructions file**.

3. **Start using it**

   Open the Databricks Assistant in agent mode and ask something like:

   > "I want to create a Genie space for our sales team to analyze revenue by product and region."

   The Assistant will automatically load the skill and walk you through the process conversationally.

## Usage Examples

For full end-to-end walkthroughs, see the [`examples/`](examples/) directory — it includes two real sessions: [creating a new space](examples/create-space/) and [reviewing/improving an existing space](examples/review-space/).

### Create a New Genie Space

> **You:** "Create a Genie space for our finance team. The data is in `analytics.finance.transactions` and `analytics.finance.budgets`."
>
> **Assistant:** Gathers details about your use case, suggests sample questions, discovers your warehouse, and creates the space via the API.

### Audit an Existing Space

> **You:** "Can you review my Sales Analytics Genie space and tell me what I should improve?"
>
> **Assistant:** Retrieves the configuration, audits it against best practices, and provides a prioritized list of recommendations (e.g., add parameterized queries, improve column descriptions, reduce table count).

### Diagnose Issues

> **You:** "My Genie space keeps giving wrong answers when users ask about revenue by region."
>
> **Assistant:** Walks through a diagnostic flow — checks column metadata, instructions, example SQL, and join definitions — then identifies the root cause and applies fixes.

### Explore Your Data First

> **You:** "I'm not sure which tables to include. Can you help me explore what's in the `analytics` catalog?"
>
> **Assistant:** Runs catalog exploration queries and helps you pick the right tables.

## How It Works

This project leverages two Databricks Assistant extensibility features:

### Agent Skills

[Skills](https://docs.databricks.com/aws/en/assistant/skills) package domain-specific knowledge and workflows that the Assistant can load when relevant. Unlike custom instructions (which are applied globally), skills are loaded automatically and only in the relevant context. Each skill lives in its own folder under `/Users/{username}/.assistant/skills/` and contains a `SKILL.md` file with frontmatter metadata and markdown instructions.

Skills can include:
- Step-by-step procedural guidance
- Code templates and examples
- Validation checklists and error handling
- References to additional scripts or documentation

### Custom Instructions

[Custom instructions](https://docs.databricks.com/aws/en/notebooks/assistant-tips#customize-assistant-responses-by-adding-instructions) let you provide persistent, system-level context to the Assistant. They are applied to every response the Assistant generates (except Quick Fix and Autocomplete). The `.assistant_instructions.md` file in this repo ensures the Assistant knows to reach for the Genie skill when relevant.

## API Reference

The skill uses the following Databricks REST APIs under the hood:

| Operation | Method | Endpoint |
|-----------|--------|----------|
| List SQL warehouses | `GET` | `/api/2.0/sql/warehouses` |
| Create Genie space | `POST` | `/api/2.0/genie/spaces` |
| Get Genie space | `GET` | `/api/2.0/genie/spaces/{space_id}?include_serialized_space=true` |
| Update Genie space | `PATCH` | `/api/2.0/genie/spaces/{space_id}` |

For full API documentation, see:
- [Genie API Reference](https://docs.databricks.com/api/workspace/genie)
- [Create Genie Space API](https://docs.databricks.com/api/workspace/genie/createspace)

See the [Databricks skill authoring best practices](https://docs.databricks.com/aws/en/assistant/skills#best-practices) for guidance on writing effective skills.
