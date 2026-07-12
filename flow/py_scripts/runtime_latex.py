import pandas as pd
import os

CSV_PATH = "../tables/runtime_summary.csv"
OUTPUT_TEX = "../tables/runtime_results.tex"

df = pd.read_csv(CSV_PATH)

# ------------------------------------------------------------
# Helpers
# ------------------------------------------------------------

def pct(base, value):
    if pd.isna(base) or pd.isna(value) or base == 0:
        return None
    return 100.0 * (value - base) / base

def fmt_mean_std(mean, std):
    return f"{mean:.2f} $\\pm$ {std:.2f}"

def fmt_pct_std(pct_value, std):
    return f"{pct_value:+.2f}\\% $\\pm$ {std:.2f}"

# ------------------------------------------------------------
# Build table
# ------------------------------------------------------------

latex = []

latex.append(r"\begin{table}[t]")
latex.append(r"\centering")
latex.append(
    r"\caption{Runtime comparison between NC, SFTray, MCF-Crit, and MCF+LP-Crit. "
    r"NC rows show mean runtime in seconds with standard deviation, while the "
    r"remaining rows show percentage variation relative to NC together with the "
    r"corresponding runtime standard deviation.}"
)
latex.append(r"\label{tab:runtime_results}")
latex.append(r"\scriptsize")
latex.append(r"\setlength{\tabcolsep}{3pt}")
latex.append(r"\begin{tabular}{llcc}")
latex.append(r"\toprule")
latex.append(r"Design & Version & GP Runtime & Total Runtime \\")
latex.append(r"\midrule")

for _, row in df.iterrows():

    design = row["design"]

    # --------------------------------------------------------
    # NC
    # --------------------------------------------------------

    nc_gp_mean = row["NC GP Mean (s)"]
    nc_gp_std = row["NC GP Std (s)"]

    nc_total_mean = row["NC Total Mean (s)"]
    nc_total_std = row["NC Total Std (s)"]

    # --------------------------------------------------------
    # SFTray
    # --------------------------------------------------------

    sf_gp_pct = pct(nc_gp_mean, row["SFTray GP Mean (s)"])
    sf_total_pct = pct(nc_total_mean, row["SFTray Total Mean (s)"])

    sf_gp_std = row["SFTray GP Std (s)"]
    sf_total_std = row["SFTray Total Std (s)"]

    # --------------------------------------------------------
    # MCF-Crit
    # --------------------------------------------------------

    mcf_gp_pct = pct(nc_gp_mean, row["MCF-Crit GP Mean (s)"])
    mcf_total_pct = pct(nc_total_mean, row["MCF-Crit Total Mean (s)"])

    mcf_gp_std = row["MCF-Crit GP Std (s)"]
    mcf_total_std = row["MCF-Crit Total Std (s)"]

    # --------------------------------------------------------
    # MCF+LP-Crit
    # --------------------------------------------------------

    lp_gp_pct = pct(nc_gp_mean, row["MCF+LP-Crit GP Mean (s)"])
    lp_total_pct = pct(nc_total_mean, row["MCF+LP-Crit Total Mean (s)"])

    lp_gp_std = row["MCF+LP-Crit GP Std (s)"]
    lp_total_std = row["MCF+LP-Crit Total Std (s)"]

    # --------------------------------------------------------
    # Table rows
    # --------------------------------------------------------

    latex.append(
        rf"\multirow{{4}}{{*}}{{{design}}}"
        rf" & NC"
        rf" & {fmt_mean_std(nc_gp_mean, nc_gp_std)}"
        rf" & {fmt_mean_std(nc_total_mean, nc_total_std)} \\"
    )

    latex.append(
        rf" & SFTray"
        rf" & {fmt_pct_std(sf_gp_pct, sf_gp_std)}"
        rf" & {fmt_pct_std(sf_total_pct, sf_total_std)} \\"
    )

    latex.append(
        rf" & MCF-Crit"
        rf" & {fmt_pct_std(mcf_gp_pct, mcf_gp_std)}"
        rf" & {fmt_pct_std(mcf_total_pct, mcf_total_std)} \\"
    )

    latex.append(
        rf" & MCF+LP-Crit"
        rf" & {fmt_pct_std(lp_gp_pct, lp_gp_std)}"
        rf" & {fmt_pct_std(lp_total_pct, lp_total_std)} \\"
    )

    latex.append(r"\midrule")

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"\end{table}")

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)

with open(OUTPUT_TEX, "w") as f:
    f.write("\n".join(latex))

print(f"Saved: {OUTPUT_TEX}")