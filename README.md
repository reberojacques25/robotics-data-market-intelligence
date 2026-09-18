# Robotics Data Market Intelligence

An evidence-based business analytics project identifying commercial opportunities in the robotics demonstration data, teleoperation data, and embodied-AI/VLA training data market.

## Project Overview

This project investigates whether a real, evidence-based business analytics dataset can be built to identify current and emerging commercial opportunities for a company capable of collecting high-quality robot demonstration data.

**Key principle:** Every claim is traceable to a source URL, publication date, and evidence strength classification. No company is labeled a customer without direct evidence.

## Evidence Classification Tiers

| Tier | Definition | Evidence Standard |
|------|-----------|-------------------|
| **A** | Confirmed buyer/user | Direct evidence of purchasing, licensing, commissioning, or using external robotics data |
| **B** | Strong potential buyer | Substantial evidence of data requirements but no direct evidence of external purchasing |
| **C** | Possible buyer | Relevant robotics/AI activity but insufficient evidence of a specific data requirement |
| **D** | Not enough evidence | Excluded from opportunity analysis |

## Data Model

The project uses an evidence-centered data model with 8 core tables:

1. **organizations** — Registry of companies, labs, and consortia
2. **evidence_events** — Core table: every claim maps to a source with provenance
3. **data_requirements** — What kinds of robotics data each organization needs
4. **datasets** — Registry of publicly available robot-learning datasets
5. **commercial_relationships** — Buyer-supplier relationships (conservatively classified)
6. **jobs** — Job postings as leading indicators of data demand
7. **funding_events** — Funding rounds for robotics and embodied-AI companies
8. **market_signals** — Market events: funding, partnerships, acquisitions, model launches

## Repository Structure

```
├── data/
│   ├── seeds/          # Evidence-backed seed data (CSV)
│   ├── raw/            # Raw data (gitignored)
│   ├── interim/        # Intermediate data (gitignored)
│   └── processed/      # Processed data
├── schemas/            # JSON schemas for all tables
├── src/
│   ├── data_loader.py  # Data loading and validation
│   ├── analysis.py     # Analysis scripts
│   └── dashboard/      # Dashboard generator
├── tests/              # Test suite
├── docs/               # Documentation
├── reports/            # Generated analysis reports
├── dashboard/          # Generated HTML dashboard
├── requirements.txt
└── README.md
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Load and validate all tables
python -m src.data_loader

# Generate analysis report
python -m src.analysis

# Generate dashboard
python -m src.dashboard.generate_dashboard

# Run tests
pytest tests/ -v
```

## Key Findings

- **47 organizations** tracked across humanoid, manipulation, warehouse, and autonomous vehicle segments
- **45 evidence events** with direct source URLs, covering 2023-2026
- **13 datasets** indexed totaling 1M+ trajectories and 15,000+ hours
- **16 job postings** indicating active data collection hiring
- **18 funding events** totaling $5.9B+ in robotics/embodied-AI investment
- **31 market signals** including model launches, dataset releases, and partnerships

## Data Sources

All evidence is sourced from:
- Company primary sources (blog posts, press releases, career pages)
- Academic papers and conference publications
- Dataset documentation and project pages
- Reputable financial/business databases
- High-quality journalism

## License

See [DATA_LICENSES.md](docs/DATA_LICENSES.md) for dataset-specific license information.

## Important Limitations

- Public data does not reveal total market spending on robot demonstration data
- Dataset contract prices and supplier margins are typically confidential
- Many buyer-supplier relationships are not publicly disclosed
- Proprietary dataset sizes are often not fully disclosed
- Market signals are strongest from 2024-2026; older data is used for historical context only
