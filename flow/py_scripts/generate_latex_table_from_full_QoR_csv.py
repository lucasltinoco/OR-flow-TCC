import pandas as pd
import re
import os

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"
OUTPUT_TEX = "../tables/results_unified.tex"

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

TARGET_ALPHA = 8

# ------------------------------------------------------------
# METRICS
# value_col, pct_col, display_name
# ------------------------------------------------------------

metrics = [
    ("#1-bit FFs", None, "\#1b"),
    ("#2-bit FFs", None, "\#2b"),
    ("#4-bit FFs", None, "\#4b"),
    (lambda r: round((((r["#1-bit FFs"] + r["#2-bit FFs"] + r["#4-bit FFs"]) / r["#inst"]) * 100), 1), None, "FF \%"),
    
    ("switching_power", "switching_power_%", "Swit. P (mW)"),
    ("tot_power", "tot_power_%",             "Total P (mW)"),

    ("WNS", "WNS_%", "WS (ps)"),
    # ("TNS", "TNS_%", "TS (ps)"),

    ("area", "area_%", "Area ($\\mu m^2$)"),
    ("#clk bufs", "#clk bufs_%", "\#clk bufs")
]

# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

df = pd.read_csv(CSV_PATH)

# ------------------------------------------------------------
# FILTER ONLY TARGET ALPHA + NC
# ------------------------------------------------------------

def keep_row(flow):
    flow = str(flow).strip().lower()
    if flow == "nc":
        return True

    alpha_match = re.search(r'alpha[_=](\d+)', flow)
    if not alpha_match:
        return False

    alpha = int(alpha_match.group(1))
    if alpha != TARGET_ALPHA:
        return False

    return (
        "sftray" in flow
        or "ours" in flow
        or "baseline" in flow
        or "modified" in flow
    )

df = df[df["flow"].apply(keep_row)]

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
# FLOW FORMATTER
# ------------------------------------------------------------

def format_flow(flow):
    flow_original = str(flow)
    flow_lower = flow_original.lower()

    if flow_lower in ["nc", "base"]:
        return "NC (abs.)"

    alpha_match = re.search(r'alpha[_=](\d+)', flow_lower)
    if "sftray" in flow_lower or "baseline" in flow_lower:
        return rf"SFTray"

    if "ours" in flow_lower or "modified" in flow_lower:
        return rf"Ours"

    return latex_escape(flow_original)

# ------------------------------------------------------------
# UNIT CONVERSION
# ------------------------------------------------------------

def convert_units(value, value_col):
    if pd.isna(value):
        return value

    # Apenas converte unidades se a coluna for uma string (métrica padrão)
    if isinstance(value_col, str):
        # W -> mW
        if value_col in ["switching_power", "tot_power"]:
            value *= 1000.0
        # DBU -> um
        if value_col == "WL":
            value /= 1000.0

    return value

# ------------------------------------------------------------
# FORMATTERS
# ------------------------------------------------------------

def format_absolute(value, value_col=None):
    if pd.isna(value):
        return ""

    value = convert_units(value, value_col)

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(int(value))


def format_percentage(value):
    if pd.isna(value):
        return ""
    return f"{float(value):+.2f}%"

# ------------------------------------------------------------
# SORT HELPERS
# ------------------------------------------------------------

def flow_order(flow):
    flow = str(flow).lower()
    if flow in ["nc", "base"]:
        return 0
    if "sftray" in flow or "baseline" in flow:
        return 1
    if "ours" in flow or "modified" in flow:
        return 2
    return 99

# ------------------------------------------------------------
# GET DESIGN ORDER (#1-bit FFs / #inst DESC)
# ------------------------------------------------------------

design_order = {}
for design in df["design"].unique():
    nc_rows = df[
        (df["design"] == design)
        & (df["flow"].str.lower() == "nc")
    ]
    if len(nc_rows) == 0:
        design_order[design] = 0
        continue
    design_order[design] = nc_rows.iloc[0]["#1-bit FFs"] / nc_rows.iloc[0]["#inst"]

# ------------------------------------------------------------
# SORT DATAFRAME
# ------------------------------------------------------------

df["_design_order"] = df["design"].map(design_order)
df["_flow_order"] = df["flow"].map(flow_order)

df = df.sort_values(
    by=["_design_order", "design", "_flow_order"],
    ascending=[False, True, True]
)
df = df.drop(columns=["_design_order", "_flow_order"])

# ------------------------------------------------------------
# LATEX TABLE
# ------------------------------------------------------------

latex = []
latex.append(r"\begin{table*}[t]")
latex.append(r"\centering")
latex.append(
    rf"\caption{{Comparison of MBFF clustering strategies "
    rf"for $\alpha = {TARGET_ALPHA}$ and $\beta = 0.1$. "
    r"NC rows present absolute values, while SFTray and Ours "
    r"show percentage variation relative to NC (except for \#1b, \#2b and \#4b).}}"
)
latex.append(rf"\label{{tab:results_alpha_{TARGET_ALPHA}}}")
latex.append(r"\resizebox{\textwidth}{!}{")

# ------------------------------------------------------------
# COLUMN FORMAT
# ------------------------------------------------------------

col_fmt = (
    "ll|"   # Design | Condition |
    "cccc|" # Physical + FF Ratio |
    "ccc|"   # Power + Timing
    "cc"     # Area + WL
)

latex.append(r"\begin{tabular}{" + col_fmt + "}")
latex.append(r"\toprule")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

header = [r"Design", r"Version"]
for _, _, name in metrics:
    header.append(name)

latex.append(" & ".join(header) + r" \\")
latex.append(r"\midrule")

# ------------------------------------------------------------
# BODY
# ------------------------------------------------------------

grouped = df.groupby("design", sort=False)

for design, group in grouped:
    group = group.sort_values(
        by="flow",
        key=lambda col: col.map(flow_order)
    )

    rows = list(group.iterrows())
    nrows = len(rows)
    first = True

    for _, row in rows:
        flow_lower = str(row["flow"]).lower()
        entries = []

        # ----------------------------------------------------
        # MULTIROW DESIGN
        # ----------------------------------------------------
        if first:
            entries.append(rf"\multirow{{{nrows}}}{{*}}{{{latex_escape(design)}}}")
            first = False
        else:
            entries.append("")

        entries.append(format_flow(row["flow"]))

        # ----------------------------------------------------
        # METRICS
        # ----------------------------------------------------
        is_nc = flow_lower == "nc"

        for value_col, pct_col, _ in metrics:
            
            # Extrai o dado original caso a coluna seja uma função/lambda
            raw_val = value_col(row) if callable(value_col) else row[value_col]

            # ------------------------------------------------
            # NC -> ABSOLUTE VALUE
            # ------------------------------------------------
            if is_nc:
                value = format_absolute(raw_val, value_col)
                entries.append(latex_escape(value))

            # ------------------------------------------------
            # SFTRAY / OURS -> PERCENTAGE (ou absoluto se pct_col for None)
            # ------------------------------------------------
            else:
                if pct_col is None or pct_col not in df.columns:
                    value = format_absolute(raw_val, value_col)
                    entries.append(latex_escape(value))
                else:
                    pct_value = row[pct_col]
                    entries.append(latex_escape(format_percentage(pct_value)))

        latex.append(" & ".join(entries) + r" \\")

    latex.append(r"\midrule")

# ------------------------------------------------------------
# FOOTER
# ------------------------------------------------------------

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"}")
latex.append(r"\end{table*}")

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)
with open(OUTPUT_TEX, "w") as f:
    f.write("\n".join(latex))

print(f"Saved: {OUTPUT_TEX}")