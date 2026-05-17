import pandas as pd
import re
import os

CSV_PATH = "../tables/final_results_pct_vs_nc.csv"
OUTPUT_DIR = "../tables/"

# ------------------------------------------------------------
# CONFIG
# ------------------------------------------------------------

TARGET_ALPHA = 256

TABLES = {
    "power": {
        "caption": "Power-related metrics relative to the non-clustered (NC) baseline",
        "metrics": [
            ("switching_power", "switching_power_%", "Switching Power (mW)"),
            ("tot_power", "tot_power_%", "Total Power (mW)"),
            ("#clk bufs", "#clk bufs_%", "Clock Buffers"),
        ]
    },

    "timing": {
        "caption": "Timing-related metrics relative to the non-clustered (NC) baseline",
        "metrics": [
            ("WNS", "WNS_%", "WNS (ns)"),
            ("TNS", "TNS_%", "TNS (ns)"),
        ]
    },

    "physical": {
        "caption": "Physical design metrics relative to the non-clustered (NC) baseline",
        "metrics": [
            ("area", "area_%", "Area ($\\mu m^2$)"),
            ("WL", "WL_%", "Wirelength ($\\mu m$)"),
            ("#inst", "#inst_%", "Instances"),
        ]
    },

    "mbff": {
        "caption": "MBFF composition for each clustering strategy",
        "metrics": [
            ("#1-bit FFs", None, "1-bit FFs"),
            ("#2-bit FFs", None, "2-bit FFs"),
            ("#4-bit FFs", None, "4-bit FFs"),
        ]
    }
}

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
        return "NC"

    alpha_match = re.search(r'alpha[_=](\d+)', flow_lower)
    alpha_txt = ""

    if alpha_match:
        alpha_txt = rf" ($\alpha$={alpha_match.group(1)})"

    if "sftray" in flow_lower or "baseline" in flow_lower:
        return "SFTray"

    if "ours" in flow_lower or "modified" in flow_lower:
        return "Ours"

    return latex_escape(flow_original)

# ------------------------------------------------------------
# FORMATTERS
# ------------------------------------------------------------

def format_value(value, value_col=None):

    if pd.isna(value):
        return ""

    # --------------------------------------------------------
    # UNIT CONVERSIONS
    # --------------------------------------------------------

    # W -> mW
    if value_col in ["switching_power", "tot_power"]:
        value *= 1000.0

    # DBU -> um
    if value_col == "WL":
        value /= 1000.0

    # --------------------------------------------------------

    if isinstance(value, float):
        return f"{value:.3f}"

    return str(value)


def format_pct(value):

    if pd.isna(value):
        return ""

    if isinstance(value, float):
        return f"{value:+.2f}"

    return str(value)

# ------------------------------------------------------------
# SORT
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
# GET DESIGN ORDER (#INST DESC)
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

    design_order[design] = nc_rows.iloc[0]["#inst"]

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
# GENERATE TABLES
# ------------------------------------------------------------

os.makedirs(OUTPUT_DIR, exist_ok=True)

for table_name, table_cfg in TABLES.items():

    metrics = table_cfg["metrics"]
    caption = table_cfg["caption"]

    latex = []

    latex.append(r"\begin{table*}[t]")
    latex.append(r"\centering")

    latex.append(
        rf"\caption{{{caption} for $\alpha = {TARGET_ALPHA}$ "
        r"and $\beta = 0.1$.}"
    )

    latex.append(
        rf"\label{{tab:{table_name}_alpha_{TARGET_ALPHA}}}"
    )

    # --------------------------------------------------------
    # MBFF TABLE
    # --------------------------------------------------------

    if table_name == "mbff":

        latex.append(r"\begin{tabular}{llccc}")
        latex.append(r"\toprule")

        latex.append(
            r"Design & Flow & 1-bit FFs & 2-bit FFs & 4-bit FFs \\"
        )

        latex.append(r"\midrule")

    # --------------------------------------------------------
    # OTHER TABLES
    # --------------------------------------------------------

    else:

        latex.append(r"\resizebox{\textwidth}{!}{")

        col_fmt = "ll" + ("cc" * len(metrics))

        latex.append(r"\begin{tabular}{" + col_fmt + "}")
        latex.append(r"\toprule")

        # ----------------------------------------------------
        # TOP HEADER
        # ----------------------------------------------------

        top = [
            r"\multirow{2}{*}{Design}",
            r"\multirow{2}{*}{Condition}"
        ]

        for _, _, name in metrics:
            top.append(
                rf"\multicolumn{{2}}{{c}}{{{name}}}"
            )

        latex.append(" & ".join(top) + r" \\")
        latex.append("")

        # ----------------------------------------------------
        # SECOND HEADER
        # ----------------------------------------------------

        second = ["", ""]

        for _ in metrics:
            second += ["Value", r"$\Delta$ (\%)"]

        latex.append(" & ".join(second) + r" \\")
        latex.append(r"\midrule")

    # --------------------------------------------------------
    # BODY
    # --------------------------------------------------------

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

            flow = format_flow(row["flow"])

            entries = []

            # ------------------------------------------------
            # MULTIROW DESIGN
            # ------------------------------------------------

            if first:
                entries.append(
                    rf"\multirow{{{nrows}}}{{*}}{{{latex_escape(design)}}}"
                )
                first = False
            else:
                entries.append("")

            entries.append(flow)

            # ------------------------------------------------
            # METRICS
            # ------------------------------------------------

            for value_col, pct_col, _ in metrics:

                value = format_value(
                    row[value_col],
                    value_col
                )

                # MBFF TABLE
                if pct_col is None:

                    entries.append(
                        latex_escape(value)
                    )

                # OTHER TABLES
                else:

                    pct = format_pct(row[pct_col])

                    entries.append(
                        latex_escape(value)
                    )

                    entries.append(
                        latex_escape(pct)
                    )

            latex.append(
                " & ".join(entries) + r" \\"
            )

        latex.append(r"\midrule")

    # --------------------------------------------------------
    # FOOTER
    # --------------------------------------------------------

    latex.append(r"\bottomrule")
    latex.append(r"\end{tabular}")

    if table_name != "mbff":
        latex.append(r"}")

    latex.append(r"\end{table*}")

    # --------------------------------------------------------
    # SAVE
    # --------------------------------------------------------

    output_path = os.path.join(
        OUTPUT_DIR,
        f"results_{table_name}_alpha_{TARGET_ALPHA}.tex"
    )

    with open(output_path, "w") as f:
        f.write("\n".join(latex))

    print(f"Saved: {output_path}")