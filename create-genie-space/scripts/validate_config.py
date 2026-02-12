"""
Validate a Genie space serialized_space JSON configuration.

Checks all validation rules enforced by the API:
  - Version field
  - ID format (32-char lowercase hex)
  - Sorting requirements (all collections sorted by key)
  - Uniqueness constraints (no duplicate IDs)
  - Table identifier format (catalog.schema.table)
  - Text instruction limit (max 1)
  - String length limits (25,000 chars)
  - Array size limits (10,000 items)
  - Required fields and structure

Usage: Run this in a Databricks notebook cell.
       Set `config` to your serialized_space dict (parsed JSON, not a string).
       Or set `config_json_string` to your raw JSON string.
"""

import json
import re

# --- CONFIGURE: paste your config here ---

# Option A: Provide the dict directly
config = None

# Option B: Provide a JSON string (e.g., copied from an API response)
config_json_string = None

# Option C: Read from an existing Genie space (uncomment below)
# from databricks.sdk import WorkspaceClient
# w = WorkspaceClient()
# space_id = "your_space_id"
# resp = w.api_client.do(
#     "GET",
#     f"/api/2.0/genie/spaces/{space_id}",
#     query={"include_serialized_space": "true"},
# )
# config = json.loads(resp.get("serialized_space", "{}"))


# =====================================================================
# VALIDATION LOGIC
# =====================================================================

ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
TABLE_ID_PATTERN = re.compile(r"^[^.]+\.[^.]+\.[^.]+$")

MAX_STRING_LENGTH = 25_000
MAX_ARRAY_SIZE = 10_000


def validate_config(config: dict) -> list[dict]:
    """
    Validate a serialized_space config dict.

    Returns a list of issue dicts: {"level": "error"|"warning", "path": str, "message": str}
    Errors will cause API rejection. Warnings are best-practice recommendations.
    """
    issues = []

    def error(path, msg):
        issues.append({"level": "error", "path": path, "message": msg})

    def warning(path, msg):
        issues.append({"level": "warning", "path": path, "message": msg})

    # --- Version ---
    version = config.get("version")
    if version is None:
        error("version", "Missing required 'version' field. Use 2 for new spaces.")
    elif version not in (1, 2):
        warning("version", f"Version is {version}. Recommended value is 2.")

    # --- Helper: validate ID ---
    def check_id(path, id_val):
        if not isinstance(id_val, str):
            error(path, f"ID must be a string, got {type(id_val).__name__}")
            return False
        if not ID_PATTERN.match(id_val):
            error(path, f"ID '{id_val}' is not a valid 32-character lowercase hex string")
            return False
        return True

    # --- Helper: validate sorting ---
    def check_sorted(path, items, key_fn, key_name):
        keys = [key_fn(item) for item in items]
        for i in range(1, len(keys)):
            if keys[i] < keys[i - 1]:
                error(path, f"Array must be sorted by '{key_name}'. '{keys[i]}' comes after '{keys[i-1]}' but should come before it.")
                return False
        return True

    # --- Helper: validate string length ---
    def check_string_length(path, val):
        if isinstance(val, str) and len(val) > MAX_STRING_LENGTH:
            error(path, f"String exceeds {MAX_STRING_LENGTH} character limit (length: {len(val)})")

    # --- Helper: validate array size ---
    def check_array_size(path, arr):
        if len(arr) > MAX_ARRAY_SIZE:
            error(path, f"Array exceeds {MAX_ARRAY_SIZE} item limit (size: {len(arr)})")

    # --- Helper: validate string arrays ---
    def check_string_array(path, arr):
        if not isinstance(arr, list):
            error(path, f"Expected array, got {type(arr).__name__}")
            return
        for i, item in enumerate(arr):
            if not isinstance(item, str):
                error(f"{path}[{i}]", f"Expected string, got {type(item).__name__}")
            else:
                check_string_length(f"{path}[{i}]", item)

    # Collect all IDs for uniqueness checks
    question_and_benchmark_ids = []
    instruction_ids = []

    # --- config.sample_questions ---
    sample_questions = config.get("config", {}).get("sample_questions", [])
    if sample_questions:
        check_array_size("config.sample_questions", sample_questions)
        check_sorted("config.sample_questions", sample_questions, lambda x: x.get("id", ""), "id")
        for i, sq in enumerate(sample_questions):
            p = f"config.sample_questions[{i}]"
            sid = sq.get("id")
            if sid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", sid)
                question_and_benchmark_ids.append((sid, p))
            q = sq.get("question")
            if q is None:
                error(f"{p}.question", "Missing required 'question' field")
            elif not isinstance(q, list) or len(q) == 0:
                error(f"{p}.question", "Must be a non-empty array of strings")
            else:
                check_string_array(f"{p}.question", q)
    else:
        warning("config.sample_questions", "No sample questions defined. Recommend adding 3-5 starter questions.")

    # --- data_sources.tables ---
    tables = config.get("data_sources", {}).get("tables", [])
    if tables:
        check_array_size("data_sources.tables", tables)
        check_sorted("data_sources.tables", tables, lambda x: x.get("identifier", ""), "identifier")
        for i, tbl in enumerate(tables):
            p = f"data_sources.tables[{i}]"
            ident = tbl.get("identifier")
            if ident is None:
                error(f"{p}.identifier", "Missing required 'identifier' field")
            elif not TABLE_ID_PATTERN.match(ident):
                error(f"{p}.identifier", f"'{ident}' must be three-level namespace: catalog.schema.table")
            # Check column_configs sorting and prompt matching consistency
            col_configs = tbl.get("column_configs", [])
            if col_configs:
                check_sorted(f"{p}.column_configs", col_configs, lambda x: x.get("column_name", ""), "column_name")
                for j, cc in enumerate(col_configs):
                    cp = f"{p}.column_configs[{j}]"
                    col_name = cc.get("column_name", f"index {j}")
                    # Entity matching requires format assistance
                    if cc.get("enable_entity_matching") and not cc.get("enable_format_assistance"):
                        error(cp, f"Column '{col_name}' has enable_entity_matching=true but enable_format_assistance is not true. Entity matching requires format assistance to be enabled.")
                    # Warn if excluded column has prompt matching on
                    if cc.get("exclude") and (cc.get("enable_entity_matching") or cc.get("enable_format_assistance")):
                        warning(cp, f"Column '{col_name}' is excluded but has prompt matching enabled. Consider disabling enable_entity_matching and enable_format_assistance on excluded columns.")
        if len(tables) > 25:
            warning("data_sources.tables", f"Space has {len(tables)} tables (max 25). Recommend ≤5 for best accuracy.")
        elif len(tables) > 5:
            warning("data_sources.tables", f"Space has {len(tables)} tables. Recommend ≤5 for best accuracy.")
    else:
        error("data_sources.tables", "No tables defined. At least one table is required.")

    # --- data_sources.metric_views ---
    metric_views = config.get("data_sources", {}).get("metric_views", [])
    if metric_views:
        check_array_size("data_sources.metric_views", metric_views)
        check_sorted("data_sources.metric_views", metric_views, lambda x: x.get("identifier", ""), "identifier")
        for i, mv in enumerate(metric_views):
            p = f"data_sources.metric_views[{i}]"
            ident = mv.get("identifier")
            if ident is None:
                error(f"{p}.identifier", "Missing required 'identifier' field")
            elif not TABLE_ID_PATTERN.match(ident):
                error(f"{p}.identifier", f"'{ident}' must be three-level namespace: catalog.schema.metric_view")
            col_configs = mv.get("column_configs", [])
            if col_configs:
                check_sorted(f"{p}.column_configs", col_configs, lambda x: x.get("column_name", ""), "column_name")

    # --- instructions ---
    instructions = config.get("instructions", {})

    # text_instructions (max 1)
    text_instr = instructions.get("text_instructions", [])
    if text_instr:
        if len(text_instr) > 1:
            error("instructions.text_instructions", f"At most 1 text instruction allowed, found {len(text_instr)}")
        check_sorted("instructions.text_instructions", text_instr, lambda x: x.get("id", ""), "id")
        for i, ti in enumerate(text_instr):
            p = f"instructions.text_instructions[{i}]"
            tid = ti.get("id")
            if tid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", tid)
                instruction_ids.append((tid, p))
            content = ti.get("content")
            if content is None:
                error(f"{p}.content", "Missing required 'content' field")
            elif not isinstance(content, list) or len(content) == 0:
                error(f"{p}.content", "Must be a non-empty array of strings")
            else:
                check_string_array(f"{p}.content", content)
                # Check for placeholder/stale text patterns in instructions
                full_text = " ".join(content).lower()
                stale_patterns = [
                    ("todo", "Contains TODO marker — may be a draft instruction"),
                    ("fixme", "Contains FIXME marker — may be incomplete"),
                    ("placeholder", "Contains 'placeholder' — may not be finalized"),
                    ("change this", "Contains 'change this' — may be a template reminder"),
                    ("update this", "Contains 'update this' — may be a template reminder"),
                    ("# comment", "Contains comment syntax — should be plain text instructions"),
                    ("//", "Contains comment syntax — should be plain text instructions"),
                ]
                for pattern, msg in stale_patterns:
                    if pattern in full_text:
                        warning(f"{p}.content", msg)

    # example_question_sqls
    example_sqls = instructions.get("example_question_sqls", [])
    if example_sqls:
        check_array_size("instructions.example_question_sqls", example_sqls)
        check_sorted("instructions.example_question_sqls", example_sqls, lambda x: x.get("id", ""), "id")
        for i, eq in enumerate(example_sqls):
            p = f"instructions.example_question_sqls[{i}]"
            eid = eq.get("id")
            if eid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", eid)
                instruction_ids.append((eid, p))
            q = eq.get("question")
            if q is None:
                error(f"{p}.question", "Missing required 'question' field")
            else:
                check_string_array(f"{p}.question", q)
            sql = eq.get("sql")
            if sql is None:
                error(f"{p}.sql", "Missing required 'sql' field")
            else:
                check_string_array(f"{p}.sql", sql)
                if isinstance(sql, list) and len(sql) == 0:
                    error(f"{p}.sql", "SQL array must not be empty")
            # Check for usage_guidance (recommended on complex examples)
            ug = eq.get("usage_guidance")
            if ug is not None and not isinstance(ug, list):
                error(f"{p}.usage_guidance", "Must be an array of strings")

        # Warn if no example SQLs have usage_guidance
        sqls_with_guidance = sum(1 for eq in example_sqls if eq.get("usage_guidance"))
        if len(example_sqls) > 0 and sqls_with_guidance == 0:
            warning(
                "instructions.example_question_sqls",
                "No example SQL queries have 'usage_guidance'. Adding usage_guidance helps Genie know when to apply each pattern."
            )

    # sql_functions
    sql_functions = instructions.get("sql_functions", [])
    if sql_functions:
        check_array_size("instructions.sql_functions", sql_functions)
        # Sorted by (id, identifier) tuple
        check_sorted(
            "instructions.sql_functions", sql_functions,
            lambda x: (x.get("id", ""), x.get("identifier", "")), "(id, identifier)"
        )
        for i, sf in enumerate(sql_functions):
            p = f"instructions.sql_functions[{i}]"
            sfid = sf.get("id")
            if sfid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", sfid)
                instruction_ids.append((sfid, p))
            if not sf.get("identifier"):
                error(f"{p}.identifier", "Missing required 'identifier' field")

    # join_specs
    join_specs = instructions.get("join_specs", [])
    if join_specs:
        check_array_size("instructions.join_specs", join_specs)
        check_sorted("instructions.join_specs", join_specs, lambda x: x.get("id", ""), "id")
        for i, js in enumerate(join_specs):
            p = f"instructions.join_specs[{i}]"
            jid = js.get("id")
            if jid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", jid)
                instruction_ids.append((jid, p))
            sql = js.get("sql")
            if sql is None or (isinstance(sql, list) and len(sql) == 0):
                error(f"{p}.sql", "Missing or empty 'sql' field")
            elif isinstance(sql, list):
                # Warn about compound conditions (AND/OR not supported in single elements)
                for j, s in enumerate(sql):
                    if isinstance(s, str) and re.search(r'\b(AND|OR)\b', s, re.IGNORECASE):
                        warning(
                            f"{p}.sql[{j}]",
                            "Join spec SQL contains AND/OR — each element must be a single equality. "
                            "For multi-column joins, use separate join specs with comment/instruction fields indicating they go together."
                        )
            # Warn if missing comment/instruction (recommended)
            if not js.get("comment"):
                warning(f"{p}.comment", "Missing 'comment' — adding business context helps Genie choose the right join")
            if not js.get("instruction"):
                warning(f"{p}.instruction", "Missing 'instruction' — adding usage guidance helps Genie know when to apply this join")

    # sql_snippets
    snippets = instructions.get("sql_snippets", {})
    for snippet_type in ("filters", "expressions", "measures"):
        snippet_list = snippets.get(snippet_type, [])
        if snippet_list:
            sp = f"instructions.sql_snippets.{snippet_type}"
            check_array_size(sp, snippet_list)
            check_sorted(sp, snippet_list, lambda x: x.get("id", ""), "id")
            for i, sn in enumerate(snippet_list):
                p = f"{sp}[{i}]"
                snid = sn.get("id")
                if snid is None:
                    error(f"{p}.id", "Missing required 'id' field")
                else:
                    check_id(f"{p}.id", snid)
                    instruction_ids.append((snid, p))
                sql = sn.get("sql")
                if sql is None or (isinstance(sql, list) and len(sql) == 0):
                    error(f"{p}.sql", "SQL field must not be empty")
                # Check for required name/alias fields
                if snippet_type == "filters":
                    if not sn.get("display_name"):
                        warning(f"{p}.display_name", "Missing 'display_name' field — filters should have a display name")
                elif snippet_type in ("expressions", "measures"):
                    if not sn.get("alias"):
                        warning(f"{p}.alias", "Missing 'alias' field — expressions and measures should have an alias")
                # Check for recommended optional fields
                if not sn.get("synonyms"):
                    warning(f"{p}.synonyms", "Missing 'synonyms' — adding alternate terms helps Genie match user questions to this snippet")
                if not sn.get("instruction"):
                    warning(f"{p}.instruction", "Missing 'instruction' — adding usage guidance helps Genie know when to apply this snippet")

    # --- benchmarks ---
    benchmarks = config.get("benchmarks", {})
    bench_questions = benchmarks.get("questions", [])
    if bench_questions:
        check_array_size("benchmarks.questions", bench_questions)
        check_sorted("benchmarks.questions", bench_questions, lambda x: x.get("id", ""), "id")
        for i, bq in enumerate(bench_questions):
            p = f"benchmarks.questions[{i}]"
            bid = bq.get("id")
            if bid is None:
                error(f"{p}.id", "Missing required 'id' field")
            else:
                check_id(f"{p}.id", bid)
                question_and_benchmark_ids.append((bid, p))
            answers = bq.get("answer", [])
            if len(answers) != 1:
                error(f"{p}.answer", f"Each benchmark must have exactly 1 answer, found {len(answers)}")
            for j, ans in enumerate(answers):
                if ans.get("format") != "SQL":
                    error(f"{p}.answer[{j}].format", f"Answer format must be 'SQL', got '{ans.get('format')}'")

    # --- Uniqueness checks ---
    # Question + benchmark IDs must be unique across both collections
    seen_qb = {}
    for id_val, path in question_and_benchmark_ids:
        if id_val in seen_qb:
            error(path, f"Duplicate ID '{id_val}' — also used at {seen_qb[id_val]}")
        else:
            seen_qb[id_val] = path

    # Instruction IDs must be unique across all instruction types
    seen_instr = {}
    for id_val, path in instruction_ids:
        if id_val in seen_instr:
            error(path, f"Duplicate ID '{id_val}' — also used at {seen_instr[id_val]}")
        else:
            seen_instr[id_val] = path

    # --- Instruction count budget ---
    total_instructions = len(example_sqls) + len(sql_functions) + (1 if text_instr else 0)
    if total_instructions > 100:
        error("instructions", f"Total instruction count is {total_instructions} — exceeds the 100 limit")
    elif total_instructions > 80:
        warning("instructions", f"Total instruction count is {total_instructions}/100 — approaching the limit")

    # --- Column config uniqueness ---
    col_config_keys = set()
    all_tables = tables + metric_views
    for tbl in all_tables:
        ident = tbl.get("identifier", "unknown")
        for cc in tbl.get("column_configs", []):
            key = (ident, cc.get("column_name", ""))
            if key in col_config_keys:
                error(
                    f"data_sources",
                    f"Duplicate column config: ({ident}, {cc.get('column_name')}) — must be unique"
                )
            col_config_keys.add(key)

    # --- Question formatting checks ---
    # Detect concatenated question phrasings (multiple sentences jammed into one string)
    def check_question_formatting(q_str, path):
        """Check a single question string for concatenation issues."""
        # Multiple ? in a single string = likely concatenated phrasings
        q_marks = q_str.count("?")
        if q_marks > 1:
            error(path, f"String contains {q_marks} question marks — likely multiple questions concatenated into one string. Split into separate entries, each with one question.")
            return
        # Detect sentences jammed together: "...level?Show" or "...groupsCompare"
        # Pattern: lowercase/punctuation immediately followed by uppercase (no space)
        jammed_sentences = re.findall(r'[a-z?.!]([A-Z][a-z])', q_str)
        if jammed_sentences:
            error(path, f"String appears to have multiple sentences concatenated without spaces (e.g., '...{q_str[max(0,q_str.find(jammed_sentences[0])-5):q_str.find(jammed_sentences[0])+10]}...'). Split into separate entries, each with one question.")
            return
        # Very long single question without punctuation
        if len(q_str) > 200 and "?" not in q_str:
            warning(path, f"Very long question string ({len(q_str)} chars) without a question mark — check formatting")

    for i, sq in enumerate(sample_questions):
        q_list = sq.get("question", [])
        if len(q_list) > 1:
            warning(f"config.sample_questions[{i}].question", f"Has {len(q_list)} phrasings — use one question per entry. Create separate entries for alternate phrasings.")
        for j, q_str in enumerate(q_list):
            check_question_formatting(q_str, f"config.sample_questions[{i}].question[{j}]")

    for i, eq in enumerate(example_sqls):
        q_list = eq.get("question", [])
        if len(q_list) > 1:
            warning(f"instructions.example_question_sqls[{i}].question", f"Has {len(q_list)} phrasings — use one question per SQL entry. Create separate entries for alternate phrasings.")
        for j, q_str in enumerate(q_list):
            check_question_formatting(q_str, f"instructions.example_question_sqls[{i}].question[{j}]")

    # --- SQL formatting checks ---
    # Detect SQL that's all on one line or has keywords jammed together
    SQL_KEYWORDS = {"SELECT", "FROM", "WHERE", "JOIN", "LEFT", "RIGHT", "INNER",
                    "OUTER", "CROSS", "GROUP", "ORDER", "HAVING", "LIMIT", "UNION",
                    "INSERT", "UPDATE", "DELETE", "CREATE", "WITH", "CASE", "WHEN"}

    for i, eq in enumerate(example_sqls):
        sql_parts = eq.get("sql", [])
        if sql_parts:
            full_sql = "".join(sql_parts)
            p = f"instructions.example_question_sqls[{i}].sql"

            # Check 1: SQL keywords jammed together without whitespace
            # e.g., "country_countFROM" or "antigenORDER" or "stockoutsFROM"
            jammed = re.findall(r'[a-z0-9_)][A-Z]{2,}', full_sql)
            jammed_keywords = [m for m in jammed if any(m[1:].startswith(kw) for kw in SQL_KEYWORDS)]
            if jammed_keywords:
                error(p, f"SQL keywords concatenated without whitespace (e.g., '{jammed_keywords[0]}'). "
                      f"Missing newlines between SQL clauses. Each clause should be a separate array element.")
            # Check 2: Entire SQL in a single array element and long
            elif len(sql_parts) == 1 and len(full_sql) > 100:
                error(p, f"Entire SQL query is in a single array element ({len(full_sql)} chars). "
                      f"Split each clause (SELECT, FROM, WHERE, etc.) into a separate array element.")
            # Check 3: SQL is long with no newlines across all elements
            elif len(full_sql) > 100 and "\n" not in full_sql:
                warning(p, f"SQL is {len(full_sql)} chars on a single line — consider adding '\\n' at the end of each array element for readability.")

    # --- Similar query detection and parameterization suggestions ---
    def normalize_sql(sql_parts):
        """Normalize SQL by replacing literals with placeholders for comparison."""
        full = " ".join("".join(sql_parts).split())  # collapse whitespace
        full = full.upper()
        # Replace string literals
        full = re.sub(r"'[^']*'", "'?'", full)
        # Replace numeric literals (but not in column names)
        full = re.sub(r'\b\d+\.?\d*\b', '?', full)
        return full

    def question_similarity(q1_list, q2_list):
        """Calculate word-level Jaccard similarity between two question lists."""
        words1 = set()
        for q in q1_list:
            words1.update(q.lower().split())
        words2 = set()
        for q in q2_list:
            words2.update(q.lower().split())
        if not words1 or not words2:
            return 0.0
        intersection = words1 & words2
        union = words1 | words2
        return len(intersection) / len(union)

    if len(example_sqls) >= 2:
        similar_pairs = []
        param_candidates = []
        for i in range(len(example_sqls)):
            for j in range(i + 1, len(example_sqls)):
                eq_i = example_sqls[i]
                eq_j = example_sqls[j]

                norm_i = normalize_sql(eq_i.get("sql", []))
                norm_j = normalize_sql(eq_j.get("sql", []))

                q_sim = question_similarity(
                    eq_i.get("question", []),
                    eq_j.get("question", [])
                )

                # Check if SQL structure is identical (only literals differ)
                if norm_i == norm_j:
                    q_i_text = eq_i.get("question", [""])[0][:60]
                    q_j_text = eq_j.get("question", [""])[0][:60]
                    param_candidates.append((i, j, q_i_text, q_j_text))
                # Check for high question similarity with different SQL
                elif q_sim > 0.7:
                    q_i_text = eq_i.get("question", [""])[0][:60]
                    q_j_text = eq_j.get("question", [""])[0][:60]
                    similar_pairs.append((i, j, q_i_text, q_j_text, q_sim))

        for i, j, q_i, q_j, in param_candidates:
            warning(
                f"instructions.example_question_sqls[{i}] & [{j}]",
                f"These queries have identical SQL structure — consolidate into one parameterized query using :parameter syntax.\n"
                f"      Query {i}: \"{q_i}\"\n"
                f"      Query {j}: \"{q_j}\""
            )

        for i, j, q_i, q_j, sim in similar_pairs:
            warning(
                f"instructions.example_question_sqls[{i}] & [{j}]",
                f"Questions are {int(sim*100)}% similar but SQL differs — review if these can be merged or if one is redundant.\n"
                f"      Query {i}: \"{q_i}\"\n"
                f"      Query {j}: \"{q_j}\""
            )

    # Check for example queries that already have parameters (good!) vs those that could
    for i, eq in enumerate(example_sqls):
        sql_text = "".join(eq.get("sql", []))
        has_params = eq.get("parameters") or re.search(r':\w+', sql_text)
        if not has_params:
            # Look for hardcoded filter values that could be parameters
            where_literals = re.findall(r"=\s*'([^']+)'", sql_text)
            if where_literals:
                warning(
                    f"instructions.example_question_sqls[{i}]",
                    f"Query has hardcoded filter value(s): {where_literals[:3]}. "
                    f"Consider using :parameter syntax for trusted asset labeling."
                )

    return issues


# =====================================================================
# RUN VALIDATION
# =====================================================================

if config is None and config_json_string is not None:
    try:
        config = json.loads(config_json_string)
    except json.JSONDecodeError as e:
        print(f"FATAL: Invalid JSON string — {e}")
        config = None

if config is None:
    print("No config provided. Set 'config' (dict) or 'config_json_string' (str) at the top of this script.")
    print("Or uncomment Option C to read from an existing Genie space.")
else:
    issues = validate_config(config)

    errors = [i for i in issues if i["level"] == "error"]
    warnings = [i for i in issues if i["level"] == "warning"]

    print("=" * 70)
    print("GENIE SPACE CONFIGURATION VALIDATION")
    print("=" * 70)

    # Summary counts
    tables = config.get("data_sources", {}).get("tables", [])
    metric_views = config.get("data_sources", {}).get("metric_views", [])
    instructions = config.get("instructions", {})
    example_sqls = instructions.get("example_question_sqls", [])
    text_instr = instructions.get("text_instructions", [])
    sql_functions = instructions.get("sql_functions", [])
    join_specs = instructions.get("join_specs", [])
    snippets = instructions.get("sql_snippets", {})
    snippet_measures = snippets.get("measures", [])
    snippet_filters = snippets.get("filters", [])
    snippet_expressions = snippets.get("expressions", [])
    sample_qs = config.get("config", {}).get("sample_questions", [])
    bench_qs = config.get("benchmarks", {}).get("questions", [])

    # Count column configs and usage guidance
    total_col_configs = sum(len(t.get("column_configs", [])) for t in tables)
    sqls_with_guidance = sum(1 for eq in example_sqls if eq.get("usage_guidance"))

    print(f"\n  Version: {config.get('version', 'MISSING')}")
    print(f"  Tables: {len(tables)}")
    if total_col_configs:
        print(f"  Column configs: {total_col_configs} (across all tables)")
    if metric_views:
        print(f"  Metric views: {len(metric_views)}")
    print(f"  Sample questions: {len(sample_qs)}")
    print(f"  Text instructions: {len(text_instr)}")
    print(f"  Example SQL queries: {len(example_sqls)}" + (f" ({sqls_with_guidance} with usage_guidance)" if example_sqls else ""))
    print(f"  SQL functions: {len(sql_functions)}")
    print(f"  Join specs: {len(join_specs)}")
    total_snippets = len(snippet_measures) + len(snippet_filters) + len(snippet_expressions)
    if total_snippets:
        print(f"  SQL expressions: {total_snippets} (measures: {len(snippet_measures)}, filters: {len(snippet_filters)}, dimensions: {len(snippet_expressions)})")
    else:
        print(f"  SQL expressions: 0")
    print(f"  Benchmarks: {len(bench_qs)}")
    total_instr = len(example_sqls) + len(sql_functions) + (1 if text_instr else 0)
    print(f"  Instruction budget: {total_instr}/100")

    # Categorize warnings for cleaner output
    formatting_keywords = ["concatenated", "single line", "single array element", "without whitespace", "question mark"]
    similarity_keywords = ["identical SQL structure", "similar but SQL differs", "hardcoded filter"]

    formatting_issues = [
        w for w in warnings
        if any(kw in w["message"] for kw in formatting_keywords)
    ]
    similarity_issues = [
        w for w in warnings
        if any(kw in w["message"] for kw in similarity_keywords)
    ]
    other_warnings = [
        w for w in warnings
        if w not in formatting_issues and w not in similarity_issues
    ]

    if errors:
        print(f"\n{'─' * 70}")
        print(f"ERRORS ({len(errors)}) — these will cause API rejection:")
        print(f"{'─' * 70}")
        for issue in errors:
            print(f"  ✗ [{issue['path']}]")
            print(f"    {issue['message']}")

    if other_warnings:
        print(f"\n{'─' * 70}")
        print(f"WARNINGS ({len(other_warnings)}) — best-practice recommendations:")
        print(f"{'─' * 70}")
        for issue in other_warnings:
            print(f"  ○ [{issue['path']}]")
            print(f"    {issue['message']}")

    if formatting_issues:
        print(f"\n{'─' * 70}")
        print(f"FORMATTING ISSUES ({len(formatting_issues)}):")
        print(f"{'─' * 70}")
        for issue in formatting_issues:
            print(f"  ✗ [{issue['path']}]")
            print(f"    {issue['message']}")

    if similarity_issues:
        print(f"\n{'─' * 70}")
        print(f"PARAMETERIZATION SUGGESTIONS ({len(similarity_issues)}):")
        print(f"{'─' * 70}")
        for issue in similarity_issues:
            print(f"  → [{issue['path']}]")
            print(f"    {issue['message']}")

    if not errors and not other_warnings and not formatting_issues and not similarity_issues:
        print(f"\n  ✓ Configuration is valid. No issues found.")
    elif not errors:
        total_notes = len(other_warnings) + len(formatting_issues) + len(similarity_issues)
        print(f"\n  ✓ Configuration is valid (will be accepted by API).")
        print(f"    {total_notes} suggestion(s) to consider.")
    else:
        print(f"\n  ✗ Configuration has {len(errors)} error(s) that will cause API rejection.")
        total_notes = len(other_warnings) + len(formatting_issues) + len(similarity_issues)
        if total_notes:
            print(f"    Also {total_notes} suggestion(s) to consider.")
