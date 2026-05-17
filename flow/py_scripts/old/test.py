import os
import json
import re
import csv

BASE_DIR = "logs/asap7"
OUTPUT = "./tables/ff_distribution_asap7_expanded_v2.csv"

LOG_FILE = "3_3_place_gp.log"
JSON_FILE = "6_report.json"

# capture sizes block
SIZES_PATTERN = re.compile(
    r"1-bit:\s*(\d+)\s+2-bit:\s*(\d+)\s+4-bit:\s*(\d+)",
    re.MULTILINE
)

ALPHAS = [2, 4, 8, 16, 67, 130, 193, 256]


def parse_base(json_path):
    if not os.path.exists(json_path):
        return ""

    with open(json_path) as f:
        data = json.load(f)

    return data.get("finish__design__instance__count__class:sequential_cell", "")


def parse_log(log_path):
    if not os.path.exists(log_path):
        return (0, 0, 0)

    one = two = four = 0

    with open(log_path, "r", errors="ignore") as f:
        for line in f:
            line = line.strip()

            if "1-bit:" in line:
                try:
                    one = int(line.split(":")[1].strip())
                except:
                    one = 0

            elif "2-bit:" in line:
                try:
                    two = int(line.split(":")[1].strip())
                except:
                    two = 0

            elif "4-bit:" in line:
                try:
                    four = int(line.split(":")[1].strip())
                except:
                    four = 0

    return (one, two, four)


def get_values(circuit_path, mode, alpha):
    folder = f"{mode}_alpha_{alpha}-beta_0.1"
    log_path = os.path.join(circuit_path, folder, LOG_FILE)
    return parse_log(log_path)


def main():
    os.makedirs("./tables", exist_ok=True)

    circuits = sorted([
        d for d in os.listdir(BASE_DIR)
        if os.path.isdir(os.path.join(BASE_DIR, d))
    ])

    # HEADER
    header = ["circuit", "base"]

    for a in ALPHAS:
        header += [
            f"baseline a={a} (1b)",
            f"baseline a={a} (2b)",
            f"baseline a={a} (4b)",
            f"modified a={a} (1b)",
            f"modified a={a} (2b)",
            f"modified a={a} (4b)",
        ]

    rows = []

    for circuit in circuits:
        circuit_path = os.path.join(BASE_DIR, circuit)

        base_json = os.path.join(circuit_path, "base", JSON_FILE)
        base_val = parse_base(base_json)

        row = [circuit, base_val]

        for a in ALPHAS:
            b1, b2, b4 = get_values(circuit_path, "baseline", a)
            m1, m2, m4 = get_values(circuit_path, "modified", a)

            row += [b1, b2, b4, m1, m2, m4]

        rows.append(row)

    # SAVE CSV
    with open(OUTPUT, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(rows)

    print(f"Saved to {OUTPUT}")

    # pretty print
    print("\n=== FF DISTRIBUTION (EXPANDED) ===\n")
    print(" | ".join(h.ljust(20) for h in header))
    print("-" * (22 * len(header)))

    for r in rows:
        print(" | ".join(str(x).ljust(20) for x in r))


if __name__ == "__main__":
    main()