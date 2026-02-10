# Prompt to Genie

Leveraging [Databricks Assistant agent skills](https://docs.databricks.com/aws/en/assistant/skills) and [custom instructions](https://docs.databricks.com/aws/en/notebooks/assistant-tips#customize-assistant-responses-by-adding-instructions) that enable you to create and manage [AI/BI Genie](https://docs.databricks.com/aws/en/genie/index.html) spaces using natural language — directly from the Databricks Assistant in agent mode.

Instead of manually configuring Genie spaces through the UI or writing raw API calls, simply describe what you want in plain English and let the Assistant handle the rest.

## What's Included

```
prompt-to-genie/
├── .assistant_instructions.md              # Custom user instructions for the Assistant
└── create-genie-space/
    └── SKILL.MD                            # Skill: Create & update Genie spaces via conversation
```

### `create-genie-space` Skill

A step-by-step conversational skill that guides you through:

1. **Gathering requirements** — purpose, audience, and data domain
2. **Identifying data sources** — Unity Catalog tables to include
3. **Defining sample questions** — business-friendly starter questions for end users
4. **Configuring instructions** — domain-specific rules, terminology, and calculation logic
5. **Discovering resources** — finding serverless SQL warehouses and workspace URLs
6. **Creating the space** — generating the `serialized_space` JSON and calling the Genie API
7. **Updating the space** — modifying tables, questions, instructions, or example SQL queries on an existing space

### `.assistant_instructions.md`

Custom user instructions that tell the Databricks Assistant to automatically load the `create-genie-space` skill whenever you're working with Genie spaces.
`
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
   /Users/{your-username}/.assistant/skills/create-genie-space/SKILL.MD
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

### Create a New Genie Space

> **You:** "Create a Genie space for our finance team. The data is in `analytics.finance.transactions` and `analytics.finance.budgets`."
>
> **Assistant:** Gathers details about your use case, suggests sample questions, discovers your warehouse, and creates the space via the API.

### Update an Existing Space

> **You:** "Add example SQL queries to my Sales Analytics Genie space to help it understand complex joins."
>
> **Assistant:** Retrieves the current configuration, adds the example queries, and updates the space.

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
| Get Genie space | `GET` | `/api/2.0/genie/spaces/{space_id}` |
| Update Genie space | `PATCH` | `/api/2.0/genie/spaces/{space_id}` |

For full API documentation, see:
- [Genie API Reference](https://docs.databricks.com/api/workspace/genie)
- [Create Genie Space API](https://docs.databricks.com/api/workspace/genie/createspace)

See the [Databricks skill authoring best practices](https://docs.databricks.com/aws/en/assistant/skills#best-practices) for guidance on writing effective skills.
