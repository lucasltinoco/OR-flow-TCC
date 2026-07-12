import pandas as pd
import re

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"

ALPHAS = [2, 4, 8, 16, 67, 130, 193, 256]

df = pd.read_csv(CSV_PATH)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def extract_alpha(flow):
    m = re.search(r'alpha[_=](\d+)', str(flow).lower())
    return int(m.group(1)) if m else None

def is_ours(flow):
    flow = str(flow).lower()
    return (
        "ours" in flow
        or "modified" in flow
    )

# --------------------------------------------------
# KEEP ONLY OURS
# --------------------------------------------------

df = df[df["flow"].apply(is_ours)].copy()

df["alpha"] = df["flow"].apply(extract_alpha)

df = df[df["alpha"].isin(ALPHAS)]

# --------------------------------------------------
# WIN COUNTERS
# --------------------------------------------------

wins = {
    alpha: {
        "Power": 0,
        "WS": 0,
        "Area": 0,
        "ClkBuf": 0
    }
    for alpha in ALPHAS
}

# --------------------------------------------------
# DETERMINE BEST α PER DESIGN
# --------------------------------------------------

for design in sorted(df["design"].unique()):

    design_df = df[df["design"] == design]

    # ---------------------------
    # POWER
    # more negative is better
    # ---------------------------
    best_idx = design_df["tot_power_%"].idxmin()
    best_alpha = design_df.loc[best_idx, "alpha"]
    wins[best_alpha]["Power"] += 1

    # ---------------------------
    # AREA
    # more negative is better
    # ---------------------------
    best_idx = design_df["area_%"].idxmin()
    best_alpha = design_df.loc[best_idx, "alpha"]
    wins[best_alpha]["Area"] += 1

    # ---------------------------
    # CLOCK BUFFERS
    # more negative is better
    # ---------------------------
    best_idx = design_df["#clk bufs_%"].idxmin()
    best_alpha = design_df.loc[best_idx, "alpha"]
    wins[best_alpha]["ClkBuf"] += 1

    # ---------------------------
    # WS
    #
    # If NC slack is negative:
    #   lower WNS_% is better
    #
    # If NC slack is positive:
    #   higher WNS_% is better
    # ---------------------------

    nc_row = pd.read_csv(CSV_PATH)

    nc_row = nc_row[
        (nc_row["design"] == design)
        & (nc_row["flow"].str.lower() == "nc")
    ].iloc[0]

    nc_ws = nc_row["WNS"]

    if nc_ws < 0:
        best_idx = design_df["WNS_%"].idxmin()
    else:
        best_idx = design_df["WNS_%"].idxmax()

    best_alpha = design_df.loc[best_idx, "alpha"]
    wins[best_alpha]["WS"] += 1

# --------------------------------------------------
# BUILD SUMMARY TABLE
# --------------------------------------------------

rows = []

for alpha in ALPHAS:

    total = (
        wins[alpha]["Power"]
        + wins[alpha]["WS"]
        + wins[alpha]["Area"]
        + wins[alpha]["ClkBuf"]
    )

    rows.append({
        "alpha": alpha,
        "Power": wins[alpha]["Power"],
        "WS": wins[alpha]["WS"],
        "Area": wins[alpha]["Area"],
        "ClkBuf": wins[alpha]["ClkBuf"],
        "Total": total
    })

summary = pd.DataFrame(rows)

summary = summary.sort_values(
    by=["Total", "Power", "WS"],
    ascending=False
)

print(summary)
