"""Run the openly labeled fictional research-admission case catalog.

Case expectations are public training/development fixtures, not a protected
oracle. This program checks validator behavior, not scientific correctness.
"""
import argparse
import hashlib
import json
from pathlib import Path

from .research_quality import evaluate_research

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / 'examples' / 'research-quality-cases-v0.json'


def run_suite():
    raw = CATALOG.read_bytes()
    catalog = json.loads(raw)
    if catalog.get('schema') != 'workcoord.research-case-catalog/v0':
        raise ValueError('unsupported public fixture')
    ids = [x['case_id'] for x in catalog['cases']]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate development case ID')
    rows = []
    for case in catalog['cases']:
        result = evaluate_research(case['packet'])
        codes = {code for group in result['issues'].values() for code in group}
        expected_codes = set(case['expected_issue_codes'])
        matches = result['status'] == case['expected_status'] and expected_codes <= codes
        rows.append({
            'case_id': case['case_id'],
            'fixture_label': case['label'],
            'status': result['status'],
            'issue_codes': sorted(codes),
            'development_expectation_match': matches,
            'authority': result['execution_authority'],
            'verified_causal_claim': result['verified_causal_claim'],
        })
    return {
        'schema': 'workcoord.research-case-results/v0',
        'status': 'PUBLIC_SYNTHETIC_DEVELOPMENT_NO_AGENT_RESULTS',
        'catalog_sha256': hashlib.sha256(raw).hexdigest(),
        'case_count': len(rows),
        'passed_fixture_expectations': sum(r['development_expectation_match'] for r in rows),
        'case_results': rows,
        'no_empirical_efficacy_claim': True,
        'disclaimer': 'The rubric and case labels are public and human-authored; labels do not attest causality or valid work.'
    }


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', help='Write a deterministic JSON receipt to path')
    args = parser.parse_args(argv)
    result = run_suite()
    receipt = json.dumps(result, indent=2, sort_keys=True) + '\n'
    if args.output:
        p = Path(args.output)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(receipt, encoding='utf-8')
        print(json.dumps({'cases':result['case_count'],
                          'expectations_met':result['passed_fixture_expectations'],
                          'output':str(p)}))
    else:
        print(receipt,end='')


if __name__ == '__main__':
    main()
