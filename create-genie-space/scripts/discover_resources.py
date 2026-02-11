"""
Discover and validate resources for Genie space creation.

Part 1: List serverless SQL warehouses and workspace URL.
Part 2: Audit Unity Catalog table metadata for Genie-readiness —
        checks table comments, column descriptions, column counts,
        foreign keys, and generates a quality score with recommendations.

Usage: Run this script in a Databricks notebook cell.
       Set `tables_to_review` to the tables you plan to include in your Genie space.
"""

from databricks.sdk import WorkspaceClient
from pyspark.sql import SparkSession

w = WorkspaceClient()
spark = SparkSession.builder.getOrCreate()

# =====================================================================
# PART 1: DISCOVER SQL WAREHOUSES
# =====================================================================

print("=" * 70)
print("PART 1: SQL WAREHOUSES")
print("=" * 70)
print(f"\nWorkspace URL: {w.config.host}\n")

warehouses = list(w.warehouses.list())
serverless_warehouses = [
    wh for wh in warehouses
    if wh.enable_serverless_compute
]

if serverless_warehouses:
    print(f"Found {len(serverless_warehouses)} serverless SQL warehouse(s):\n")
    for wh in serverless_warehouses:
        print(f"  Name: {wh.name}")
        print(f"  ID:   {wh.id}")
        print(f"  State: {wh.state}")
        print(f"  Size: {wh.cluster_size or 'N/A'}")
        print(f"  {'─' * 50}")
else:
    print("No serverless SQL warehouses found.")
    print("Note: Genie spaces require a serverless SQL warehouse.")
    print("You may need to create one in the SQL Warehouses UI.")


# =====================================================================
# PART 2: REVIEW TABLE METADATA (Genie-readiness audit)
# =====================================================================

# --- CONFIGURE THESE VALUES ---

tables_to_review = [
    "catalog.schema.table1",
    "catalog.schema.table2",
]


def review_table(table_identifier: str) -> dict:
    """Review a single table's metadata quality for Genie readiness."""
    result = {
        "table": table_identifier,
        "exists": False,
        "table_comment": None,
        "total_columns": 0,
        "columns_with_description": 0,
        "columns_missing_description": [],
        "columns": [],
        "foreign_keys": [],
        "quality_score": 0.0,
        "recommendations": [],
    }

    # Check table exists and get metadata
    try:
        table_info = spark.sql(f"DESCRIBE TABLE EXTENDED {table_identifier}").collect()
    except Exception as e:
        result["recommendations"].append(f"ERROR: Cannot access table — {e}")
        return result

    result["exists"] = True

    # Parse column info and table properties
    in_detail_section = False
    columns = []
    for row in table_info:
        col_name = row["col_name"].strip() if row["col_name"] else ""
        data_type = row["data_type"].strip() if row["data_type"] else ""
        comment = row["comment"].strip() if row["comment"] else ""

        if col_name == "" and data_type == "" and comment == "":
            in_detail_section = True
            continue
        if col_name.startswith("#"):
            in_detail_section = True
            continue

        if not in_detail_section:
            columns.append({
                "name": col_name,
                "type": data_type,
                "description": comment if comment else None,
            })
        else:
            if col_name.lower() == "comment":
                result["table_comment"] = data_type if data_type else None

    result["total_columns"] = len(columns)
    result["columns"] = columns
    result["columns_with_description"] = sum(1 for c in columns if c["description"])
    result["columns_missing_description"] = [
        c["name"] for c in columns if not c["description"]
    ]

    # Check foreign key constraints
    try:
        constraints = spark.sql(
            f"SHOW CONSTRAINTS ON {table_identifier}"
        ).collect()
        for constraint in constraints:
            constraint_dict = constraint.asDict()
            if constraint_dict.get("constraint_type", "").upper() == "FOREIGN_KEY":
                result["foreign_keys"].append(constraint_dict)
    except Exception:
        pass

    # Calculate quality score (0-100)
    score = 0
    total_weight = 0

    # Table comment (20 points)
    total_weight += 20
    if result["table_comment"]:
        score += 20
    else:
        result["recommendations"].append(
            f"Add a table comment: COMMENT ON TABLE {table_identifier} IS '<description>'"
        )

    # Column descriptions (60 points, proportional)
    total_weight += 60
    if result["total_columns"] > 0:
        desc_ratio = result["columns_with_description"] / result["total_columns"]
        score += int(60 * desc_ratio)
        if desc_ratio < 1.0:
            missing = result["columns_missing_description"]
            if len(missing) <= 5:
                for col in missing:
                    result["recommendations"].append(
                        f"Add column description: COMMENT ON COLUMN {table_identifier}.{col} IS '<description>'"
                    )
            else:
                result["recommendations"].append(
                    f"{len(missing)} columns missing descriptions: {', '.join(missing[:5])}... and {len(missing) - 5} more"
                )

    # Column count (10 points)
    total_weight += 10
    if result["total_columns"] <= 30:
        score += 10
    elif result["total_columns"] <= 50:
        score += 5
        result["recommendations"].append(
            f"Table has {result['total_columns']} columns — consider hiding irrelevant ones in the Genie space"
        )
    else:
        result["recommendations"].append(
            f"Table has {result['total_columns']} columns — strongly recommend creating a focused view"
        )

    # Foreign keys (10 points)
    total_weight += 10
    if result["foreign_keys"]:
        score += 10

    result["quality_score"] = round((score / total_weight) * 100, 1) if total_weight > 0 else 0
    return result


# --- RUN TABLE REVIEW ---

print(f"\n\n{'=' * 70}")
print("PART 2: TABLE METADATA REVIEW")
print("Auditing Genie-readiness for table descriptions and column metadata")
print("=" * 70)

all_results = []
for table in tables_to_review:
    review = review_table(table)
    all_results.append(review)

    print(f"\n{'─' * 70}")
    print(f"TABLE: {review['table']}")
    print(f"{'─' * 70}")

    if not review["exists"]:
        print(f"  ✗ Table not accessible")
        for rec in review["recommendations"]:
            print(f"    {rec}")
        continue

    # Table comment
    if review["table_comment"]:
        print(f"  ✓ Table comment: {review['table_comment'][:100]}{'...' if len(review['table_comment']) > 100 else ''}")
    else:
        print(f"  ✗ Table comment: MISSING")

    # Column summary
    total = review["total_columns"]
    described = review["columns_with_description"]
    print(f"  {'✓' if described == total else '✗'} Columns: {described}/{total} have descriptions")

    # Foreign keys
    if review["foreign_keys"]:
        print(f"  ✓ Foreign keys: {len(review['foreign_keys'])} defined")
    else:
        print(f"  ○ Foreign keys: None (can define in Genie knowledge store)")

    # Quality score
    score = review["quality_score"]
    grade = "Excellent" if score >= 90 else "Good" if score >= 70 else "Fair" if score >= 50 else "Needs work"
    print(f"\n  Quality Score: {score}/100 ({grade})")

    # Recommendations
    if review["recommendations"]:
        print(f"\n  Recommendations:")
        for rec in review["recommendations"]:
            print(f"    → {rec}")

    # Column detail table
    if review["columns"]:
        print(f"\n  {'Column':<30} {'Type':<15} {'Description'}")
        print(f"  {'─' * 30} {'─' * 15} {'─' * 40}")
        for col in review["columns"]:
            desc = col["description"] or "—"
            if len(desc) > 40:
                desc = desc[:37] + "..."
            print(f"  {col['name']:<30} {col['type']:<15} {desc}")

# --- SUMMARY ---

print(f"\n{'=' * 70}")
print("SUMMARY")
print(f"{'=' * 70}")
accessible = [r for r in all_results if r["exists"]]
if accessible:
    total_cols = sum(r["total_columns"] for r in accessible)
    described_cols = sum(r["columns_with_description"] for r in accessible)
    avg_score = sum(r["quality_score"] for r in accessible) / len(accessible)

    print(f"  Tables reviewed: {len(accessible)}/{len(tables_to_review)}")
    print(f"  Total columns: {total_cols}")
    print(f"  Columns with descriptions: {described_cols}/{total_cols} ({round(described_cols / total_cols * 100, 1) if total_cols > 0 else 0}%)")
    print(f"  Average quality score: {round(avg_score, 1)}/100")

    if avg_score >= 80:
        print(f"\n  Tables are well-annotated and ready for a Genie space.")
    elif avg_score >= 50:
        print(f"\n  Tables are usable but would benefit from better annotations.")
        print(f"  Adding column descriptions will significantly improve Genie accuracy.")
    else:
        print(f"\n  Tables need more annotation before use in a Genie space.")
        print(f"  Strongly recommend adding table comments and column descriptions first.")
else:
    print(f"  No tables were accessible. Check permissions and table identifiers.")


# =====================================================================
# PART 3: PROFILE KEY COLUMNS
# =====================================================================
# Profile string/category columns and date ranges to help write accurate
# SQL expressions, filters, and example queries.
#
# This is OPTIONAL but strongly recommended before generating SQL.
# Helps avoid common errors like referencing non-existent column values.

# Set to True to enable profiling
enable_profiling = False

# Max distinct values to show per column (for string/category columns)
max_distinct_values = 20

# Column types to profile for distinct values
CATEGORICAL_TYPES = {"string", "varchar", "char", "boolean"}
DATE_TYPES = {"date", "timestamp", "timestamp_ntz"}

if enable_profiling and accessible:
    print(f"\n\n{'=' * 70}")
    print("PART 3: COLUMN VALUE PROFILING")
    print("Inspecting actual data values to inform SQL generation")
    print("=" * 70)

    for result in accessible:
        table_id = result["table"]
        print(f"\n{'─' * 70}")
        print(f"TABLE: {table_id}")
        print(f"{'─' * 70}")

        for col in result["columns"]:
            col_name = col["name"]
            col_type = col["type"].lower().split("<")[0].split("(")[0].strip()

            if col_type in CATEGORICAL_TYPES:
                try:
                    rows = spark.sql(
                        f"SELECT DISTINCT `{col_name}` FROM {table_id} "
                        f"WHERE `{col_name}` IS NOT NULL "
                        f"ORDER BY `{col_name}` LIMIT {max_distinct_values + 1}"
                    ).collect()
                    values = [str(r[0]) for r in rows]
                    if len(values) > max_distinct_values:
                        print(f"  {col_name} ({col_type}): {max_distinct_values}+ distinct values — {', '.join(values[:10])}...")
                    elif values:
                        print(f"  {col_name} ({col_type}): {', '.join(values)}")
                    else:
                        print(f"  {col_name} ({col_type}): (all NULL)")
                except Exception as e:
                    print(f"  {col_name} ({col_type}): Error — {e}")

            elif col_type in DATE_TYPES:
                try:
                    row = spark.sql(
                        f"SELECT MIN(`{col_name}`) AS min_val, MAX(`{col_name}`) AS max_val "
                        f"FROM {table_id}"
                    ).collect()[0]
                    print(f"  {col_name} ({col_type}): {row['min_val']} to {row['max_val']}")
                except Exception as e:
                    print(f"  {col_name} ({col_type}): Error — {e}")

    print(f"\n  Tip: Use these values to write accurate filters and SQL expressions.")
    print(f"  Ask the user about domain conventions (fiscal calendar, abbreviations, etc.).")
