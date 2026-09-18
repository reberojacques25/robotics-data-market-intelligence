"""Load and validate seed data from CSV files into structured DataFrames."""

import csv
import json
from pathlib import Path
from typing import Dict, List

try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

SCHEMAS_DIR = Path(__file__).parent.parent / "schemas"
SEEDS_DIR = Path(__file__).parent.parent / "data" / "seeds"

TABLES = [
    "organizations",
    "evidence_events",
    "data_requirements",
    "datasets",
    "commercial_relationships",
    "jobs",
    "funding_events",
    "market_signals",
]


def load_schema(table_name: str) -> dict:
    """Load JSON schema for a given table."""
    schema_path = SCHEMAS_DIR / f"{table_name}.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    with open(schema_path) as f:
        return json.load(f)


def load_table(table_name: str):
    """Load a CSV seed file into a DataFrame (pandas) or list of dicts."""
    csv_path = SEEDS_DIR / f"{table_name}.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Seed file not found: {csv_path}")

    if HAS_PANDAS:
        return pd.read_csv(csv_path)
    else:
        with open(csv_path, newline="") as f:
            return list(csv.DictReader(f))


def load_all_tables() -> Dict[str, object]:
    """Load all tables into a dictionary keyed by table name."""
    return {name: load_table(name) for name in TABLES}


def get_required_fields(table_name: str) -> List[str]:
    """Get list of required fields from schema."""
    schema = load_schema(table_name)
    return schema.get("required", [])


def get_enum_fields(table_name: str) -> Dict[str, List[str]]:
    """Get all fields that have enum constraints from schema."""
    schema = load_schema(table_name)
    enums = {}
    for field, props in schema.get("properties", {}).items():
        if "enum" in props:
            enums[field] = props["enum"]
    return enums


def validate_table(table_name: str) -> List[str]:
    """Validate a table against its schema. Returns list of errors."""
    errors = []
    required = get_required_fields(table_name)
    enums = get_enum_fields(table_name)
    data = load_table(table_name)

    if HAS_PANDAS:
        df = data
        # Check required fields
        for field in required:
            if field not in df.columns:
                errors.append(f"{table_name}: missing required column '{field}'")
            elif df[field].isnull().any():
                null_count = df[field].isnull().sum()
                errors.append(f"{table_name}: {null_count} null values in required field '{field}'")
        # Check enum constraints
        for field, allowed in enums.items():
            if field in df.columns:
                invalid = df[~df[field].isin(allowed + [None, ""])][field]
                if len(invalid) > 0:
                    errors.append(
                        f"{table_name}: invalid enum values in '{field}': "
                        f"{invalid.unique().tolist()}"
                    )
    else:
        rows = data
        for i, row in enumerate(rows):
            for field in required:
                if not row.get(field):
                    errors.append(f"{table_name} row {i}: missing required field '{field}'")
            for field, allowed in enums.items():
                val = row.get(field, "")
                if val and val not in allowed:
                    errors.append(
                        f"{table_name} row {i}: invalid enum value '{val}' for field '{field}'"
                    )

    return errors


def validate_all_tables() -> Dict[str, List[str]]:
    """Validate all tables. Returns dict of table_name -> list of errors."""
    return {name: validate_table(name) for name in TABLES}


def get_record_counts() -> Dict[str, int]:
    """Get record counts for all tables."""
    counts = {}
    for name in TABLES:
        data = load_table(name)
        if HAS_PANDAS:
            counts[name] = len(data)
        else:
            counts[name] = len(data)
    return counts


if __name__ == "__main__":
    print("Loading all tables...")
    tables = load_all_tables()
    for name, data in tables.items():
        if HAS_PANDAS:
            print(f"  {name}: {len(data)} records, {len(data.columns)} columns")
        else:
            print(f"  {name}: {len(data)} records")

    print("\nValidating all tables...")
    errors = validate_all_tables()
    has_errors = False
    for name, errs in errors.items():
        if errs:
            has_errors = True
            print(f"  {name}: {len(errs)} errors")
            for e in errs[:5]:
                print(f"    - {e}")
        else:
            print(f"  {name}: OK")
    if not has_errors:
        print("\nAll tables passed validation.")
