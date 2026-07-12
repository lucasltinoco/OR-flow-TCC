import pandas as pd
import re
import os

CSV_PATH_V1 = "../tables/final_results_pct_vs_nc.csv"
CSV_PATH_V2 = "../tables/final_results_pct_vs_nc_v3.csv"

df_v1 = pd.read_csv(CSV_PATH_V1)
df_v2 = pd.read_csv(CSV_PATH_V2)

# SFTray + Ours v1
df_v1["version_group"] = "v1"

# SFTray + Ours v2
df_v2["version_group"] = "v2"

df = pd.concat(
    [df_v1, df_v2],
    ignore_index=True
)

df = df.drop_duplicates(
    subset=["design", "flow"],
    keep="first"
)

OUTPUT_TEX = "../tables/results_varying_alpha_all_versions.tex"

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

ALPHAS = [2, 4, 8, 16, 67, 130, 193, 256]
DESIGNS_PER_TABLE = 2

# ------------------------------------------------------------
# METRICS
# value_col, pct_col, display_name
# ------------------------------------------------------------
def ff_ratio(row):
    return (
        (row["#1-bit FFs"] +
         row["#2-bit FFs"] +
         row["#4-bit FFs"])
        / row["#inst"] * 100
    )

metrics = [
    ("#1-bit FFs", None, "\#1b"),
    ("#2-bit FFs", None, "\#2b"),
    ("#4-bit FFs", None, "\#4b"),
    (ff_ratio, None, "FF \%"),
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

# df = pd.read_csv(CSV_PATH)

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


def is_ours_v1(flow, version_group=None):
    flow = str(flow).lower()

    return (
        "ours" in flow
        and version_group == "v1"
    )


def is_ours_v2(flow, version_group=None):
    flow = str(flow).lower()

    return (
        "ours" in flow
        and version_group == "v2"
    )

def convert_units(value, value_col):
    if pd.isna(value):
        return value

    # Apenas converte se for uma string (métrica original)
    if isinstance(value_col, str):
        # W -> mW
        if value_col in ["switching_power", "tot_power"]:
            value *= 1000.0
        # DBU -> um
        if value_col == "WL":
            value /= 1000.0

    return value

def is_better(metric_name, ours, sftray, nc_wns=None):
    """
    Returns True if Ours is better than SFTray.
    """

    if pd.isna(ours) or pd.isna(sftray):
        return False

    # More reduction is better
    if metric_name in [
        "switching_power_%",
        "tot_power_%",
        "area_%",
        "#clk bufs_%"
    ]:
        return ours < sftray

    # WNS special case
    if metric_name == "WNS_%":

        # NC timing violation
        if nc_wns is not None and nc_wns < 0:
            return ours < sftray

        # NC timing clean
        return ours > sftray

    return False


def latex_bold(text):
    return rf"\textbf{{{text}}}"


def format_absolute(value, value_col):
    if pd.isna(value):
        return ""

    value = convert_units(value, value_col)
    
    if callable(value_col) and value_col.__name__ == "ff_ratio":
        return f"{float(value):.1f}%"

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

    if is_ours_v1(flow):
        return 2

    if is_ours_v2(flow):
        return 3

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

    if (
        is_sftray(flow)
        or is_ours_v1(flow, row["version_group"])
        or is_ours_v2(flow, row["version_group"])
    ):
        valid_rows.append(True)
    else:
        valid_rows.append(False)

df = df[valid_rows]

# ------------------------------------------------------------
# DESIGN ORDER (#1b / #inst DESC)
# + TIMING CLEAN DESIGNS LAST
# ------------------------------------------------------------

design_order = {}
positive_ws_designs = []

for design in df["design"].unique():
    nc_rows = df[
        (df["design"] == design)
        & (df["flow"].str.lower() == "nc")
    ]

    if len(nc_rows) == 0:
        design_order[design] = 0
        continue

    nc_row = nc_rows.iloc[0]

    design_order[design] = (
        nc_row["#1-bit FFs"] / nc_row["#inst"]
    )

    # WS > 0 -> move to end
    if nc_row["WNS"] > 0:
        positive_ws_designs.append(design)

# ------------------------------------------------------------
# SORT
# ------------------------------------------------------------

df["_design_order"] = df["design"].map(design_order)

df["_positive_ws"] = df["design"].apply(
    lambda d: 1 if d in positive_ws_designs else 0
)

df["_alpha"] = df["flow"].apply(
    lambda x: extract_alpha(x) if extract_alpha(x) is not None else -1
)

df["_flow_order"] = df["flow"].map(flow_order)

df = df.sort_values(
    by=[
        "_positive_ws",      # negative WS first
        "_design_order",
        "design",
        "_alpha",
        "_flow_order"
    ],
    ascending=[
        True,
        False,
        True,
        True,
        True
    ]
)

# ------------------------------------------------------------
# LATEX TABLE
# ------------------------------------------------------------

def begin_table(table_idx):
    latex = []

    latex.append(r"\begin{table*}[t]")
    latex.append(r"\centering")

    latex.append(
        rf"\caption{{Comparison of MBFF clustering strategies "
        rf"for varying $\alpha$ values with $\beta=0.1$ "
        rf"(Part {table_idx}).}}"
    )

    latex.append(
        rf"\label{{tab:varying_alpha_part{table_idx}}}"
    )

    latex.append(r"\resizebox{\textwidth}{!}{")

    col_fmt = (
        "ll|"
        "cccc|"
        "ccc|"
        "cc"
    )

    latex.append(r"\begin{tabular}{" + col_fmt + "}")
    latex.append(r"\toprule")

    header = [r"Design", r"Version"]

    for _, _, name in metrics:
        header.append(name)

    latex.append(" & ".join(header) + r" \\")
    latex.append(r"\midrule")

    return latex

def end_table(latex):
    latex.append(r"\bottomrule")
    latex.append(r"\end{tabular}")
    latex.append(r"}")
    latex.append(r"\end{table*}")
    return latex

all_tables = []

table_idx = 1
latex = begin_table(table_idx)

design_counter = 0

# ------------------------------------------------------------
# ORDERED DESIGN LIST
# ------------------------------------------------------------

negative_designs = []
positive_designs = []

for design in df["design"].unique():

    nc_row = df[
        (df["design"] == design)
        & (df["flow"].str.lower() == "nc")
    ].iloc[0]

    if nc_row["WNS"] > 0:
        positive_designs.append(design)
    else:
        negative_designs.append(design)

ordered_designs = negative_designs + positive_designs

# ------------------------------------------------------------
# BODY
# ------------------------------------------------------------

for idx, design in enumerate(ordered_designs):
    design_df = df[df["design"] == design]
    nc_rows = design_df[design_df["flow"].str.lower() == "nc"]
    
    if idx > 0 and idx % DESIGNS_PER_TABLE == 0:
        latex = end_table(latex)
        all_tables.extend(latex)

        table_idx += 1
        latex = begin_table(table_idx)

    if len(nc_rows) == 0:
        continue

    nc_row = nc_rows.iloc[0]

    # count rows for multirow
    nrows = 1 + 3 * len(ALPHAS)
    first_design_row = True

    # --------------------------------------------------------
    # NC ROW
    # --------------------------------------------------------
    entries = []
    entries.append(rf"\multirow{{{nrows}}}{{*}}{{{latex_escape(design)}}}")
    entries.append("NC (abs.)")

    for value_col, _, _ in metrics:
        raw_val = value_col(nc_row) if callable(value_col) else nc_row[value_col]
        value = format_absolute(raw_val, value_col)
        entries.append(latex_escape(value))

    latex.append(" & ".join(entries) + r" \\")
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

        ours_v1_rows = alpha_df[
            alpha_df.apply(
                lambda r: is_ours_v1(
                    r["flow"],
                    r["version_group"]
                ),
                axis=1
            )
        ]

        ours_v2_rows = alpha_df[
            alpha_df.apply(
                lambda r: is_ours_v2(
                    r["flow"],
                    r["version_group"]
                ),
                axis=1
            )
        ]

        # ----------------------------------------------------
        # SFTRAY
        # ----------------------------------------------------
        if len(sftray_rows) > 0:
            row = sftray_rows.iloc[0]
            entries = [""]
            entries.append(rf"SFTray ($\alpha$={alpha})")

            for value_col, pct_col, _ in metrics:
                raw_val = value_col(row) if callable(value_col) else row[value_col]
                
                if pct_col is None or pct_col not in df.columns:
                    value = format_absolute(raw_val, value_col)
                    entries.append(latex_escape(value))
                else:
                    entries.append(latex_escape(format_percentage(row[pct_col])))

            latex.append(" & ".join(entries) + r" \\")

        # ----------------------------------------------------
        # OURS
        # ----------------------------------------------------
        if len(ours_v1_rows) > 0:
            row = ours_v1_rows.iloc[0]
            entries = [""]
            entries.append(
                rf"Ours v1 ($\alpha$={alpha})"
            )

            for value_col, pct_col, metric_name in metrics:
                raw_val = (
                    value_col(row)
                    if callable(value_col)
                    else row[value_col]
                )

                if pct_col is None or pct_col not in df.columns:

                    value = format_absolute(raw_val, value_col)

                    entries.append(
                        latex_escape(value)
                    )

                else:

                    value_str = format_percentage(
                        row[pct_col]
                    )

                    # compare against SFTray
                    bold = False

                    if len(sftray_rows) > 0:

                        sftray_row = sftray_rows.iloc[0]

                        bold = is_better(
                            pct_col,
                            row[pct_col],
                            sftray_row[pct_col],
                            nc_row["WNS"]
                        )

                    if bold:
                        value_str = latex_bold(latex_escape(value_str))
                    else:
                        value_str = latex_escape(value_str)

                    entries.append(value_str)

            latex.append(" & ".join(entries) + r" \\")
                
        # ----------------------------------------------------
        # OURS V2
        # ----------------------------------------------------
        if len(ours_v2_rows) > 0:

            row = ours_v2_rows.iloc[0]

            entries = [""]
            entries.append(
                rf"Ours v2 ($\alpha$={alpha})"
            )

            for value_col, pct_col, metric_name in metrics:

                raw_val = (
                    value_col(row)
                    if callable(value_col)
                    else row[value_col]
                )

                if pct_col is None or pct_col not in df.columns:

                    value = format_absolute(
                        raw_val,
                        value_col
                    )

                    entries.append(
                        latex_escape(value)
                    )

                else:

                    value_str = format_percentage(
                        row[pct_col]
                    )

                    entries.append(
                        latex_escape(value_str)
                    )

            latex.append(
                " & ".join(entries) + r" \\"
            )

            if alpha != ALPHAS[-1]:
                latex.append(r"\addlinespace[0.5em]")
    # # extra separator between violating and timing-clean designs
    # if (
    #     design == negative_designs[-1]
    #     and len(positive_designs) > 0
    # ):
    #     latex.append(r"\midrule")
    #     latex.append(r"\midrule")
    # else:
    latex.append(r"\midrule")
        
    design_counter += 1

latex = end_table(latex)
all_tables.extend(latex)

# ------------------------------------------------------------
# SAVE
# ------------------------------------------------------------

os.makedirs(os.path.dirname(OUTPUT_TEX), exist_ok=True)
with open(OUTPUT_TEX, "w") as f:
    f.write("\n\n".join(all_tables))

print(f"Saved: {OUTPUT_TEX}")