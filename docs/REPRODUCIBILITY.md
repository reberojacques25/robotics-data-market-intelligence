# Reproducibility Guide

## Environment Requirements

- Python 3.9+
- pandas >= 2.0.0
- pytest >= 7.0.0

## Setup

```bash
# Clone the repository
git clone https://github.com/reberojacques25/robotics-data-market-intelligence.git
cd robotics-data-market-intelligence

# Install dependencies
pip install -r requirements.txt
```

## Running the Pipeline

### 1. Validate Data
```bash
python -m src.data_loader
```
This loads all CSV seed files, validates them against their JSON schemas, and reports any errors.

### 2. Generate Analysis
```bash
python -m src.analysis
```
This generates:
- `reports/analysis_report.json` — Full analysis results in JSON
- `reports/analysis_report.md` — Human-readable markdown report

### 3. Generate Dashboard
```bash
python -m src.dashboard.generate_dashboard
```
This generates `dashboard/index.html` — a self-contained interactive dashboard.

### 4. Run Tests
```bash
pytest tests/ -v
```
This runs:
- Schema validation tests
- Required field tests
- Evidence source URL tests
- Security tests (no secrets, no large files)
- Analysis function tests

## Expected Output

The pipeline should produce:
- 47 organizations
- 45 evidence events
- 25 data requirements
- 13 datasets
- 5 commercial relationships
- 16 job postings
- 18 funding events
- 31 market signals

All validation tests should pass with zero errors.

## Data Provenance

Every record in the seed data is traceable to a source URL. The `evidence_events` table is the core provenance table, linking each claim to its original source, publication date, source type, and evidence strength.

## Reproducing Research

To expand the dataset with additional organizations:
1. Add a new row to `data/seeds/organizations.csv`
2. Add evidence events to `data/seeds/evidence_events.csv` with source URLs
3. Add data requirements to `data/seeds/data_requirements.csv`
4. Re-run validation and analysis
5. Verify all tests still pass
