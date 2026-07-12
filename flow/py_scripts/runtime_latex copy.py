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

def fmt_abs(x):
    return f"{x:.2f}"

def fmt_pct(x):
    return f"{x:+.2f}\\%"

# ------------------------------------------------------------
# Build table
# ------------------------------------------------------------

latex = []

latex.append(r"\begin{table}[t]")
latex.append(r"\centering")
latex.append(
    r"\caption{Runtime comparison between NC, SFTray, MCF-Crit, and MCF+LP-Crit. "
    r"NC rows show absolute runtime in seconds, while the remaining rows show "
    r"percentage variation relative to NC.}"
)
latex.append(r"\label{tab:runtime_results}")
latex.append(r"\resizebox{\columnwidth}{!}{")
latex.append(r"\begin{tabular}{llcc}")
latex.append(r"\toprule")
latex.append(r"Design & Version & GP Runtime (s) & Total Runtime (s) \\")
latex.append(r"\midrule")

for _, row in df.iterrows():

    design = row["design"]

    nc_gp = row["NC GP (s)"]
    nc_total = row["NC Total (s)"]

    sf_gp = pct(nc_gp, row["SFTray GP (s)"])
    sf_total = pct(nc_total, row["SFTray Total (s)"])

    mcf_gp = pct(nc_gp, row["MCF-Crit GP (s)"])
    mcf_total = pct(nc_total, row["MCF-Crit Total (s)"])

    lp_gp = pct(nc_gp, row["MCF+LP-Crit GP (s)"])
    lp_total = pct(nc_total, row["MCF+LP-Crit Total (s)"])

    latex.append(
        rf"\multirow{{4}}{{*}}{{{design}}}"
        rf" & NC"
        rf" & {fmt_abs(nc_gp)}"
        rf" & {fmt_abs(nc_total)} \\"
    )

    latex.append(
        rf" & SFTray"
        rf" & {fmt_pct(sf_gp)}"
        rf" & {fmt_pct(sf_total)} \\"
    )

    latex.append(
        rf" & MCF-Crit"
        rf" & {fmt_pct(mcf_gp)}"
        rf" & {fmt_pct(mcf_total)} \\"
    )

    latex.append(
        rf" & MCF+LP-Crit"
        rf" & {fmt_pct(lp_gp)}"
        rf" & {fmt_pct(lp_total)} \\"
    )

    latex.append(r"\midrule")

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"}")
latex.append(r"\end{table}")

# ------------------------------------------------------------
# Save
# ------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)

with open(OUTPUT_TEX, "w") as f:
    f.write("\n".join(latex))

print(f"Saved: {OUTPUT_TEX}")