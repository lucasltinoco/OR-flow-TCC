import os
import re
import csv

BASE_DIR = "/home/ltinoco/workspace/OR-flow-TCC/flow/logs/asap7"
OUTPUT_DIR = "./tables"
LOG_FILE = "3_3_place_gp.log"

# regex to extract sizes block
SIZES_PATTERN = re.compile(
    r"Sizes used\s+"
    r"\s*1-bit:\s*(\d+)\s+"
    r"\s*2-bit:\s*(\d+)\s+"
    r"\s*4-bit:\s*(\d+)",
    re.MULTILINE
)


def parse_sizes(filepath):
    if not os.path.exists(filepath):
        return None

    with open(filepath, "r", errors="ignore") as f:
        text = f.read()

    match = SIZES_PATTERN.search(text)
    if not match:
        return None

    return {
        "1bit": int(match.group(1)),
        "2bit": int(match.group(2)),
        "4bit": int(match.group(3)),
    }


def process_experiment(exp_name):
    exp_path = os.path.join(BASE_DIR, exp_name)
    results = []

    if not os.path.exists(exp_path):
        return results

    for config in os.listdir(exp_path):
        config_path = os.path.join(exp_path, config)

        if not os.path.isdir(config_path):
            continue

        log_path = os.path.join(config_path, LOG_FILE)
        sizes = parse_sizes(log_path)

        if sizes is None:
            continue

        results.append({
            "experiment": exp_name,
            "config": config,
            "1bit": sizes["1bit"],
            "2bit": sizes["2bit"],
            "4bit": sizes["4bit"],
        })

    return results


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    table = []

    # baseline AES (no clustering)
    table.append({
        "experiment": "aes",
        "config": "base",
        "1bit": 562,
        "2bit": 0,
        "4bit": 0,
    })

    experiments = [
        "aes-mbff-customized-lib",
        "aes-mbff-criticality-continuous",
    ]

    for exp in experiments:
        table.extend(process_experiment(exp))

    # sort for readability
    table.sort(key=lambda x: (x["experiment"], x["config"]))

    # write CSV
    output_path = os.path.join(OUTPUT_DIR, "ff_comparison.csv")
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["experiment", "config", "1bit", "2bit", "4bit"]
        )
        writer.writeheader()
        writer.writerows(table)

    print(f"CSV generated at: {output_path}")

    # pretty print
    print(f"\n{'Experiment':40} {'Config':25} {'1-bit':>8} {'2-bit':>8} {'4-bit':>8}")
    print("-" * 95)
    for row in table:
        print(f"{row['experiment']:40} {row['config']:25} "
              f"{row['1bit']:8} {row['2bit']:8} {row['4bit']:8}")


if __name__ == "__main__":
    main()