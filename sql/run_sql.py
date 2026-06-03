"""Execute a .sql file (semicolon-separated statements) against a Databricks SQL warehouse."""
import sys, re
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.sql import StatementState

PROFILE = "DEFAULT"
WAREHOUSE_ID = "ec3b3b85811ecd2c"
CATALOG = "mlops_pj"
SCHEMA = "coverage_gap"

def strip_sql_comments(text: str) -> str:
    return "\n".join(l for l in text.splitlines() if not l.strip().startswith("--"))

def split_statements(text: str):
    text = strip_sql_comments(text)
    return [s.strip() for s in text.split(";") if s.strip()]

def main(path):
    w = WorkspaceClient(profile=PROFILE)
    with open(path) as f:
        statements = split_statements(f.read())
    print(f"Running {len(statements)} statements from {path}")
    for i, stmt in enumerate(statements, 1):
        preview = " ".join(stmt.split())[:90]
        resp = w.statement_execution.execute_statement(
            warehouse_id=WAREHOUSE_ID, catalog=CATALOG, schema=SCHEMA,
            statement=stmt, wait_timeout="50s",
        )
        state = resp.status.state
        if state == StatementState.SUCCEEDED:
            print(f"[{i}/{len(statements)}] OK   {preview}")
        else:
            err = resp.status.error.message if resp.status.error else state
            print(f"[{i}/{len(statements)}] FAIL {preview}\n     -> {err}")
            sys.exit(1)
    print("All statements succeeded.")

if __name__ == "__main__":
    main(sys.argv[1])
