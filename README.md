# Prompt to Genie Space

A [Databricks Assistant agent skill](https://docs.databricks.com/aws/en/assistant/skills) that lets you create or optimize [AI/BI Genie](https://docs.databricks.com/aws/en/genie/index.html) spaces using natural language — directly from the Databricks Assistant in agent mode. As this skill follows the standard [Agent Skill](https://agentskills.io/specification) format, it is extensible to other agents such as Cursor or Claude Code. It takes only 5 seconds to configure!

Instead of manually configuring Genie spaces through the UI or writing raw API calls, simply describe what you want in plain English and let the Assistant handle the rest.

## Getting Started

### Prerequisites

- A Databricks workspace with [AI/BI Genie](https://docs.databricks.com/aws/en/genie/index.html) enabled
- Access to Databricks Assistant in **agent mode**
- A **pro or serverless SQL warehouse** (serverless recommended for performance)
- SELECT permissions on the Unity Catalog tables you want to include

### Installation

#### Step 1: Clone as a Git folder (one-time setup)

1. In your Databricks workspace, navigate to `/Users/{your-username}/.assistant/skills/`
   - You can open this folder from the Assistant panel: click **Settings** > **Open skills folder**
2. Click **Create** > **Git folder**
3. Paste this repository's URL — the folder will default to **`prompt-to-genie`**, which is the correct skill name

That's it. The skill is now installed at:
```
/Users/{your-username}/.assistant/skills/prompt-to-genie/SKILL.md
```

#### Step 2: Add custom instructions (optional but recommended)

Custom instructions tell the Assistant to automatically load this skill for Genie-related tasks. Open or create your user instructions file at:

```
/Users/{your-username}/.assistant_instructions.md
```

You can find this from the Assistant panel under **Settings** > **User instructions** > **Add instructions file**. Then add the following:

```markdown
## Custom Skills

### Genie Space Management
When working with Databricks AI/BI Genie spaces — creating, managing, auditing, diagnosing issues, or optimizing:
- **Always load first**: `/Users/{username}/.assistant/skills/prompt-to-genie/SKILL.md`
- This contains the most up-to-date API documentation, error codes, best practices, and troubleshooting guidance
- Use the **Create a New Space** workflow when the user wants to build a new Genie space
- Use the **Diagnose and Optimize an Existing Space** workflow when the user wants to review, audit, fix, or optimize an existing space
```

#### Step 3: Start using it with a Databricks Notebook

Open the Databricks Assistant in agent mode with a blank Notebook open and ask something like:

> "I want to create a Genie space for our sales team to analyze revenue by product and region."

The Assistant will automatically load the skill and walk you through the process conversationally. Note that at times, the Assistant may reference its internal documentation instead of the skill, especially for creating the final JSON. Manually prompt the Assistant to reference the schema provided by using `@schema.md`, as the current documentation is outdated.

### Updating

To get the latest version, open the Git folder in your workspace and click **Pull**. No files to re-upload.

## What's Included

```
prompt-to-genie/
├── SKILL.md                           # Main skill file — Create a New Space workflow
├── references/
│   ├── schema.md                      # serialized_space JSON schema, field reference, formatting rules
│   ├── diagnose_optimize_space.md     # Diagnose & Optimize workflow, error codes, troubleshooting
│   └── ui_walkthroughs.md             # Step-by-step UI templates for guided changes
├── scripts/
│   ├── discover_resources.py          # List warehouses + audit table metadata quality
│   ├── validate_config.py             # Validate serialized_space JSON before API calls
│   ├── create_space.py                # Template: create a new Genie space via API
│   └── manage_space.py                # Retrieve, summarize, and update an existing space
└── README.md
```

### Skill Overview

A conversational skill with two workflows:

**Create a New Space** (7 steps): Gather requirements > Identify and profile data sources > Define sample questions > Configure instructions > Generate configuration > Create the space > Test and iterate. See `SKILL.md` for the full workflow.

**Diagnose and Optimize an Existing Space** (6 steps): Retrieve configuration > Audit against best practices > Diagnose issues > Recommend optimizations > Apply updates > Benchmark and verify. See `references/diagnose_optimize_space.md`.

The skill is organized as:
- **`SKILL.md`** — The Create a New Space workflow. This is what the Assistant loads and follows step by step.
- **`references/`** — Reference material the Assistant consults as needed:
  - `schema.md` — `serialized_space` JSON schema, field reference, formatting rules, ID generation
  - `diagnose_optimize_space.md` — Diagnose and Optimize workflow, error codes, troubleshooting patterns
  - `ui_walkthroughs.md` — Step-by-step templates for making changes in the Genie space UI
- **`scripts/`** — Python templates the Assistant adapts and runs in notebook cells
- **`examples/`** — Real conversation transcripts and generated notebooks showing the skill in action

## Usage Examples

For full end-to-end walkthroughs, see the [`examples/`](examples/) directory.

### Create a New Genie Space

> **You:** "Create a Genie space for our finance team. The data is in `analytics.finance.transactions` and `analytics.finance.budgets`."
>
> **Assistant:** Gathers details about your use case, asks about business logic, suggests sample questions, discovers your warehouse, presents a plan for review, and creates the space via the API.

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

This project uses [Databricks Assistant agent skills](https://docs.databricks.com/aws/en/assistant/skills) — packaged domain knowledge and workflows that the Assistant loads automatically when relevant. Each skill lives in its own folder under `/Users/{username}/.assistant/skills/` and contains a `SKILL.md` file with frontmatter metadata and markdown instructions.

Optionally, [custom instructions](https://docs.databricks.com/aws/en/notebooks/assistant-tips#customize-assistant-responses-by-adding-instructions) (the `.assistant_instructions.md` step above) provide persistent, system-level context to the Assistant so it knows to reach for the skill when you mention Genie spaces.

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
