import pandas as pd
import re
import os

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"
OUTPUT_TEX = "../tables/results_varying_alpha.tex"

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

ALPHAS = [2, 4, 8, 16, 67, 130, 193, 256]

# ------------------------------------------------------------
# METRICS
# value_col, pct_col, display_name
# ------------------------------------------------------------

metrics = [
    ("switching_power", "switching_power_%", "Swit. P (mW)"),
    ("tot_power", "tot_power_%",             "Total P (mW)"),

    ("WNS", "WNS_%", "WNS (ns)"),
    ("TNS", "TNS_%", "TNS (ns)"),

    ("area", "area_%", "Area ($\\mu m^2$)"),
    ("WL", "WL_%",     "WL ($\\mu m$)"),

    ("#clk bufs", "#clk bufs_%", "\\#clk bufs"),

    ("#1-bit FFs", None, "\\#1b"),
    ("#2-bit FFs", None, "\\#2b"),
    ("#4-bit FFs", None, "\\#4b"),
]

# ------------------------------------------------------------
# LOAD
# ------------------------------------------------------------

df = pd.read_csv(CSV_PATH)

# ------------------------------------------------------------
# HELPERS
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


def extract_alpha(flow):

    match = re.search(r'alpha[_=](\d+)', str(flow).lower())

    if match:
        return int(match.group(1))

    return None


def is_nc(flow):

    return str(flow).strip().lower() == "nc"


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


def convert_units(value, value_col):

    if pd.isna(value):
        return value

    # W -> mW
    if value_col in ["switching_power", "tot_power"]:
        value *= 1000.0

    # DBU -> um
    if value_col == "WL":
        value /= 1000.0

    return value


def format_absolute(value, value_col):

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


def flow_order(flow):

    if is_nc(flow):
        return 0

    if is_sftray(flow):
        return 1

    if is_ours(flow):
        return 2

    return 99

# ------------------------------------------------------------
# FILTER VALID ROWS
# ------------------------------------------------------------

valid_rows = []

for _, row in df.iterrows():

    flow = row["flow"]

    if is_nc(flow):
        valid_rows.append(True)
        continue

    alpha = extract_alpha(flow)

    if alpha not in ALPHAS:
        valid_rows.append(False)
        continue

    if is_sftray(flow) or is_ours(flow):
        valid_rows.append(True)
    else:
        valid_rows.append(False)

df = df[valid_rows]

# ------------------------------------------------------------
# DESIGN ORDER (#1b DESC)
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

    design_order[design] = nc_rows.iloc[0]["#1-bit FFs"]

# ------------------------------------------------------------
# SORT
# ------------------------------------------------------------

df["_design_order"] = df["design"].map(design_order)

df["_alpha"] = df["flow"].apply(
    lambda x: extract_alpha(x) if extract_alpha(x) is not None else -1
)

df["_flow_order"] = df["flow"].map(flow_order)

df = df.sort_values(
    by=[
        "_design_order",
        "design",
        "_alpha",
        "_flow_order"
    ],
    ascending=[
        False,
        True,
        True,
        True
    ]
)

# ------------------------------------------------------------
# LATEX TABLE
# ------------------------------------------------------------

latex = []

latex.append(r"\begin{table*}[t]")
latex.append(r"\centering")

latex.append(
    r"\caption{Comparison of MBFF clustering strategies "
    r"for varying $\alpha$ values ($\beta=0.1$). "
    r"NC rows present absolute values, while SFTray and Ours "
    r"show percentage variation relative to NC "
    r"(except for \#1b, \#2b and \#4b).}"
)

latex.append(r"\label{tab:varying_alpha}")

latex.append(r"\resizebox{\textwidth}{!}{")

# ------------------------------------------------------------
# COLUMN FORMAT
# ------------------------------------------------------------

col_fmt = (
    "ll|"
    "cc|"
    "cc|"
    "ccc|"
    "ccc"
)

latex.append(r"\begin{tabular}{" + col_fmt + "}")
latex.append(r"\toprule")

# ------------------------------------------------------------
# HEADER
# ------------------------------------------------------------

header = [
    r"Design",
    r"Condition"
]

for _, _, name in metrics:
    header.append(name)

latex.append(" & ".join(header) + r" \\")
latex.append(r"\midrule")

# ------------------------------------------------------------
# BODY
# ------------------------------------------------------------

for design in df["design"].unique():

    design_df = df[df["design"] == design]

    nc_rows = design_df[
        design_df["flow"].str.lower() == "nc"
    ]

    if len(nc_rows) == 0:
        continue

    nc_row = nc_rows.iloc[0]

    # count rows for multirow
    nrows = 1 + 2 * len(ALPHAS)

    first_design_row = True

    # --------------------------------------------------------
    # NC ROW
    # --------------------------------------------------------

    entries = []

    entries.append(
        rf"\multirow{{{nrows}}}{{*}}{{{latex_escape(design)}}}"
    )

    entries.append("NC")

    for value_col, _, _ in metrics:

        value = format_absolute(
            nc_row[value_col],
            value_col
        )

        entries.append(
            latex_escape(value)
        )

    latex.append(
        " & ".join(entries) + r" \\"
    )

    latex.append(r"\addlinespace[0.4em]")

    # --------------------------------------------------------
    # ALPHA SWEEPS
    # --------------------------------------------------------

    for alpha in ALPHAS:

        alpha_df = design_df[
            design_df["_alpha"] == alpha
        ]

        sftray_rows = alpha_df[
            alpha_df["flow"].apply(is_sftray)
        ]

        ours_rows = alpha_df[
            alpha_df["flow"].apply(is_ours)
        ]

        # ----------------------------------------------------
        # SFTRAY
        # ----------------------------------------------------

        if len(sftray_rows) > 0:

            row = sftray_rows.iloc[0]

            entries = [""]

            entries.append(
                rf"SFTray ($\alpha$={alpha})"
            )

            for value_col, pct_col, _ in metrics:

                if pct_col is None:

                    value = format_absolute(
                        row[value_col],
                        value_col
                    )

                    entries.append(
                        latex_escape(value)
                    )

                else:

                    entries.append(
                        latex_escape(
                            format_percentage(
                                row[pct_col]
                            )
                        )
                    )

            latex.append(
                " & ".join(entries) + r" \\"
            )

        # ----------------------------------------------------
        # OURS
        # ----------------------------------------------------

        if len(ours_rows) > 0:

            row = ours_rows.iloc[0]

            entries = [""]

            entries.append(
                rf"Ours ($\alpha$={alpha})"
            )

            for value_col, pct_col, _ in metrics:

                if pct_col is None:

                    value = format_absolute(
                        row[value_col],
                        value_col
                    )

                    entries.append(
                        latex_escape(value)
                    )

                else:

                    entries.append(
                        latex_escape(
                            format_percentage(
                                row[pct_col]
                            )
                        )
                    )

            latex.append(
                " & ".join(entries) + r" \\"
            )
            
            latex.append(r"\addlinespace[0.3em]")
    latex.append(r"\midrule")

latex.append(r"\bottomrule")
latex.append(r"\end{tabular}")
latex.append(r"}")
latex.append(r"\end{table*}")

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