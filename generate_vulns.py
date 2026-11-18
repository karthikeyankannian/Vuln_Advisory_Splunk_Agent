"""Write four synthetic vulnerability findings as JSON lines.

Lab code for the Vulnerability Priority Advisor demo. It does not scan
assets, contact hosts, exploit anything or remediate anything. Each run
appends four records with a new run_id. Priorities are deliberately absent:
SPL assigns them at search time.
"""
import json
import uuid
from datetime import datetime, timezone
from pathlib import Path

output = Path('/opt/splunk/var/log/soc_agent_demo/vulnerabilities.json')
run_id = uuid.uuid4().hex
timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')

# finding_id, asset, cvss, internet_facing, asset_criticality, known_exploited
findings = [
    ('DEMO-VULN-001', 'demo-vpn01', 9.8, 'yes', 'critical', 'yes'),
    ('DEMO-VULN-002', 'demo-payments01', 8.1, 'no', 'critical', 'yes'),
    ('DEMO-VULN-003', 'demo-web01', 9.8, 'yes', 'medium', 'no'),
    ('DEMO-VULN-004', 'demo-dev01', 9.8, 'no', 'low', 'no'),
]

with output.open('a', encoding='utf-8') as handle:
    for finding_id, asset, cvss, exposed, criticality, exploited in findings:
        event = {
            'timestamp': timestamp,
            'run_id': run_id,
            'finding_id': finding_id,
            'asset': asset,
            'cvss': cvss,
            'internet_facing': exposed,
            'asset_criticality': criticality,
            'known_exploited': exploited,
            'synthetic': True,
            'exploitation_on_asset': 'not_assessed',
            'priority_policy': 'demo_v1',
        }
        handle.write(json.dumps(event) + '\n')

print(f'run_id={run_id}')
print(f'events_written={len(findings)}')
print(f'output={output}')
