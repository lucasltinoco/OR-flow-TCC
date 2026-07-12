import pandas as pd
import re

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"
OUTPUT_TEX = "../tables/alpha_summary.tex"

ALPHAS = [2,4,8,16,67,130,193,256]

df = pd.read_csv(CSV_PATH)

# --------------------------------------------------
# HELPERS
# --------------------------------------------------

def extract_alpha(flow):
    m = re.search(r'alpha[_=](\d+)', str(flow).lower())
    return int(m.group(1)) if m else None


def is_sftray(flow):
    flow = str(flow).lower()
    return (
        "sftray" in flow
        or "baseline" in flow
    )


def is_ours(flow):
    flow = str(flow).lower()
    return (
        "ours" in flow
        or "modified" in flow
    )


def is_nc(flow):
    return str(flow).strip().lower() == "nc"


# --------------------------------------------------
# PREPARE DATA
# --------------------------------------------------

df["_alpha"] = df["flow"].apply(extract_alpha)

summary = []

for alpha in ALPHAS:

    alpha_df = df[df["_alpha"] == alpha]

    power_deltas = []
    ws_deltas = []
    area_deltas = []
    clk_deltas = []

    for design in df["design"].unique():

        design_df = alpha_df[alpha_df["design"] == design]

        sftray_rows = design_df[
            design_df["flow"].apply(is_sftray)
        ]

        ours_rows = design_df[
            design_df["flow"].apply(is_ours)
        ]

        nc_rows = df[
            (df["design"] == design)
            & (df["flow"].apply(is_nc))
        ]

        if (
            len(sftray_rows) == 0
            or len(ours_rows) == 0
            or len(nc_rows) == 0
        ):
            continue

        sf = sftray_rows.iloc[0]
        ours = ours_rows.iloc[0]
        nc = nc_rows.iloc[0]

        # ------------------------------------------
        # POWER
        # ------------------------------------------

        power_delta = (
            ours["tot_power_%"]
            - sf["tot_power_%"]
        )

        power_deltas.append(power_delta)

        # ------------------------------------------
        # AREA
        # ------------------------------------------

        area_delta = (
            ours["area_%"]
            - sf["area_%"]
        )

        area_deltas.append(area_delta)

        # ------------------------------------------
        # CLK BUFS
        # ------------------------------------------

        clk_delta = (
            ours["#clk bufs_%"]
            - sf["#clk bufs_%"]
        )

        clk_deltas.append(clk_delta)

        # ------------------------------------------
        # TIMING
        #
        # negative always means
        # Ours is better
        # ------------------------------------------

        nc_wns = nc["WNS"]

        if nc_wns < 0:
            ws_delta = (
                ours["WNS_%"]
                - sf["WNS_%"]
            )
        else:
            ws_delta = (
                sf["WNS_%"]
                - ours["WNS_%"]
            )

        ws_deltas.append(ws_delta)

    summary.append({
        "alpha": alpha,
        "AvgPower": sum(power_deltas)/len(power_deltas),
        "AvgWS": sum(ws_deltas)/len(ws_deltas),
        "AvgArea": sum(area_deltas)/len(area_deltas),
        "AvgClk": sum(clk_deltas)/len(clk_deltas),
    })

summary_df = pd.DataFrame(summary)

# --------------------------------------------------
# BEST VALUES
# (most negative = best)
# --------------------------------------------------

best_power = summary_df["AvgPower"].min()
best_ws = summary_df["AvgWS"].min()
best_area = summary_df["AvgArea"].min()
best_clk = summary_df["AvgClk"].min()

# --------------------------------------------------
# LATEX
# --------------------------------------------------

latex = []

latex.append(r"\begin{table}[t]")
latex.append(r"\centering")
latex.append(
r"\caption{Average improvement of the proposed method relative to SFTray for each $\alpha$. Negative values indicate better results for the proposed method.}"
)
latex.append(r"\label{tab:alpha_summary}")
latex.append(r"\begin{tabular}{c|cccc}")
latex.append(r"\toprule")
latex.append(
r"$\alpha$ & Avg $\Delta$Power (\%) & Avg $\Delta$WS (\%) & Avg $\Delta$Area (\%) & Avg $\Delta$ClkBuf (\%) \\"
)
latex.append(r"\midrule")

for _, row in summary_df.iterrows():

    power = f"{row['AvgPower']:.2f}"
    ws = f"{row['AvgWS']:.2f}"
    area = f"{row['AvgArea']:.2f}"
    clk = f"{row['AvgClk']:.2f}"

    if row["AvgPower"] == best_power:
        power = rf"\textbf{{{power}}}"

    if row["AvgWS"] == best_ws:
        ws = rf"\textbf{{{ws}}}"

    if row["AvgArea"] == best_area:
        area = rf"\textbf{{{area}}}"

    if row["AvgClk"] == best_clk:
        clk = rf"\textbf{{{clk}}}"

    latex.append(
        f"{int(row['alpha'])} & "
        f"{power} & "
        f"{ws} & "
        f"{area} & "
        f"{clk} \\\\"
    )

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"\end{table}")

with open(OUTPUT_TEX, "w") as f:
    f.write("\n".join(latex))

print(summary_df)
print(f"Saved {OUTPUT_TEX}")