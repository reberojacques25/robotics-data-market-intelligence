"""Generate a static HTML dashboard from the analysis report."""

import json
from pathlib import Path

from ..data_loader import load_all_tables, get_record_counts
from ..analysis import (
    opportunity_classification,
    supplier_comparison,
    data_modality_demand_map,
    market_signal_timeline,
    dataset_completeness_summary,
    measurability_assessment,
)

DASHBOARD_DIR = Path(__file__).parent.parent.parent / "dashboard"


def generate_dashboard():
    """Generate a self-contained HTML dashboard."""
    tables = load_all_tables()
    counts = get_record_counts()

    opp = opportunity_classification()
    suppliers = supplier_comparison()
    modality_map = data_modality_demand_map()
    timeline = market_signal_timeline()
    dataset_summary = dataset_completeness_summary()
    measurability = measurability_assessment()

    # Build organization data with evidence
    org_data = {}
    try:
        import pandas as pd
        orgs_df = tables["organizations"]
        events_df = tables["evidence_events"]
        data_reqs_df = tables["data_requirements"]

        for _, org in orgs_df.iterrows():
            org_id = org["organization_id"]
            org_events = events_df[events_df["organization_id"] == org_id]
            org_reqs = data_reqs_df[data_reqs_df["organization_id"] == org_id]
            opp_record = next((o for o in opp if o["organization_id"] == org_id), {})

            org_data[org_id] = {
                "id": org_id,
                "name": org.get("legal_name", ""),
                "type": org.get("organization_type", ""),
                "country": org.get("headquarters_country", ""),
                "segment": org.get("robotics_segment", ""),
                "tier": opp_record.get("tier", "D"),
                "evidence_count": opp_record.get("total_evidence_count", 0),
                "direct_evidence": opp_record.get("direct_evidence_count", 0),
                "data_reqs": opp_record.get("data_requirement_count", 0),
                "reason": opp_record.get("reason", ""),
                "events": org_events.to_dict("records"),
            }
    except Exception:
        pass

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Robotics Data Market Intelligence Dashboard</title>
    <style>
        :root {{
            --bg: #0f1117;
            --card-bg: #1a1d27;
            --text: #e4e6eb;
            --text-muted: #8b8e98;
            --accent: #4f9cf9;
            --accent-hover: #3b8be6;
            --tier-a: #2ecc71;
            --tier-b: #f39c12;
            --tier-c: #3498db;
            --tier-d: #7f8c8d;
            --border: #2a2d3a;
            --radius: 8px;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: var(--bg);
            color: var(--text);
            line-height: 1.6;
            padding: 20px;
        }}
        .container {{ max-width: 1400px; margin: 0 auto; }}
        h1 {{ font-size: 1.8em; margin-bottom: 8px; }}
        h2 {{ font-size: 1.3em; margin: 30px 0 12px; color: var(--accent); }}
        h3 {{ font-size: 1.1em; margin: 20px 0 8px; }}
        .subtitle {{ color: var(--text-muted); margin-bottom: 30px; font-size: 0.95em; }}
        .stats-grid {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            text-align: center;
        }}
        .stat-value {{ font-size: 2em; font-weight: 700; color: var(--accent); }}
        .stat-label {{ font-size: 0.85em; color: var(--text-muted); margin-top: 4px; }}
        .card {{
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 20px;
            margin-bottom: 20px;
            overflow-x: auto;
        }}
        table {{ width: 100%; border-collapse: collapse; font-size: 0.9em; }}
        th {{ text-align: left; padding: 10px 12px; border-bottom: 2px solid var(--border); color: var(--text-muted); font-weight: 600; text-transform: uppercase; font-size: 0.8em; }}
        td {{ padding: 10px 12px; border-bottom: 1px solid var(--border); }}
        tr:hover {{ background: rgba(79, 156, 249, 0.05); }}
        .tier-badge {{
            display: inline-block;
            padding: 2px 10px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 0.85em;
        }}
        .tier-A {{ background: rgba(46, 204, 113, 0.2); color: var(--tier-a); }}
        .tier-B {{ background: rgba(243, 156, 18, 0.2); color: var(--tier-b); }}
        .tier-C {{ background: rgba(52, 152, 219, 0.2); color: var(--tier-c); }}
        .tier-D {{ background: rgba(127, 140, 141, 0.2); color: var(--tier-d); }}
        .filter-bar {{
            display: flex;
            gap: 12px;
            margin-bottom: 16px;
            flex-wrap: wrap;
        }}
        .filter-bar select, .filter-bar input {{
            background: var(--card-bg);
            color: var(--text);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            padding: 8px 12px;
            font-size: 0.9em;
        }}
        .filter-bar select:focus, .filter-bar input:focus {{ outline: none; border-color: var(--accent); }}
        .evidence-link {{ color: var(--accent); text-decoration: none; }}
        .evidence-link:hover {{ text-decoration: underline; }}
        .bar-chart {{ display: flex; align-items: center; gap: 8px; margin: 4px 0; }}
        .bar {{ height: 20px; border-radius: 4px; background: var(--accent); min-width: 2px; transition: width 0.3s; }}
        .bar-label {{ font-size: 0.85em; min-width: 120px; }}
        .bar-value {{ font-size: 0.85em; color: var(--text-muted); }}
        .section-tabs {{ display: flex; gap: 8px; margin-bottom: 20px; flex-wrap: wrap; }}
        .tab {{
            padding: 8px 16px;
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: var(--radius);
            cursor: pointer;
            font-size: 0.9em;
            color: var(--text-muted);
        }}
        .tab.active {{ color: var(--accent); border-color: var(--accent); }}
        .tab:hover {{ color: var(--text); }}
        .tab-content {{ display: none; }}
        .tab-content.active {{ display: block; }}
        .evidence-row {{ padding: 12px; border-bottom: 1px solid var(--border); }}
        .evidence-claim {{ margin-bottom: 4px; }}
        .evidence-meta {{ font-size: 0.8em; color: var(--text-muted); }}
        .footer {{ margin-top: 40px; padding-top: 20px; border-top: 1px solid var(--border); color: var(--text-muted); font-size: 0.85em; }}
    </style>
</head>
<body>
<div class="container">
    <h1>Robotics Data Market Intelligence Dashboard</h1>
    <p class="subtitle">Evidence-based market intelligence for robotics demonstration data, teleoperation, and embodied-AI training data</p>

    <div class="stats-grid">
        <div class="stat-card">
            <div class="stat-value">{counts.get('organizations', 0)}</div>
            <div class="stat-label">Organizations</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{counts.get('evidence_events', 0)}</div>
            <div class="stat-label">Evidence Events</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{counts.get('datasets', 0)}</div>
            <div class="stat-label">Datasets Indexed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{dataset_summary['total_trajectories_indexed']:,}</div>
            <div class="stat-label">Trajectories Indexed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{dataset_summary['total_hours_indexed']:,.0f}</div>
            <div class="stat-label">Hours Indexed</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{counts.get('jobs', 0)}</div>
            <div class="stat-label">Job Postings</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{counts.get('funding_events', 0)}</div>
            <div class="stat-label">Funding Events</div>
        </div>
        <div class="stat-card">
            <div class="stat-value">{counts.get('market_signals', 0)}</div>
            <div class="stat-label">Market Signals</div>
        </div>
    </div>

    <div class="section-tabs">
        <div class="tab active" onclick="showTab('opportunity')">Opportunity Analysis</div>
        <div class="tab" onclick="showTab('organizations')">Organizations</div>
        <div class="tab" onclick="showTab('evidence')">Evidence Browser</div>
        <div class="tab" onclick="showTab('suppliers')">Suppliers</div>
        <div class="tab" onclick="showTab('modalities')">Data Demand</div>
        <div class="tab" onclick="showTab('timeline')">Timeline</div>
        <div class="tab" onclick="showTab('measurability')">Measurability</div>
    </div>

    <!-- Opportunity Analysis Tab -->
    <div id="opportunity" class="tab-content active">
        <h2>Opportunity Classification (A/B/C/D Tiers)</h2>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Tier</th>
                        <th>Count</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>"""

    tier_counts = {}
    for r in opp:
        tier_counts[r["tier"]] = tier_counts.get(r["tier"], 0) + 1

    tier_desc = {
        "A": "Confirmed buyer/user — direct evidence of purchasing, licensing, commissioning, or using external robotics data",
        "B": "Strong potential buyer — substantial evidence of data requirements but no direct evidence of external purchasing",
        "C": "Possible buyer — relevant robotics/AI activity but insufficient evidence of a specific data requirement",
        "D": "Not enough evidence — excluded from opportunity analysis",
    }

    for tier in ["A", "B", "C", "D"]:
        html += f"""
                    <tr>
                        <td><span class="tier-badge tier-{tier}">{tier}</span></td>
                        <td>{tier_counts.get(tier, 0)}</td>
                        <td>{tier_desc[tier]}</td>
                    </tr>"""

    html += f"""
                </tbody>
            </table>
        </div>
        <h3>Detailed Classifications</h3>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Organization</th>
                        <th>Tier</th>
                        <th>Direct Evidence</th>
                        <th>Data Reqs</th>
                        <th>Commercial Rel.</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>"""

    for r in sorted(opp, key=lambda x: (x["tier"], -x["direct_evidence_count"])):
        html += f"""
                    <tr>
                        <td>{r['organization_id']}</td>
                        <td><span class="tier-badge tier-{r['tier']}">{r['tier']}</span></td>
                        <td>{r['direct_evidence_count']}</td>
                        <td>{r['data_requirement_count']}</td>
                        <td>{r['commercial_relationship_count']}</td>
                        <td style="font-size: 0.85em;">{r['reason']}</td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- Organizations Tab -->
    <div id="organizations" class="tab-content">
        <h2>Organizations</h2>
        <div class="filter-bar">
            <input type="text" id="org-search" placeholder="Search organizations..." oninput="filterTable('org-table', 'org-search')">
            <select id="org-tier-filter" onchange="filterByTier()">
                <option value="">All Tiers</option>
                <option value="A">Tier A</option>
                <option value="B">Tier B</option>
                <option value="C">Tier C</option>
                <option value="D">Tier D</option>
            </select>
        </div>
        <div class="card">
            <table id="org-table">
                <thead>
                    <tr>
                        <th>ID</th>
                        <th>Name</th>
                        <th>Type</th>
                        <th>Country</th>
                        <th>Segment</th>
                        <th>Tier</th>
                        <th>Evidence</th>
                        <th>Data Reqs</th>
                    </tr>
                </thead>
                <tbody>"""

    for org_id, data in sorted(org_data.items()):
        html += f"""
                    <tr data-tier="{data['tier']}">
                        <td>{data['id']}</td>
                        <td>{data['name']}</td>
                        <td>{data['type']}</td>
                        <td>{data['country']}</td>
                        <td style="font-size: 0.85em;">{data['segment']}</td>
                        <td><span class="tier-badge tier-{data['tier']}">{data['tier']}</span></td>
                        <td>{data['evidence_count']}</td>
                        <td>{data['data_reqs']}</td>
                    </tr>"""

    html += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- Evidence Browser Tab -->
    <div id="evidence" class="tab-content">
        <h2>Evidence Browser</h2>
        <div class="filter-bar">
            <input type="text" id="evidence-search" placeholder="Search evidence..." oninput="filterEvidence()">
            <select id="evidence-strength-filter" onchange="filterEvidence()">
                <option value="">All Strengths</option>
                <option value="direct">Direct</option>
                <option value="strong_indirect">Strong Indirect</option>
                <option value="weak_indirect">Weak Indirect</option>
            </select>
        </div>
        <div class="card" id="evidence-list">"""

    # Add evidence rows
    try:
        import pandas as pd
        events_df = tables["evidence_events"]
        orgs_df = tables["organizations"]
        org_names = dict(zip(orgs_df["organization_id"], orgs_df["legal_name"]))
        for _, evt in events_df.iterrows():
            org_name = org_names.get(evt["organization_id"], evt["organization_id"])
            strength = evt.get("evidence_strength", "")
            html += f"""
            <div class="evidence-row" data-strength="{strength}" data-search="{org_name} {evt.get('claim_text', '')} {evt.get('signal_type', '')}">
                <div class="evidence-claim">{evt.get('claim_text', '')}</div>
                <div class="evidence-meta">
                    <strong>{org_name}</strong> · {evt.get('signal_type', '')} · {evt.get('event_date', '')} ·
                    <span class="tier-badge tier-{'A' if strength == 'direct' else 'B' if strength == 'strong_indirect' else 'D'}">{strength}</span> ·
                    <a href="{evt.get('source_url', '#')}" target="_blank" class="evidence-link">Source</a>
                </div>
            </div>"""
    except Exception:
        pass

    html += """
        </div>
    </div>

    <!-- Suppliers Tab -->
    <div id="suppliers" class="tab-content">
        <h2>Supplier & Competitor Landscape</h2>
        <div class="card">
            <table>
                <thead>
                    <tr>
                        <th>Supplier</th>
                        <th>Segment</th>
                        <th>Country</th>
                        <th>Evidence Count</th>
                        <th>Direct Evidence</th>
                    </tr>
                </thead>
                <tbody>"""

    for s in suppliers:
        html += f"""
                    <tr>
                        <td>{s['name']}</td>
                        <td style="font-size: 0.85em;">{s['segment']}</td>
                        <td>{s['country']}</td>
                        <td>{s['evidence_count']}</td>
                        <td>{s['direct_evidence_count']}</td>
                    </tr>"""

    html += f"""
                </tbody>
            </table>
        </div>
    </div>

    <!-- Data Demand Tab -->
    <div id="modalities" class="tab-content">
        <h2>Data Modality Demand Map</h2>
        <h3>Top Modalities</h3>
        <div class="card">"""

    max_count = modality_map["modalities"][0][1] if modality_map["modalities"] else 1
    for mod, count in modality_map["modalities"][:15]:
        width = (count / max_count) * 300
        html += f"""
            <div class="bar-chart">
                <span class="bar-label">{mod}</span>
                <div class="bar" style="width: {width}px;"></div>
                <span class="bar-value">{count}</span>
            </div>"""

    html += f"""
        </div>
        <h3>Top Task Types</h3>
        <div class="card">"""

    max_task = modality_map["task_types"][0][1] if modality_map["task_types"] else 1
    for task, count in modality_map["task_types"][:15]:
        width = (count / max_task) * 300
        html += f"""
            <div class="bar-chart">
                <span class="bar-label">{task}</span>
                <div class="bar" style="width: {width}px;"></div>
                <span class="bar-value">{count}</span>
            </div>"""

    html += f"""
        </div>
        <h3>Embodiments</h3>
        <div class="card">
            <table>
                <thead><tr><th>Embodiment</th><th>Count</th></tr></thead>
                <tbody>"""

    for emb, count in modality_map["embodiments"]:
        html += f"<tr><td>{emb}</td><td>{count}</td></tr>"

    html += f"""
                </tbody>
            </table>
        </div>
        <h3>Collection Methods</h3>
        <div class="card">
            <table>
                <thead><tr><th>Method</th><th>Count</th></tr></thead>
                <tbody>"""

    for method, count in modality_map["collection_methods"]:
        html += f"<tr><td>{method}</td><td>{count}</td></tr>"

    html += """
                </tbody>
            </table>
        </div>
    </div>

    <!-- Timeline Tab -->
    <div id="timeline" class="tab-content">
        <h2>Market Signal Timeline</h2>"""

    for year in sorted(timeline.keys()):
        signals = timeline[year]
        total = sum(signals.values())
        html += f"""
        <div class="card">
            <h3>{year} ({total} signals)</h3>
            <table>
                <thead><tr><th>Signal Type</th><th>Count</th></tr></thead>
                <tbody>"""
        for sig_type, count in sorted(signals.items(), key=lambda x: -x[1]):
            html += f"<tr><td>{sig_type}</td><td>{count}</td></tr>"
        html += """
                </tbody>
            </table>
        </div>"""

    html += f"""
    </div>

    <!-- Measurability Tab -->
    <div id="measurability" class="tab-content">
        <h2>Measurability Assessment</h2>
        <h3 style="color: var(--tier-a);">Directly Measurable</h3>
        <div class="card">"""

    for item in measurability["directly_measurable"]:
        html += f"<p>• {item}</p>"

    html += f"""
        </div>
        <h3 style="color: var(--tier-b);">Measurable with Integration</h3>
        <div class="card">"""

    for item in measurability["measurable_with_integration"]:
        html += f"<p>• {item}</p>"

    html += f"""
        </div>
        <h3 style="color: var(--tier-c);">Proxy Only</h3>
        <div class="card">"""

    for item in measurability["proxy_only"]:
        html += f"<p>• {item}</p>"

    html += f"""
        </div>
        <h3 style="color: var(--tier-d);">Not Reliably Measurable</h3>
        <div class="card">"""

    for item in measurability["not_reliably_measurable"]:
        html += f"<p>• {item}</p>"

    html += f"""
        </div>
    </div>

    <div class="footer">
        <p>Robotics Data Market Intelligence · Generated from evidence-backed seed data · Every claim is traceable to a source URL</p>
        <p>Classification tiers: A = Confirmed buyer/user, B = Strong potential buyer, C = Possible buyer, D = Not enough evidence</p>
    </div>
</div>

<script>
    function showTab(tabId) {{
        document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
        document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
        document.getElementById(tabId).classList.add('active');
        event.target.classList.add('active');
    }}

    function filterTable(tableId, searchId) {{
        const query = document.getElementById(searchId).value.toLowerCase();
        const rows = document.querySelectorAll('#' + tableId + ' tbody tr');
        rows.forEach(row => {{
            const text = row.textContent.toLowerCase();
            row.style.display = text.includes(query) ? '' : 'none';
        }});
    }}

    function filterByTier() {{
        const tier = document.getElementById('org-tier-filter').value;
        const rows = document.querySelectorAll('#org-table tbody tr');
        rows.forEach(row => {{
            if (!tier || row.dataset.tier === tier) {{
                row.style.display = '';
            }} else {{
                row.style.display = 'none';
            }}
        }});
    }}

    function filterEvidence() {{
        const query = document.getElementById('evidence-search').value.toLowerCase();
        const strength = document.getElementById('evidence-strength-filter').value;
        const rows = document.querySelectorAll('.evidence-row');
        rows.forEach(row => {{
            const text = row.dataset.search.toLowerCase();
            const rowStrength = row.dataset.strength;
            const textMatch = !query || text.includes(query);
            const strengthMatch = !strength || rowStrength === strength;
            row.style.display = (textMatch && strengthMatch) ? '' : 'none';
        }});
    }}
</script>
</body>
</html>"""

    DASHBOARD_DIR.mkdir(exist_ok=True)
    dashboard_path = DASHBOARD_DIR / "index.html"
    with open(dashboard_path, "w") as f:
        f.write(html)

    return dashboard_path


if __name__ == "__main__":
    path = generate_dashboard()
    print(f"Dashboard generated: {path}")
