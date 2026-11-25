"""FR08/12 synthetic five-fold plumbing demonstration, never research evidence."""
import argparse
import csv
import json
from pathlib import Path
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluation.run import hybrid_cross_validation


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    rows = []
    for user in range(6):
        for order in range(28):
            item = order if order < 2 else 2 + (order - 2 + 3 * user) % 26
            rows.append(dict(user_id=f'synthetic-{user}', item_id=f'item-{item}', rating=1 + (user + order) % 5,
                             profile_text='python workplace communication', item_text=f'python practice topic{item}',
                             occurred_at=f'2026-10-{order + 1:02d}T00:00:00+00:00'))
    with tempfile.TemporaryDirectory() as temporary:
        source = Path(temporary) / 'synthetic-hybrid-ratings.csv'
        with source.open('w', newline='', encoding='utf-8') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)
        report = hybrid_cross_validation(source, folds=5)
    report['provenance']['origin'] = 'deterministically generated synthetic functional fixture; no participants or pilot observations'
    report['synthetic_only'] = True
    report['research_findings'] = False
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(dict(synthetic_only=True, research_findings=False, status=report['status'],
                         sample_count=report['sample_count'], folds=len(report['folds']),
                         collaborative_covered_test_count=sum(f['comparison']['collaborative_covered_test_count'] for f in report['folds']))))


if __name__ == '__main__':
    main()
