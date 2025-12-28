#!/usr/bin/env python3
"""
Update the 'Last Result' column in a CSV using values from a JSON file.

Key behaviors:
- Uses ONLY original CSV keys (no 'Testcase name' field).
- Overwrites a row's 'Last Result' **only if it is different** from the JSON value.
- Matches priority: Test Case ID -> ID (no name fallback unless you enable it).
- Works with JSON from:
    a) single suite: {"Test suite name": "...", "Test case 1": {...}, ...}
    b) multiple suites: {"Suite A": {...}, "Suite B": {...}, ...}

Usage examples:
  # See what would change (no file written), with verbose trace:
  python update_last_result_from_json.py input.csv input.json --dry-run --trace

  # Write to a new file:
  python update_last_result_from_json.py input.csv input.json -o updated.csv

  # Overwrite input CSV (creates .bak backup):
  python update_last_result_from_json.py input.csv input.json --in-place

  # Allow fallback by 'Test Case'/'Name' when IDs are missing:
  python update_last_result_from_json.py input.csv input.json --allow-name-fallback
"""

import argparse
import csv
import json
import os
import shutil
from collections import defaultdict

# ------------------------
# Utilities
# ------------------------

def nstr(x):
    """Normalize to stripped string or None."""
    return None if x is None else str(x).strip()

def load_csv_rows(csv_path: str):
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
        fieldnames = reader.fieldnames or []
    return rows, fieldnames

def write_csv_rows(csv_path: str, rows, fieldnames):
    # Ensure 'Last Result' column exists
    if "Last Result" not in fieldnames:
        fieldnames = list(fieldnames) + ["Last Result"]
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)

def extract_cases_from_json(obj):
    """
    Accepts:
      - single-suite dict: { "Test suite name": "...", "Test case 1": {...}, ... }
      - multi-suite dict:  { "<suite>": { "Test suite name": "...", "Test case 1": {...}, ... }, ... }
    Returns: list of case dicts.
    """
    cases = []

    def collect_cases(suite_dict):
        if not isinstance(suite_dict, dict):
            return
        # We consider any dict value under the suite dict as a case candidate.
        for _, v in suite_dict.items():
            if isinstance(v, dict):
                cases.append(v)

    if isinstance(obj, dict) and "Test suite name" in obj:
        # Single suite
        collect_cases(obj)
    elif isinstance(obj, dict):
        # Possibly multiple suites
        for _, suite_data in obj.items():
            if isinstance(suite_data, dict):
                collect_cases(suite_data)
    return cases

def build_indexes(rows):
    """
    Build lookups for matching CSV rows.
    Returns:
      - by_tcid: map[str Test Case ID] -> list[row_index]
      - by_id:   map[str ID]          -> list[row_index]
      - by_name: map[str name]        -> list[row_index]  (Test Case or Name)
    """
    by_tcid = defaultdict(list)
    by_id   = defaultdict(list)
    by_name = defaultdict(list)

    for i, r in enumerate(rows):
        tcid = nstr(r.get("Test Case ID"))
        eid  = nstr(r.get("ID"))
        name = nstr(r.get("Test Case")) or nstr(r.get("Name"))

        if tcid:
            by_tcid[tcid].append(i)
        if eid:
            by_id[eid].append(i)
        if name:
            by_name[name].append(i)

    return by_tcid, by_id, by_name

# ------------------------
# Core update routine
# ------------------------

def update_csv_last_result(csv_path: str,
                           json_path: str,
                           out_path: str = None,
                           in_place: bool = False,
                           allow_name_fallback: bool = False,
                           dry_run: bool = False,
                           trace: bool = False,
                           case_insensitive_compare: bool = False,
                           suite_filter: str = None):
    rows, fieldnames = load_csv_rows(csv_path)
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    print(f"Loaded CSV with {len(rows)} rows")
    cases = extract_cases_from_json(data)
    print(f"Loaded JSON with {len(cases)} case objects")

    if not cases:
        print("⚠️  No cases found in JSON. Exit without changes.")
        return None

    by_tcid, by_id, by_name = build_indexes(rows)

    updated = 0
    unchanged_same_value = 0
    skipped_no_new_value = 0
    not_matched = 0
    row_to_output = []
    for case in cases:
        need_upload = case.get("Need Upload")
        new_res = nstr(case.get("Last Result"))
        if new_res == "Error":
            new_res = "Failed"
        if not new_res:
            # No new value -> nothing to update
            skipped_no_new_value += 1
            continue

        tcid = nstr(case.get("Test Case ID"))
        eid  = nstr(case.get("ID"))
        name = nstr(case.get("Test Case")) or nstr(case.get("Name"))

        # Choose matching strategy
        target_indices = []
        strategy = None

        if tcid and tcid in by_tcid:
            target_indices = by_tcid[tcid]
            strategy = "tcid"
        elif eid and eid in by_id:
            target_indices = by_id[eid]
            strategy = "id"
        elif allow_name_fallback and name and name in by_name:
            target_indices = by_name[name]
            strategy = "name"
        else:
            not_matched += 1
            continue

        # Optional suite filter
        if suite_filter:
            filtered = []
            for i in target_indices:
                current_log = nstr(rows[i].get("Log Path"))
                new_log = nstr(case.get("Log Path"))
                if nstr(rows[i].get("Test Suite Execution Records")) == nstr(suite_filter):
                    filtered.append(i)
            target_indices = filtered
            if not target_indices:
                not_matched += 1
                continue

        # Apply updates ONLY when value actually changes
        for i in target_indices:
            current_log = nstr(rows[i].get("Log Path"))
            new_log = nstr(case.get("Log Path"))
            current = nstr(rows[i].get("Last Result"))
            a = (current or "")
            b = (new_res or "")
            if case_insensitive_compare:
                a, b = a.lower(), b.lower()

            if a == b and (current_log or "") == (new_log or ""):
                unchanged_same_value += 1
                continue  # no change needed

            if trace:
                print(f"[{strategy}] ID={rows[i].get('ID')} TCID={rows[i].get('Test Case ID')} "
                      f"'{current}' -> '{new_res}' ------"
                      f"'{current_log}' -> '{new_log}'")

            if not dry_run:
                if new_res is not None:
                    rows[i]["Last Result"] = new_res
                if new_log is not None:
                    rows[i]["Log Path"] = new_log
            updated += 1
            row_to_output.append(rows[i])

    # Write file (unless dry-run)
    written_path = None
    if dry_run:
        print("Dry-run mode: no file written.")
    else:
        if in_place:
            backup_path = csv_path + ".bak"
            shutil.copyfile(csv_path, backup_path)
            write_csv_rows(csv_path, row_to_output, fieldnames)
            print(f"Updated CSV in-place. Backup created at: {backup_path}")
            written_path = csv_path
        else:
            if not out_path:
                root, ext = os.path.splitext(csv_path)
                out_path = root + ".updated" + (ext or ".csv")
            write_csv_rows(out_path, row_to_output, fieldnames)
            print(f"Wrote updated CSV to: {out_path}")
            written_path = out_path

    # Summary
    print("—— Summary ——")
    print(f"Rows updated (value changed): {updated}")
    print(f"Unchanged (already same value): {unchanged_same_value}")
    print(f"Cases with no 'Last Result' in JSON: {skipped_no_new_value}")
    print(f"Cases not matched to any CSV row: {not_matched}")

    return written_path

# ------------------------
# CLI
# ------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Update 'Last Result' in a CSV from JSON, overwriting only when the value actually changes."
    )
    parser.add_argument("csv_path", help="Path to the CSV file to update")
    parser.add_argument("json_path", help="Path to the JSON file that contains 'Last Result' updates")
    parser.add_argument("-o", "--out", dest="out_path",
                        help="Path to write updated CSV (default: <csv>.updated.csv)")
    parser.add_argument("--in-place", action="store_true",
                        help="Overwrite the input CSV in-place (a .bak backup is created)")
    parser.add_argument("--allow-name-fallback", action="store_true",
                        help="Allow fallback matching by 'Test Case'/'Name' if IDs are missing")
    parser.add_argument("--dry-run", action="store_true",
                        help="Do not write any file; just report changes")
    parser.add_argument("--trace", action="store_true",
                        help="Print each applied change (ID/TCID and before->after)")
    parser.add_argument("--case-insensitive", action="store_true",
                        help="Compare values case-insensitively when deciding whether to update")
    parser.add_argument("--suite",
                        help="Only update rows where 'Test Suite Execution Records' equals this value")
    args = parser.parse_args()

    update_csv_last_result(
        csv_path=args.csv_path,
        json_path=args.json_path,
        out_path=args.out_path,
        in_place=args.in_place,
        allow_name_fallback=args.allow_name_fallback,
        dry_run=args.dry_run,
        trace=args.trace,
        case_insensitive_compare=args.case_insensitive,
        suite_filter=args.suite,
    )

if __name__ == "__main__":
    main()

# Run update_csv_last_result when this module is imported
# update_csv_last_result(
#     csv_path="uploads/Test Execution Record - many.csv",
#     json_path="outputs/out.json",
#     out_path=None,
#     in_place=False,
#     allow_name_fallback=False,
#     dry_run=False,
#     trace=False,
#     case_insensitive_compare=False,
#     suite_filter=None)