"""Analysis scripts for the Robotics Data Market Intelligence project.

Produces:
- Opportunity scoring (A/B/C/D classification)
- Supplier/competitor comparison
- Data modality demand map
- Market signal timeline
- Dataset completeness summary
- Measurable / proxy / not-measurable assessment
"""

from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path

from .data_loader import load_all_tables, load_table

REPORTS_DIR = Path(__file__).parent.parent / "reports"
REPORTS_DIR.mkdir(exist_ok=True)


def opportunity_classification():
    """Classify organizations into A/B/C/D buyer tiers based on evidence.

    CRITICAL DISTINCTION: This function classifies organizations as BUYERS of robotics data.
    Suppliers (data_services_provider, dataset_provider) are classified separately.

    A. Confirmed buyer — direct evidence of purchasing, licensing, or commissioning external robotics data.
    B. Confirmed data user/collector — direct evidence of collecting or using robotics data, but no confirmed external purchasing.
    C. Possible buyer — relevant robotics/AI activity but insufficient evidence of a specific data requirement.
    D. Not enough evidence — excluded from opportunity analysis.
    """
    tables = load_all_tables()
    orgs = tables["organizations"]
    events = tables["evidence_events"]
    data_reqs = tables["data_requirements"]
    commercial = tables["commercial_relationships"]

    try:
        import pandas as pd
        HAS_PD = True
    except ImportError:
        HAS_PD = False

    # Build org -> evidence mapping
    org_evidence = defaultdict(list)
    org_data_reqs = defaultdict(list)
    org_commercial = defaultdict(list)

    if HAS_PD:
        for _, row in events.iterrows():
            org_evidence[row["organization_id"]].append(row.to_dict())
        for _, row in data_reqs.iterrows():
            org_data_reqs[row["organization_id"]].append(row.to_dict())
        for _, row in commercial.iterrows():
            org_commercial[row["buyer_organization_id"]].append(row.to_dict())
        org_ids = orgs["organization_id"].tolist()
        org_types = dict(zip(orgs["organization_id"], orgs["organization_type"]))
        org_names = dict(zip(orgs["organization_id"], orgs["legal_name"]))
    else:
        for row in events:
            org_evidence[row["organization_id"]].append(row)
        for row in data_reqs:
            org_data_reqs[row["organization_id"]].append(row)
        for row in commercial:
            org_commercial[row["buyer_organization_id"]].append(row)
        org_ids = [o["organization_id"] for o in orgs]
        org_types = {o["organization_id"]: o["organization_type"] for o in orgs}
        org_names = {o["organization_id"]: o["legal_name"] for o in orgs}

    SUPPLIER_TYPES = {"data_services_provider", "dataset_provider"}

    results = []
    for org_id in org_ids:
        evidence = org_evidence.get(org_id, [])
        reqs = org_data_reqs.get(org_id, [])
        comm = org_commercial.get(org_id, [])
        org_type = org_types.get(org_id, "")
        org_name = org_names.get(org_id, org_id)

        # Classification logic
        tier = "D"
        reason = "No evidence of robotics data activity"
        market_role = "unknown"

        direct_evidence = [e for e in evidence if e.get("evidence_strength") == "direct"]
        strong_indirect = [e for e in evidence if e.get("evidence_strength") == "strong_indirect"]
        has_data_req = len(reqs) > 0
        has_commercial = len(comm) > 0

        # Suppliers are classified by their supplier role, not as buyers
        if org_type in SUPPLIER_TYPES:
            market_role = "supplier"
            # Check if supplier also has confirmed commercial relationships as a buyer
            confirmed_comm = [c for c in comm if c.get("status") == "confirmed"]
            if direct_evidence:
                tier = "A"
                reason = f"Supplier with direct evidence of data services offering ({len(direct_evidence)} direct signals)"
            elif strong_indirect:
                tier = "B"
                reason = f"Supplier with indirect evidence ({len(strong_indirect)} signals)"
            else:
                tier = "C"
                reason = "Supplier but limited public evidence of commercial activity"
        else:
            market_role = "buyer_candidate"
            # Check for confirmed procurement (purchasing external data/robots for data collection)
            procurement_signals = [e for e in direct_evidence if e.get("signal_type") == "procurement"]
            confirmed_comm = [c for c in comm if c.get("status") == "confirmed" and c.get("relationship_type") == "purchase"]

            if confirmed_comm or procurement_signals:
                tier = "A"
                reason = f"Confirmed procurement: {len(confirmed_comm)} purchase(s), {len(procurement_signals)} procurement signal(s)"
            elif direct_evidence and has_data_req:
                # Confirmed data user/collector but no confirmed external purchasing
                tier = "B"
                reason = f"Confirmed data user/collector: {len(direct_evidence)} direct evidence signal(s), {len(reqs)} data requirement(s), but no confirmed external purchasing"
            elif direct_evidence:
                tier = "C"
                reason = f"Direct evidence of robotics activity ({len(direct_evidence)} signals) but no specific data requirement documented"
            elif strong_indirect and has_data_req:
                tier = "C"
                reason = f"Strong indirect evidence ({len(strong_indirect)} signals) with data requirements"
            elif strong_indirect:
                tier = "C"
                reason = f"Some indirect evidence ({len(strong_indirect)} signals) but insufficient for specific data requirement"
            elif evidence:
                tier = "D"
                reason = f"Weak or insufficient evidence ({len(evidence)} signals)"

        results.append({
            "organization_id": org_id,
            "organization_name": org_name,
            "tier": tier,
            "market_role": market_role,
            "reason": reason,
            "direct_evidence_count": len(direct_evidence),
            "strong_indirect_count": len(strong_indirect),
            "data_requirement_count": len(reqs),
            "commercial_relationship_count": len(comm),
            "total_evidence_count": len(evidence),
        })

    return results


def supplier_comparison():
    """Compare suppliers/competitors in the robotics data market."""
    tables = load_all_tables()
    orgs = tables["organizations"]
    events = tables["evidence_events"]

    try:
        import pandas as pd
        HAS_PD = True
    except ImportError:
        HAS_PD = False

    if HAS_PD:
        suppliers = orgs[orgs["organization_type"].isin(["data_services_provider", "dataset_provider"])]
        org_ids = suppliers["organization_id"].tolist()
        org_names = dict(zip(orgs["organization_id"], orgs["legal_name"]))
    else:
        suppliers = [o for o in orgs if o["organization_type"] in ("data_services_provider", "dataset_provider")]
        org_ids = [s["organization_id"] for s in suppliers]
        org_names = {o["organization_id"]: o["legal_name"] for o in orgs}

    results = []
    for org_id in org_ids:
        if HAS_PD:
            org_events = events[events["organization_id"] == org_id]
            name = org_names.get(org_id, org_id)
            org_info = suppliers[suppliers["organization_id"] == org_id].iloc[0]
        else:
            org_events = [e for e in events if e["organization_id"] == org_id]
            name = org_names.get(org_id, org_id)
            org_info = next((s for s in suppliers if s["organization_id"] == org_id), {})

        results.append({
            "organization_id": org_id,
            "name": name,
            "segment": org_info["robotics_segment"] if HAS_PD else org_info.get("robotics_segment", ""),
            "country": org_info["headquarters_country"] if HAS_PD else org_info.get("headquarters_country", ""),
            "evidence_count": len(org_events),
            "direct_evidence_count": len(org_events[org_events["evidence_strength"] == "direct"]) if HAS_PD else len([e for e in org_events if e.get("evidence_strength") == "direct"]),
        })

    return results


def data_modality_demand_map():
    """Map which data modalities are most demanded across organizations."""
    tables = load_all_tables()
    data_reqs = tables["data_requirements"]

    try:
        import pandas as pd
        HAS_PD = True
    except ImportError:
        HAS_PD = False

    modality_counter = Counter()
    task_counter = Counter()
    embodiment_counter = Counter()
    collection_method_counter = Counter()

    if HAS_PD:
        for _, row in data_reqs.iterrows():
            for m in str(row.get("modality", "")).split(";"):
                m = m.strip()
                if m:
                    modality_counter[m] += 1
            for t in str(row.get("task_type", "")).split(";"):
                t = t.strip()
                if t:
                    task_counter[t] += 1
            embodiment_counter[str(row.get("embodiment", ""))] += 1
            collection_method_counter[str(row.get("collection_method", ""))] += 1
    else:
        for row in data_reqs:
            for m in str(row.get("modality", "")).split(";"):
                m = m.strip()
                if m:
                    modality_counter[m] += 1
            for t in str(row.get("task_type", "")).split(";"):
                t = t.strip()
                if t:
                    task_counter[t] += 1
            embodiment_counter[str(row.get("embodiment", ""))] += 1
            collection_method_counter[str(row.get("collection_method", ""))] += 1

    return {
        "modalities": modality_counter.most_common(),
        "task_types": task_counter.most_common(),
        "embodiments": embodiment_counter.most_common(),
        "collection_methods": collection_method_counter.most_common(),
    }


def market_signal_timeline():
    """Create a timeline of market signals by year."""
    tables = load_all_tables()
    signals = tables["market_signals"]

    try:
        import pandas as pd
        HAS_PD = True
    except ImportError:
        HAS_PD = False

    timeline = defaultdict(lambda: defaultdict(int))

    if HAS_PD:
        for _, row in signals.iterrows():
            date_str = str(row.get("date", ""))
            if date_str and len(date_str) >= 4:
                year = date_str[:4]
                signal_type = str(row.get("signal_type", "unknown"))
                timeline[year][signal_type] += 1
    else:
        for row in signals:
            date_str = str(row.get("date", ""))
            if date_str and len(date_str) >= 4:
                year = date_str[:4]
                signal_type = str(row.get("signal_type", "unknown"))
                timeline[year][signal_type] += 1

    return dict(timeline)


def dataset_completeness_summary():
    """Summarize dataset completeness and coverage."""
    tables = load_all_tables()
    datasets = tables["datasets"]

    try:
        import pandas as pd
        HAS_PD = True
    except ImportError:
        HAS_PD = False

    total_datasets = len(datasets)
    public_count = 0
    gated_count = 0
    commercial_allowed = 0
    total_trajectories = 0
    total_hours = 0

    if HAS_PD:
        public_count = len(datasets[datasets["access_type"] == "public_download"])
        gated_count = len(datasets[datasets["access_type"].isin(["gated", "request_access", "streaming"])])
        commercial_allowed = len(datasets[datasets["commercial_use_status"].isin(["allowed", "per_component"])])
        total_trajectories = datasets["episodes_or_trajectories"].sum()
        total_hours = datasets["hours"].sum()
    else:
        for d in datasets:
            if d.get("access_type") == "public_download":
                public_count += 1
            elif d.get("access_type") in ("gated", "request_access", "streaming"):
                gated_count += 1
            if d.get("commercial_use_status") in ("allowed", "per_component"):
                commercial_allowed += 1
            try:
                total_trajectories += int(d.get("episodes_or_trajectories") or 0)
            except (ValueError, TypeError):
                pass
            try:
                total_hours += float(d.get("hours") or 0)
            except (ValueError, TypeError):
                pass

    return {
        "total_datasets": total_datasets,
        "public_download": public_count,
        "gated_or_restricted": gated_count,
        "commercial_use_allowed": commercial_allowed,
        "total_trajectories_indexed": int(total_trajectories),
        "total_hours_indexed": total_hours,
    }


def measurability_assessment():
    """Assess what analysis is directly measurable, proxy-only, or not measurable."""
    return {
        "directly_measurable": [
            "Number and timing of publicly released robot-learning datasets",
            "Dataset scale: trajectories, episodes, hours, tasks, embodiments, scenes",
            "Publicly stated use of teleoperation, demonstrations, human-motion data",
            "Geographic location of organizations and disclosed collection locations",
            "Frequency of evidence events over time",
            "Technology/task distribution: manipulation, bimanual, mobile, humanoid, logistics",
            "Open versus gated access, license conditions, commercial use status",
            "Number and type of public supplier claims and documented partnerships",
        ],
        "measurable_with_integration": [
            "Growth in visible robotics-data activity using time-series index of releases, hiring, model launches",
            "Geographic clusters of likely demand using HQ, facilities, job locations",
            "Relationship between funding events and later data signals",
            "Company opportunity ranking based on explicit evidence and confidence-weighted score",
            "Supplier comparison based on modalities, formats, task coverage, customer proof",
            "Market gaps between open-data coverage and customer-specific requirements",
        ],
        "proxy_only": [
            "Growth in demand for robot demonstrations (job posts, dataset releases, model papers as proxies)",
            "Likelihood of external procurement (inferred from scale needs, hardware diversity, teleoperation programs)",
            "Addressable-market direction (observable signals rather than opaque market-size reports)",
            "Correlation between foundation-model activity and demand for multimodal data",
        ],
        "not_reliably_measurable": [
            "Total global spending on robot demonstration data",
            "Dataset contract prices, per-episode rates, teleoperator compensation, supplier margins",
            "Full proprietary dataset sizes for most companies",
            "All buyer-supplier relationships",
            "Exact internal versus outsourced share of collection",
            "Revenue attributable to robot-data services alone at diversified suppliers",
            "Company-level demand volumes unless disclosed in contracts, papers, or procurement",
        ],
    }


def generate_full_report():
    """Generate a comprehensive analysis report and save to reports/."""
    results = {
        "opportunity_classification": opportunity_classification(),
        "supplier_comparison": supplier_comparison(),
        "data_modality_demand_map": data_modality_demand_map(),
        "market_signal_timeline": market_signal_timeline(),
        "dataset_completeness_summary": dataset_completeness_summary(),
        "measurability_assessment": measurability_assessment(),
    }

    import json
    report_path = REPORTS_DIR / "analysis_report.json"
    with open(report_path, "w") as f:
        json.dump(results, f, indent=2, default=str)

    # Also generate a markdown summary
    md_path = REPORTS_DIR / "analysis_report.md"
    with open(md_path, "w") as f:
        f.write("# Robotics Data Market Intelligence - Analysis Report\n\n")

        f.write("## Opportunity Classification (A/B/C/D Tiers)\n\n")
        f.write("| Tier | Count | Description |\n|---|---|---|\n")
        tier_counts = Counter(r["tier"] for r in results["opportunity_classification"])
        tier_desc = {
            "A": "Confirmed buyer/user — direct evidence of purchasing, licensing, commissioning, or using external robotics data",
            "B": "Strong potential buyer — substantial evidence of data requirements but no direct evidence of external purchasing",
            "C": "Possible buyer — relevant robotics/AI activity but insufficient evidence of a specific data requirement",
            "D": "Not enough evidence — excluded from opportunity analysis",
        }
        for tier in ["A", "B", "C", "D"]:
            f.write(f"| {tier} | {tier_counts.get(tier, 0)} | {tier_desc[tier]} |\n")
        f.write("\n### Detailed Classifications\n\n")
        f.write("| Organization | Tier | Direct Evidence | Data Reqs | Commercial Rel. | Reason |\n")
        f.write("|---|---|---|---|---|---|\n")
        for r in sorted(results["opportunity_classification"], key=lambda x: x["tier"]):
            f.write(f"| {r['organization_id']} | {r['tier']} | {r['direct_evidence_count']} | {r['data_requirement_count']} | {r['commercial_relationship_count']} | {r['reason']} |\n")

        f.write("\n## Supplier/Competitor Landscape\n\n")
        f.write("| Supplier | Segment | Country | Evidence Count | Direct Evidence |\n|---|---|---|---|---|\n")
        for s in results["supplier_comparison"]:
            f.write(f"| {s['name']} | {s['segment']} | {s['country']} | {s['evidence_count']} | {s['direct_evidence_count']} |\n")

        f.write("\n## Data Modality Demand Map\n\n")
        f.write("### Top Modalities\n\n| Modality | Count |\n|---|---|\n")
        for mod, count in results["data_modality_demand_map"]["modalities"][:15]:
            f.write(f"| {mod} | {count} |\n")

        f.write("\n### Top Task Types\n\n| Task Type | Count |\n|---|---|\n")
        for task, count in results["data_modality_demand_map"]["task_types"][:15]:
            f.write(f"| {task} | {count} |\n")

        f.write("\n### Embodiments\n\n| Embodiment | Count |\n|---|---|\n")
        for emb, count in results["data_modality_demand_map"]["embodiments"]:
            f.write(f"| {emb} | {count} |\n")

        f.write("\n### Collection Methods\n\n| Method | Count |\n|---|---|\n")
        for method, count in results["data_modality_demand_map"]["collection_methods"]:
            f.write(f"| {method} | {count} |\n")

        f.write("\n## Market Signal Timeline\n\n")
        for year in sorted(results["market_signal_timeline"].keys()):
            signals = results["market_signal_timeline"][year]
            total = sum(signals.values())
            f.write(f"### {year} ({total} signals)\n\n")
            f.write("| Signal Type | Count |\n|---|---|\n")
            for sig_type, count in sorted(signals.items()):
                f.write(f"| {sig_type} | {count} |\n")
            f.write("\n")

        f.write("## Dataset Completeness Summary\n\n")
        ds = results["dataset_completeness_summary"]
        f.write(f"- Total datasets indexed: {ds['total_datasets']}\n")
        f.write(f"- Public download: {ds['public_download']}\n")
        f.write(f"- Gated or restricted: {ds['gated_or_restricted']}\n")
        f.write(f"- Commercial use allowed: {ds['commercial_use_allowed']}\n")
        f.write(f"- Total trajectories indexed: {ds['total_trajectories_indexed']:,}\n")
        f.write(f"- Total hours indexed: {ds['total_hours_indexed']:,}\n")

        f.write("\n## Measurability Assessment\n\n")
        f.write("### Directly Measurable\n\n")
        for item in results["measurability_assessment"]["directly_measurable"]:
            f.write(f"- {item}\n")
        f.write("\n### Measurable with Integration\n\n")
        for item in results["measurability_assessment"]["measurable_with_integration"]:
            f.write(f"- {item}\n")
        f.write("\n### Proxy Only\n\n")
        for item in results["measurability_assessment"]["proxy_only"]:
            f.write(f"- {item}\n")
        f.write("\n### Not Reliably Measurable\n\n")
        for item in results["measurability_assessment"]["not_reliably_measurable"]:
            f.write(f"- {item}\n")

    return report_path


if __name__ == "__main__":
    report_path = generate_full_report()
    print(f"Analysis report generated: {report_path}")
    print(f"Markdown report: {REPORTS_DIR / 'analysis_report.md'}")
