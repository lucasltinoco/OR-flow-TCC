import pandas as pd
import os

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"
OUTPUT_TEX = "../tables/nc_ff_ratio_table.tex"

# ------------------------------------------------------------
# LOAD CSV
# ------------------------------------------------------------

df = pd.read_csv(CSV_PATH)

# ------------------------------------------------------------
# KEEP ONLY NC
# ------------------------------------------------------------

df = df[df["flow"].str.lower() == "nc"].copy()

# ------------------------------------------------------------
# COMPUTE RATIO
# ------------------------------------------------------------

df["ff_ratio"] = df["#1-bit FFs"] / df["#inst"]

# ------------------------------------------------------------
# SORT BY FF RATIO DESC
# ------------------------------------------------------------

df = df.sort_values(
    by="ff_ratio",
    ascending=False
)

# ------------------------------------------------------------
# LATEX ESCAPE
# ------------------------------------------------------------

def latex_escape(text):

    replacements = {
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
    }

    text = str(text)

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text

# ------------------------------------------------------------
# GENERATE LATEX
# ------------------------------------------------------------

latex = []

latex.append(r"\begin{table}[t]")
latex.append(r"\centering")

latex.append(
    r"\caption{Sequential-cell composition of non-clustered (NC) designs.}"
)

latex.append(r"\label{tab:nc_ff_ratio}")

latex.append(r"\begin{tabular}{lccc}")
latex.append(r"\toprule")

latex.append(
    r"Design & \#1-bit FFs & \#Instances & FF Ratio \\"
)

latex.append(r"\midrule")

# ------------------------------------------------------------
# BODY
# ------------------------------------------------------------

for _, row in df.iterrows():

    design = latex_escape(row["design"])

    one_bit = int(row["#1-bit FFs"])
    insts = int(row["#inst"])

    ratio = row["ff_ratio"]

    latex.append(
        f"{design} & "
        f"{one_bit} & "
        f"{insts} & "
        f"{ratio:.3f} \\\\"
    )

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"\end{table}")

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

os.makedirs(
    os.path.dirname(OUTPUT_TEX),
    exist_ok=True
)

with open(OUTPUT_TEX, "w") as f:
    f.write("\n".join(latex))

print(f"Saved: {OUTPUT_TEX}")