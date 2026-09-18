"""Test suite for schema validation and data integrity."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.data_loader import (
    load_all_tables,
    load_table,
    validate_all_tables,
    get_record_counts,
    TABLES,
)
from src.analysis import (
    opportunity_classification,
    supplier_comparison,
    data_modality_demand_map,
    market_signal_timeline,
    dataset_completeness_summary,
    measurability_assessment,
    generate_full_report,
)


class TestSchemaValidation:
    """Validate all tables against their JSON schemas."""

    def test_all_tables_loadable(self):
        """Every table should load without error."""
        tables = load_all_tables()
        for name in TABLES:
            assert name in tables, f"Table {name} not loaded"
            assert len(tables[name]) > 0, f"Table {name} has no records"

    def test_all_tables_valid(self):
        """All tables should pass schema validation."""
        errors = validate_all_tables()
        for name, errs in errors.items():
            assert len(errs) == 0, f"Table {name} has validation errors: {errs[:3]}"

    def test_record_counts_positive(self):
        """All tables should have at least 1 record."""
        counts = get_record_counts()
        for name, count in counts.items():
            assert count > 0, f"Table {name} has {count} records"

    def test_evidence_events_have_source_urls(self):
        """Every evidence event must have a source_url."""
        events = load_table("evidence_events")
        try:
            import pandas as pd
            for _, row in events.iterrows():
                assert row.get("source_url"), f"Event {row.get('event_id')} missing source_url"
        except ImportError:
            for row in events:
                assert row.get("source_url"), f"Event {row.get('event_id')} missing source_url"

    def test_evidence_events_have_dates(self):
        """Every evidence event must have an event_date."""
        events = load_table("evidence_events")
        try:
            import pandas as pd
            for _, row in events.iterrows():
                assert row.get("event_date"), f"Event {row.get('event_id')} missing event_date"
        except ImportError:
            for row in events:
                assert row.get("event_date"), f"Event {row.get('event_id')} missing event_date"

    def test_organizations_have_countries(self):
        """Every organization must have a headquarters_country."""
        orgs = load_table("organizations")
        try:
            import pandas as pd
            for _, row in orgs.iterrows():
                assert row.get("headquarters_country"), f"Org {row.get('organization_id')} missing country"
        except ImportError:
            for row in orgs:
                assert row.get("headquarters_country"), f"Org {row.get('organization_id')} missing country"

    def test_commercial_relationships_have_confidence(self):
        """Every commercial relationship must have a confidence_score."""
        comm = load_table("commercial_relationships")
        try:
            import pandas as pd
            for _, row in comm.iterrows():
                assert row.get("confidence_score"), f"Relationship {row.get('relationship_id')} missing confidence_score"
        except ImportError:
            for row in comm:
                assert row.get("confidence_score"), f"Relationship {row.get('relationship_id')} missing confidence_score"


class TestAnalysis:
    """Test analysis functions produce valid output."""

    def test_opportunity_classification(self):
        """Opportunity classification should return results for all organizations."""
        results = opportunity_classification()
        assert len(results) > 0, "No opportunity classifications generated"
        for r in results:
            assert r["tier"] in ["A", "B", "C", "D"], f"Invalid tier: {r['tier']}"

    def test_supplier_comparison(self):
        """Supplier comparison should return results."""
        results = supplier_comparison()
        assert len(results) > 0, "No suppliers found"

    def test_data_modality_demand_map(self):
        """Modality demand map should return non-empty results."""
        result = data_modality_demand_map()
        assert len(result["modalities"]) > 0, "No modalities found"
        assert len(result["task_types"]) > 0, "No task types found"

    def test_market_signal_timeline(self):
        """Timeline should have entries."""
        timeline = market_signal_timeline()
        assert len(timeline) > 0, "No timeline data"

    def test_dataset_completeness(self):
        """Dataset completeness summary should have valid counts."""
        summary = dataset_completeness_summary()
        assert summary["total_datasets"] > 0, "No datasets indexed"
        assert summary["total_trajectories_indexed"] > 0, "No trajectories indexed"

    def test_measurability_assessment(self):
        """Measurability assessment should have all four categories."""
        result = measurability_assessment()
        assert len(result["directly_measurable"]) > 0
        assert len(result["measurable_with_integration"]) > 0
        assert len(result["proxy_only"]) > 0
        assert len(result["not_reliably_measurable"]) > 0

    def test_generate_full_report(self):
        """Full report generation should succeed."""
        report_path = generate_full_report()
        assert report_path.exists(), f"Report not generated at {report_path}"


class TestSecurity:
    """Security tests to ensure no secrets or large files are committed."""

    def test_no_token_in_gitignore(self):
        """Ensure .gitignore exists and blocks common secret patterns."""
        gitignore = Path(__file__).parent.parent / ".gitignore"
        assert gitignore.exists(), ".gitignore not found"
        content = gitignore.read_text()
        assert ".env" in content, ".gitignore does not block .env files"
        assert "*token*" in content, ".gitignore does not block token files"
        assert "*secret*" in content, ".gitignore does not block secret files"

    def test_no_raw_data_tracked(self):
        """Ensure raw data directory is gitignored."""
        gitignore = Path(__file__).parent.parent / ".gitignore"
        content = gitignore.read_text()
        assert "data/raw/*" in content, ".gitignore does not block raw data"

    def test_no_credentials_in_seed_data(self):
        """Ensure no credential patterns in seed data files."""
        seeds_dir = Path(__file__).parent.parent / "data" / "seeds"
        for csv_file in seeds_dir.glob("*.csv"):
            content = csv_file.read_text()
            # Check for common credential patterns
            assert "password" not in content.lower() or "data_keywords" in content.lower(), \
                f"Possible password in {csv_file.name}"
            assert "api_key" not in content.lower(), f"Possible API key in {csv_file.name}"
            assert "bearer " not in content.lower(), f"Possible bearer token in {csv_file.name}"
