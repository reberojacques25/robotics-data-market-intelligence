# Methodology

## Evidence-Based Approach

This project follows a strict evidence-based methodology. No claim is made without a source URL, and no company is classified as a customer without direct evidence of purchasing, licensing, commissioning, or using external robotics data.

## Data Collection Process

### Phase 1: Source Discovery
- Systematic search across Kaggle, Hugging Face, GitHub, Google Dataset Search, academic repositories, company websites, press releases, job postings, and funding databases
- Each source evaluated for relevance to the research questions, not just keyword matching

### Phase 2: Evidence Extraction
For each discovered organization, we capture:
- The exact or near-verbatim claim
- The source URL
- Publication date
- Original source type (company page, academic paper, dataset card, etc.)
- Whether it is primary-source evidence
- The data modality/task/robot inferred from the source
- A confidence score (1-5) and evidence strength (direct, strong indirect, weak indirect)

### Phase 3: Classification
Organizations are classified into evidence tiers (A/B/C/D) based on the strength and type of evidence found.

## Evidence Strength Definitions

- **Direct**: The organization itself states it collects, uses, purchases, or licenses robotics data
- **Strong indirect**: Substantial evidence from secondary sources indicating data requirements
- **Weak indirect**: Limited evidence suggesting possible data needs but insufficient for confident claims

## Opportunity Scoring Logic

An organization receives Tier A if:
1. There is direct evidence of procurement or data services purchasing, OR
2. There is a confirmed commercial relationship

Tier B requires:
- Direct evidence of data collection/use AND documented data requirements, BUT
- No confirmed evidence of external purchasing

Tier C requires:
- Some evidence of robotics/AI activity but insufficient proof of specific data requirements

Tier D:
- No credible evidence of relevant data needs

## What This Project Does NOT Claim

- Total market size estimates (methodology and data not transparent enough)
- Actual transaction prices for robotics data
- Complete buyer-supplier relationship mapping
- Internal vs. outsourced collection ratios
- Company-level demand volumes

## Data Quality Controls

- Every evidence event has a required source_url field
- Every evidence event has a required event_date field
- All enum fields are validated against allowed values
- Duplicate organization detection is enforced
- Raw data and credentials are gitignored
