import os
import json
import re
import csv

BASE_DIR = "logs/asap7"
OUTPUT = "./tables/asap7_comparison_pct_paired.csv"

METRICS = {
    "seq_cells": "finish__design__instance__count__class:sequential_cell",
    "internal_power":"finish__power__internal__total",
    "switching_power":"finish__power__switching__total",
    "leakage_power":"finish__power__leakage__total",
    "total_power": "finish__power__total",
    "setup_tns": "finish__timing__setup__tns",
    "hold_tns": "finish__timing__hold__tns",
    "setup_ws": "finish__timing__setup__ws",
    "hold_ws": "finish__timing__hold__ws",
    "clk_buffers": "finish__design__instance__count__class:clock_buffer",
    "area": "finish__design__instance__area"
}

def extract_alpha(config):
    match = re.search(r'alpha_(\d+)', config)
    return int(match.group(1)) if match else None


def load_json(path):
    if not os.path.exists(path):
        return None
    with open(path, "r") as f:
        return json.load(f)


def pct_change(value, baseline):
    if value is None or baseline in (None, 0):
        return None
    return 100.0 * (value - baseline) / baseline


def collect_data():
    data = {
        "baseline": {},
        "theirs": {},
        "ours": {}
    }

    for exp in os.listdir(BASE_DIR):
        exp_path = os.path.join(BASE_DIR, exp)

        if not os.path.isdir(exp_path):
            continue

        for config in os.listdir(exp_path):
            config_path = os.path.join(exp_path, config)

            if not os.path.isdir(config_path):
                continue

            json_path = os.path.join(config_path, "6_report.json")
            report = load_json(json_path)

            if report is None:
                continue

            # baseline
            if exp == "aes":
                data["baseline"] = {
                    k: report.get(v, None)
                    for k, v in METRICS.items()
                }
                continue

            # filter beta
            if "beta_0.1" not in config:
                continue

            alpha = extract_alpha(config)
            if alpha is None:
                continue

            values = {
                k: report.get(v, None)
                for k, v in METRICS.items()
            }

            if "modified-v1" in exp:
                data["ours"][alpha] = values
            elif exp == "aes-mbff":
                data["theirs"][alpha] = values

    return data


def build_table(data):
    alphas = sorted(set(data["theirs"].keys()) | set(data["ours"].keys()))

    # HEADER: paired columns
    header = ["metric", "baseline"]
    for a in alphas:
        header.append(f"theirs α={a} (%)")
        header.append(f"ours α={a} (%)")

    rows = []

    for metric in METRICS.keys():
        baseline_val = data["baseline"].get(metric, None)

        row = [metric, baseline_val]

        for a in alphas:
            theirs_val = data["theirs"].get(a, {}).get(metric, None)
            ours_val   = data["ours"].get(a, {}).get(metric, None)

            t = pct_change(theirs_val, baseline_val)
            o = pct_change(ours_val, baseline_val)

            row.append(round(t, 2) if t is not None else "")
            row.append(round(o, 2) if o is not None else "")

        rows.append(row)

    return header, rows


def save_csv(header, rows):
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)

    with open(OUTPUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Saved: {OUTPUT}")


def pretty_print(header, rows):
    print("\n=== ASAP7 COMPARISON (PAIRED α) ===\n")
    print(" | ".join(str(h).ljust(18) for h in header))
    print("-" * (20 * len(header)))

    for row in rows:
        print(" | ".join(str(x).ljust(18) for x in row))


def main():
    data = collect_data()
    header, rows = build_table(data)
    save_csv(header, rows)
    pretty_print(header, rows)


if __name__ == "__main__":
    main()