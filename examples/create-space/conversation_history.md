# Example Conversation: Creating a Vaccine Analytics Genie Space

This is a real conversation between a user and the Databricks Assistant (in agent mode) using the `create-genie-space` skill.

---

**User:**

> I want to create a Genie space

**Assistant:**

I'll help you create a Genie space. Let me first gather the necessary context from the skill documentation.

I've created a guide to help us build your Genie space. To get started, I need to gather some information from you:

1. **Purpose & Audience:**
   - What kind of business questions should users be able to ask in this space? (e.g., sales performance, customer behavior, operational metrics)
   - Who will be using this space?
   - What data domain does this cover?

2. **Data Sources:**
   - Which Unity Catalog tables should this Genie space have access to? Please provide the full paths (`catalog.schema.table`)
   - If you're not sure which tables you have, I can help you discover them

3. **Configuration:**
   - Do you know your serverless SQL warehouse ID? (If not, I can help you find one)
   - What title and description would you like for the space?

Once you provide this information, I'll generate the configuration and create the Genie space for you!

---

**User:**

> I don't know my SQL warehouse ID.

**Assistant:**

No problem! Let me help you discover your available serverless SQL warehouses.

I found 5 serverless SQL warehouses in your workspace:

| Name | ID | Size | State |
|------|----|------|-------|
| Shared Endpoint | `XXXXXX` | Large | RUNNING |
| Starter Warehouse | `XXXXXX` | Medium | RUNNING |
| Testing-wh | `XXXXXX` | 2X-Small | STOPPED |
| cleanup-auto-created-warehouse | `XXXXXX` | 2X-Small | STOPPED |
| dev-warehouse | `XXXXXX` | Small | STOPPED |

I'd recommend using one of the running warehouses like **Shared Endpoint** for immediate availability.

Now, to complete the Genie space setup, please provide:

1. Which warehouse would you like to use? (You can just tell me the name or ID)
2. What business questions should this space answer?
3. Which Unity Catalog tables should be included? (`catalog.schema.table` format)
4. What title and description would you like for the space?
---

**User:**

> Let's use Shared Endpoint.
>
> Create the 5 business questions based on your understanding of the metadata. Make sure to include them in the sample SQL queries.
>
> For Unity Catalog tables, review tables in `users.sean_zhang`.
>
> The title will be Vaccine Analytics. You can create a description based on your best understanding of the metadata.

**Assistant:**

Let me explore the tables in `users.sean_zhang` to see what data is available, then create the Genie space with vaccine analytics questions.

I can see you have a comprehensive vaccine supply chain dataset. Now let me create the Genie space with 5 business questions and corresponding SQL examples.

I've successfully created your **Vaccine Analytics** Genie space!

### Space Details

- **Space ID:** `<your-space-id>`
- **Warehouse:** Shared Endpoint
- **Access URL:** [Open Vaccine Analytics Space](https://<your-workspace-url>/genie/rooms/<your-space-id>)

### What's Included

**5 Sample Questions** covering key vaccine analytics topics:
1. Countries with lowest vaccine availability and highest stockout rates
2. Immunization coverage gaps by country and antigen
3. Products and sites with inventory stockout risks
4. Manufacturing performance by product and site
5. Vaccine supply pricing and volume by country and supplier

**5 Example SQL Queries** to guide Genie's query generation for complex joins and calculations

**9 Data Tables** from the vaccine supply chain:
- Dimension tables (products, sites)
- Fact tables (country supply, inventory, production/shipment)
- View tables (availability, coverage, inventory health, manufacturing status)

**Domain Instructions** explaining key metrics like coverage gaps, OTIF targets, and stockout risk thresholds

You can now start asking natural language questions about your vaccine supply chain data!
