import os
import re
import pandas as pd

ROOT = "../logs/asap7"

configs = {
    "NC": [
        "base-run1",
        "base-run2",
        "base-run4",
        "base-run5",
        "base-run6",
    ],
    "SFTray": [
        "baseline_alpha_8-beta_0.1-run1",
        "baseline_alpha_8-beta_0.1-run2",
        # "baseline_alpha_8-beta_0.1-run3",
        "baseline_alpha_8-beta_0.1-run4",
        "baseline_alpha_8-beta_0.1-run5",
        "baseline_alpha_8-beta_0.1-run6",
    ],
    "MCF-Crit": [
        "modified_mcf_alpha_8-beta_0.1-run1",
        "modified_mcf_alpha_8-beta_0.1-run2",
        # "modified_mcf_alpha_8-beta_0.1-run3",
        "modified_mcf_alpha_8-beta_0.1-run4",
        "modified_mcf_alpha_8-beta_0.1-run5",
        "modified_mcf_alpha_8-beta_0.1-run6",
    ],
    "MCF+LP-Crit": [
        "modified_mcf_lp_alpha_8-beta_0.1-run1",
        "modified_mcf_lp_alpha_8-beta_0.1-run2",
        # "modified_mcf_lp_alpha_8-beta_0.1-run3",
        "modified_mcf_lp_alpha_8-beta_0.1-run4",
        "modified_mcf_lp_alpha_8-beta_0.1-run5",
        "modified_mcf_lp_alpha_8-beta_0.1-run6"
    ]
}

bypass_list = [
    "aes_lvt",
    "aes-block",
    "aes-block_aes_rcon",
    "aes-block_aes_sbox",
    "aes-mbff",
    "aes-mbff-tcc-v1",
    "ethmac_lvt",
    "gcd-ccs",
    "jpeg_lvt",
    "riscv32i-mock-sram",
    "riscv32i-mock-sram_fakeram7_256x32",
    "swerv_wrapper",
    "mock-cpu"
]

TIME_RE = re.compile(
    r"Elapsed time:\s*(\d+):(\d+\.\d+|\d+)\[h:\]min:sec"
)

# ---------------------------------------------------------
# Parse one log file
# ---------------------------------------------------------

def parse_elapsed_seconds(logfile):

    if not os.path.exists(logfile):
        return None

    with open(logfile, "r", errors="ignore") as f:
        text = f.read()

    matches = TIME_RE.findall(text)

    if not matches:
        return None

    # Use last elapsed time reported in file
    mins, secs = matches[-1]

    return int(mins) * 60 + float(secs)


# ---------------------------------------------------------
# Sum all runtimes from all .log files in a run directory
# ---------------------------------------------------------

def total_runtime_from_run(run_dir):

    if not os.path.isdir(run_dir):
        return None

    total = 0.0
    found = False

    for fname in os.listdir(run_dir):

        if not fname.endswith(".log"):
            continue

        logfile = os.path.join(run_dir, fname)

        t = parse_elapsed_seconds(logfile)

        if t is not None:
            total += t
            found = True

    return total if found else None


# ---------------------------------------------------------
# Convert seconds to mm:ss
# ---------------------------------------------------------

def format_time(seconds):

    if pd.isna(seconds):
        return ""

    mins = int(seconds // 60)
    secs = seconds % 60

    return f"{mins}:{secs:05.2f}"


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

results = []

for design in sorted(os.listdir(ROOT)):

    if design in bypass_list:
        continue

    design_dir = os.path.join(ROOT, design)

    if not os.path.isdir(design_dir):
        continue

    row = {"design": design}

    for cfg_name, runs in configs.items():

        gp_times = []
        total_times = []

        for run in runs:
            print(f"Processing {design} - {cfg_name} - {run}...")
            run_dir = os.path.join(design_dir, run)

            # -------------------------
            # Global placement runtime
            # -------------------------
            gp_log = os.path.join(run_dir, "3_3_place_gp.log")

            gp_time = parse_elapsed_seconds(gp_log)

            if gp_time is not None:
                gp_times.append(gp_time)

            # -------------------------
            # Total flow runtime
            # -------------------------
            total_time = total_runtime_from_run(run_dir)

            if total_time is not None:
                total_times.append(total_time)

        row[f"{cfg_name} GP (s)"] = (
            sum(gp_times) / len(gp_times)
            if gp_times else None
        )

        row[f"{cfg_name} Total (s)"] = (
            sum(total_times) / len(total_times)
            if total_times else None
        )

        row[f"{cfg_name} GP"] = (
            format_time(row[f"{cfg_name} GP (s)"])
            if row[f"{cfg_name} GP (s)"] is not None
            else ""
        )

        row[f"{cfg_name} Total"] = (
            format_time(row[f"{cfg_name} Total (s)"])
            if row[f"{cfg_name} Total (s)"] is not None
            else ""
        )

    results.append(row)

df = pd.DataFrame(results)

# nicer column order
ordered_cols = ["design"]

for cfg in configs.keys():
    ordered_cols.extend([
        f"{cfg} GP",
        f"{cfg} Total",
        f"{cfg} GP (s)",
        f"{cfg} Total (s)"
    ])

df = df[ordered_cols]

print(df)

df.to_csv("../tables/runtime_summary.csv", index=False)

print("\nSaved to ../tables/runtime_summary.csv")