import csv
import os
import re

INPUT_CSV = "./tables/ff_comparison.csv"
OUTPUT_CSV = "./tables/ff_comparison_pivot.csv"

def extract_alpha(config):
    match = re.search(r'alpha_(\d+)', config)
    return int(match.group(1)) if match else None


def load_data():
    data = {
        "baseline": {"1bit": 562, "2bit": 0, "4bit": 0},
        "theirs": {},
        "ours": {}
    }

    with open(INPUT_CSV, "r") as f:
        reader = csv.DictReader(f)

        for row in reader:
            exp = row["experiment"]
            config = row["config"]

            if "beta_0.1" not in config:
                continue

            alpha = extract_alpha(config)
            if alpha is None:
                continue

            values = {
                "1bit": int(row["1bit"]),
                "2bit": int(row["2bit"]),
                "4bit": int(row["4bit"]),
            }

            if exp == "aes-mbff-customized-lib":
                data["theirs"][alpha] = values
            elif exp == "aes-mbff-criticality-continuous":
                data["ours"][alpha] = values

    return data


def build_table(data):
    alphas = sorted(set(data["theirs"].keys()) | set(data["ours"].keys()))

    header = (
        [""] +
        ["baseline"] +
        ["theirs α=" + str(a) for a in alphas] +
        ["ours α=" + str(a) for a in alphas]
    )

    rows = []

    for bit in ["1bit", "2bit", "4bit"]:
        row = [f"#{bit.replace('bit','-bit')}"]

        # baseline
        row.append(data["baseline"][bit])

        # customized
        for a in alphas:
            row.append(data["theirs"].get(a, {}).get(bit, ""))

        # ours
        for a in alphas:
            row.append(data["ours"].get(a, {}).get(bit, ""))

        rows.append(row)

    return header, rows


def save_csv(header, rows):
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)

    with open(OUTPUT_CSV, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Saved pivot table to: {OUTPUT_CSV}")


def print_pretty(header, rows):
    print("\n=== FORMATTED TABLE ===\n")
    print(" | ".join(str(h).ljust(12) for h in header))
    print("-" * (15 * len(header)))

    for row in rows:
        print(" | ".join(str(x).ljust(12) for x in row))


def main():
    data = load_data()
    header, rows = build_table(data)
    save_csv(header, rows)
    print_pretty(header, rows)


if __name__ == "__main__":
    main()