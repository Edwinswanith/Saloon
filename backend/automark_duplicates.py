"""
Auto-mark high-confidence duplicate clusters as `delete` in the review CSV.

Reads the CSV produced by `export_duplicate_bills.py`, applies STRICT criteria
to identify clusters where the rapid-Checkout pattern is unambiguous, and
writes a new CSV with the `decision` column pre-filled for those rows.

Strict criteria (ALL must be true within the cluster):
  - Time gap from first bill is <= MAX_GAP_SECONDS (default 10)
  - item_count matches the first bill's item_count exactly
  - item_summary matches the first bill's item_summary exactly
  - bill_number timestamp prefix differs by at most a few seconds (≤ 10)

Clusters that fail any criterion are left blank — the owner reviews those manually.

Usage:
    python automark_duplicates.py
    python automark_duplicates.py --input duplicate_bills_report.csv \
                                  --output duplicate_bills_report_marked.csv
    python automark_duplicates.py --max-gap 15      # widen the gap threshold

Read-only on the database. Only writes a new CSV file.
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from collections import defaultdict

try:
    sys.stdout.reconfigure(encoding='utf-8')
except Exception:
    pass

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def parse_args():
    p = argparse.ArgumentParser(description='Auto-mark high-confidence duplicates in the review CSV')
    p.add_argument('--input', default='duplicate_bills_report.csv')
    p.add_argument('--output', default='duplicate_bills_report_marked.csv')
    p.add_argument('--max-gap', type=int, default=10,
                   help='Max seconds from first bill in cluster to be auto-marked (default 10)')
    return p.parse_args()


def parse_ts_prefix(bn_ts):
    """bill_number timestamp YYYYMMDDhhmmss -> int seconds-since-epoch-ish for diff."""
    if not bn_ts or len(bn_ts) < 14:
        return None
    try:
        from datetime import datetime as _dt
        return _dt.strptime(bn_ts, '%Y%m%d%H%M%S')
    except Exception:
        return None


def main():
    args = parse_args()
    in_path = args.input if os.path.isabs(args.input) else os.path.join(SCRIPT_DIR, args.input)
    out_path = args.output if os.path.isabs(args.output) else os.path.join(SCRIPT_DIR, args.output)

    if not os.path.exists(in_path):
        print(f'Input CSV not found: {in_path}')
        print('Run export_duplicate_bills.py first.')
        sys.exit(1)

    # Read everything (preserve blank separator rows)
    with open(in_path, 'r', encoding='utf-8', newline='') as f:
        reader = csv.reader(f)
        all_rows = list(reader)

    if not all_rows:
        print('Empty CSV.')
        return

    header = all_rows[0]
    col = {name: idx for idx, name in enumerate(header)}
    required = ['cluster_id', 'is_first_in_cluster', 'gap_seconds_from_first',
                'item_count', 'item_summary', 'bill_number_timestamp', 'decision']
    for name in required:
        if name not in col:
            print(f'Required column missing in CSV: {name}')
            sys.exit(1)

    # Group data rows by cluster_id (skip blank separator rows)
    cluster_rows = defaultdict(list)  # cluster_id -> list of (orig_index, row)
    for idx, row in enumerate(all_rows[1:], start=1):
        if not row or not any(cell.strip() for cell in row):
            continue
        cid = row[col['cluster_id']].strip()
        if not cid:
            continue
        cluster_rows[cid].append((idx, list(row)))

    auto_marked_clusters = 0
    auto_marked_bills = 0
    needs_review_clusters = 0

    for cid, rows in cluster_rows.items():
        # Identify the "first" row in the cluster
        first = next((r for (_, r) in rows if r[col['is_first_in_cluster']].strip().upper() == 'YES'), None)
        if first is None:
            # No row marked first — be conservative, skip
            needs_review_clusters += 1
            continue

        first_item_count = first[col['item_count']].strip()
        first_item_summary = first[col['item_summary']].strip()
        first_ts = parse_ts_prefix(first[col['bill_number_timestamp']].strip())

        # Verify every non-first row in cluster meets ALL strict criteria
        all_pass = True
        followers = []
        for orig_idx, r in rows:
            if r[col['is_first_in_cluster']].strip().upper() == 'YES':
                continue
            try:
                gap = float(r[col['gap_seconds_from_first']].strip() or '0')
            except ValueError:
                gap = 9e9
            ic = r[col['item_count']].strip()
            isum = r[col['item_summary']].strip()
            ts = parse_ts_prefix(r[col['bill_number_timestamp']].strip())

            # Criterion 1: gap within window
            if gap > args.max_gap:
                all_pass = False
                break
            # Criterion 2: identical item_count
            if ic != first_item_count:
                all_pass = False
                break
            # Criterion 3: identical item_summary
            if isum != first_item_summary:
                all_pass = False
                break
            # Criterion 4: bill_number timestamps within max_gap
            if first_ts and ts:
                if abs((ts - first_ts).total_seconds()) > args.max_gap:
                    all_pass = False
                    break

            followers.append((orig_idx, r))

        if all_pass and followers:
            auto_marked_clusters += 1
            for orig_idx, r in followers:
                # Mutate in our copy AND in all_rows so we can write it back
                r[col['decision']] = 'delete'
                all_rows[orig_idx] = r
                auto_marked_bills += 1
        else:
            needs_review_clusters += 1

    # Write out
    with open(out_path, 'w', encoding='utf-8', newline='') as f:
        w = csv.writer(f)
        for r in all_rows:
            w.writerow(r)

    print(f'Auto-marked {auto_marked_clusters} cluster(s) — {auto_marked_bills} bill(s) flagged as `delete`.')
    print(f'{needs_review_clusters} cluster(s) need manual review.')
    print(f'\nMarked CSV: {out_path}')
    print('\nNext steps:')
    print('  1. Open the marked CSV. Rows with decision=delete are auto-flagged duplicates.')
    print('  2. For clusters left blank, manually fill `delete` or `keep` per row.')
    print('  3. Run a dry-run cleanup:')
    print(f'         python cleanup_duplicate_bills.py --csv {os.path.basename(out_path)}')
    print('  4. If happy, apply:')
    print(f'         python cleanup_duplicate_bills.py --csv {os.path.basename(out_path)} --apply')


if __name__ == '__main__':
    main()
