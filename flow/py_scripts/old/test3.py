import csv
import os

INPUT_CSV = "./tables/ff_distribution_asap7_expanded.csv"
OUTPUT_DIR = "./tables/per_circuit_tables"

ALPHAS = [2, 4, 8, 16, 67, 130, 193, 256]


def escape_latex(text):
    replacements = {
        "_": r"\_",
        "%": r"\%",
        "&": r"\&",
        "#": r"\#",
    }

    for k, v in replacements.items():
        text = text.replace(k, v)

    return text


def load_csv():
    with open(INPUT_CSV, newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def build_table(circuit_row):
    circuit = circuit_row["circuit"]

    latex = []

    latex.append(r"\begin{table}[ht]")
    latex.append(r"\centering")
    latex.append(r"\scriptsize")
    latex.append(r"\begin{tabular}{l" + "r" * (1 + 2 * len(ALPHAS)) + "}")
    latex.append(r"\hline")

    # HEADER
    header = [""]

    header.append("Base")

    for a in ALPHAS:
        header.append(f"Baseline $\\alpha={a}$")
        header.append(f"Modified $\\alpha={a}$")

    latex.append(" & ".join(header) + r" \\")
    latex.append(r"\hline")

    # ---------- 1-bit ----------
    row_1b = ["#1-bit"]
    row_1b.append(circuit_row["base"])

    for a in ALPHAS:
        row_1b.append(circuit_row.get(f"baseline a={a} (1b)", ""))
        row_1b.append(circuit_row.get(f"modified a={a} (1b)", ""))

    latex.append(" & ".join(map(str, row_1b)) + r" \\")

    # ---------- 2-bit ----------
    row_2b = ["#2-bit"]
    row_2b.append("")

    for a in ALPHAS:
        row_2b.append(circuit_row.get(f"baseline a={a} (2b)", ""))
        row_2b.append(circuit_row.get(f"modified a={a} (2b)", ""))

    latex.append(" & ".join(map(str, row_2b)) + r" \\")

    # ---------- 4-bit ----------
    row_4b = ["#4-bit"]
    row_4b.append("")

    for a in ALPHAS:
        row_4b.append(circuit_row.get(f"baseline a={a} (4b)", ""))
        row_4b.append(circuit_row.get(f"modified a={a} (4b)", ""))

    latex.append(" & ".join(map(str, row_4b)) + r" \\")

    latex.append(r"\hline")
    latex.append(r"\end{tabular}")

    latex.append(
        rf"\caption{{Flip-flop distribution for {escape_latex(circuit)}.}}"
    )

    latex.append(
        rf"\label{{tab:{circuit.replace('_', '-')}}}"
    )

    latex.append(r"\end{table}")

    return "\n".join(latex)


def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    rows = load_csv()

    for row in rows:
        circuit = row["circuit"]

        latex = build_table(row)

        output_path = os.path.join(
            OUTPUT_DIR,
            f"{circuit}_ff_distribution.tex"
        )

        with open(output_path, "w") as f:
            f.write(latex)

        print(f"Saved: {output_path}")


if __name__ == "__main__":
    main()