import os
import re
import json
import csv

BASE_DIR = "../logs/asap7"
OUTPUT_CSV = "../tables/final_results_pct_vs_nc.csv"

REPORT_FILE = "6_report.json"
ROUTE_FILE = "5_2_route.json"
LOG_FILE = "3_3_place_gp.log"

DESIGNS_BLACKLIST = [
    "aes_lvt",
    "aes-block",
    "aes-block_aes_rcon",
    "aes-block_aes_sbox",
    "aes-mbff",
    "aes-mbff-tcc-v1",
    "ethmac_lvt",
    "gcd-ccs",
    "jpeg_lvt",
    "mock-cpu",
    "riscv32i-mock-sram",
    "riscv32i-mock-sram_fakeram7_256x32",
    "swerv_wrapper"
]

# ------------------------------------------------------------
# REGEX
# ------------------------------------------------------------

RE_1B = re.compile(r"1-bit:\s*(\d+)")
RE_2B = re.compile(r"2-bit:\s*(\d+)")
RE_4B = re.compile(r"4-bit:\s*(\d+)")

RE_ALPHA = re.compile(r"alpha_(\d+)")

# ------------------------------------------------------------
# HELPERS
# ------------------------------------------------------------

def read_json(path):
    if not os.path.exists(path):
        return None

    with open(path, "r") as f:
        return json.load(f)


def extract_ff_counts(log_path):
    one = two = four = 0

    if not os.path.exists(log_path):
        return one, two, four

    with open(log_path, "r", errors="ignore") as f:
        text = f.read()

    m = RE_1B.search(text)
    if m:
        one = int(m.group(1))

    m = RE_2B.search(text)
    if m:
        two = int(m.group(1))

    m = RE_4B.search(text)
    if m:
        four = int(m.group(1))

    return one, two, four


def classify_flow(config):
    if config == "base":
        return "NC"

    if config.startswith("baseline_"):
        return config.replace("baseline_", "SFTray ")

    if config.startswith("modified_"):
        return config.replace("modified_", "Ours ")

    return config


def extract_alpha(config):
    m = RE_ALPHA.search(config)

    if not m:
        return -1

    return int(m.group(1))


def flow_priority(flow_name):
    if flow_name == "NC":
        return 0

    if flow_name.startswith("SFTray"):
        return 1

    if flow_name.startswith("Ours"):
        return 2

    return 99


def pct_change(value, baseline):
    if baseline == 0 or baseline is None:
        return 0.0

    return 100.0 * (value - baseline) / baseline


# ------------------------------------------------------------
# BUILD ROW
# ------------------------------------------------------------

def build_row(design,
              flow_name,
              report,
              route,
              log_path):

    one, two, four = extract_ff_counts(log_path)

    # fallback for non-clustered flows
    if one == 0 and two == 0 and four == 0:
        one = report.get(
            "finish__design__instance__count__class:sequential_cell",
            0
        )

    switching_power = report.get(
        "finish__power__switching__total",
        0
    )

    total_power = report.get(
        "finish__power__total",
        0
    )

    clk_bufs = report.get(
        "finish__design__instance__count__class:clock_buffer",
        0
    )

    wns = report.get(
        "finish__timing__setup__ws",
        0
    )

    tns = report.get(
        "finish__timing__setup__tns",
        0
    )

    area = report.get(
        "finish__design__instance__area",
        0
    )

    insts = report.get(
        "finish__design__instance__count",
        0
    )

    wl = 0

    if route is not None:
        wl = route.get(
            "detailedroute__route__wirelength",
            0
        )

    return {
        "design": design,
        "flow": flow_name,

        "switching_power": switching_power,
        "tot_power": total_power,

        "#1-bit FFs": one,
        "#2-bit FFs": two,
        "#4-bit FFs": four,

        "#clk bufs": clk_bufs,

        "WNS": wns,
        "TNS": tns,

        "area": area,
        "WL": wl,

        "#inst": insts
    }


# ------------------------------------------------------------
# MAIN
# ------------------------------------------------------------

def main():

    os.makedirs("../tables", exist_ok=True)

    collected_rows = []

    # --------------------------------------------------------
    # COLLECT RAW DATA
    # --------------------------------------------------------

    for design in sorted(os.listdir(BASE_DIR)):

        if design in DESIGNS_BLACKLIST:
            print(f"Skipping blacklisted design: {design}")
            continue

        design_path = os.path.join(BASE_DIR, design)

        if not os.path.isdir(design_path):
            continue

        for config in os.listdir(design_path):

            config_path = os.path.join(design_path, config)

            if not os.path.isdir(config_path):
                continue

            report_path = os.path.join(
                config_path,
                REPORT_FILE
            )

            route_path = os.path.join(
                config_path,
                ROUTE_FILE
            )

            log_path = os.path.join(
                config_path,
                LOG_FILE
            )

            report = read_json(report_path)

            if report is None:
                continue

            route = read_json(route_path)

            flow_name = classify_flow(config)

            row = build_row(
                design,
                flow_name,
                report,
                route,
                log_path
            )

            alpha = extract_alpha(config)

            collected_rows.append(
                (
                    design,
                    alpha,
                    flow_priority(flow_name),
                    row
                )
            )

    # --------------------------------------------------------
    # FIND NC REFERENCES
    # --------------------------------------------------------

    nc_reference = {}

    for _, _, _, row in collected_rows:
        if row["flow"] == "NC":
            nc_reference[row["design"]] = row

    # --------------------------------------------------------
    # DESIGN ORDERING BY #INST
    # --------------------------------------------------------

    design_order = []

    for design, baseline in nc_reference.items():

        insts = baseline["#inst"]

        design_order.append(
            (
                insts,
                design
            )
        )

    design_order.sort(key=lambda x: x[0])

    design_rank = {}

    for idx, (_, design) in enumerate(design_order):
        design_rank[design] = idx

    # --------------------------------------------------------
    # BUILD FINAL TABLE
    # --------------------------------------------------------

    final_rows = []

    metrics_pct = [
        "switching_power",
        "tot_power",
        "#clk bufs",
        "WNS",
        "TNS",
        "area",
        "WL",
        "#inst"
    ]

    for design, alpha, priority, row in collected_rows:

        baseline = nc_reference.get(design)

        if baseline is None:
            continue

        final_row = {
            "design": row["design"],
            "flow": row["flow"],

            "#1-bit FFs": row["#1-bit FFs"],
            "#2-bit FFs": row["#2-bit FFs"],
            "#4-bit FFs": row["#4-bit FFs"],
        }

        # concrete values + percentages
        for metric in metrics_pct:

            value = row[metric]
            ref = baseline[metric]

            final_row[metric] = value

            final_row[f"{metric}_%"] = round(
                pct_change(value, ref),
                2
            )

        final_rows.append(
            (
                design_rank[design],  # sort by #inst
                alpha,
                priority,
                final_row
            )
        )

    # --------------------------------------------------------
    # SORT
    # --------------------------------------------------------

    final_rows.sort(
        key=lambda x: (
            x[0],  # design rank by #inst
            x[1],  # alpha
            x[2]   # NC -> SFTray -> Ours
        )
    )

    rows = [x[3] for x in final_rows]

    headers = [
        "design",
        "flow",

        "switching_power",
        "switching_power_%",

        "tot_power",
        "tot_power_%",

        "#1-bit FFs",
        "#2-bit FFs",
        "#4-bit FFs",

        "#clk bufs",
        "#clk bufs_%",

        "WNS",
        "WNS_%",

        "TNS",
        "TNS_%",

        "area",
        "area_%",

        "WL",
        "WL_%",

        "#inst",
        "#inst_%"
    ]

    # --------------------------------------------------------
    # SAVE CSV
    # --------------------------------------------------------

    with open(OUTPUT_CSV, "w", newline="") as f:

        writer = csv.DictWriter(
            f,
            fieldnames=headers
        )

        writer.writeheader()
        writer.writerows(rows)

    print(f"Saved CSV to: {OUTPUT_CSV}")


if __name__ == "__main__":
    main()