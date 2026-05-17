import csv

INPUT_CSV = "./tables/ff_distribution_asap7_expanded.csv"
OUTPUT_TEX = "./tables/ff_distribution_asap7_expanded.tex"


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


def shorten_header(h):
    h = h.replace("baseline", "Base")
    h = h.replace("modified", "Mod")
    h = h.replace("(1b)", "1b")
    h = h.replace("(2b)", "2b")
    h = h.replace("(4b)", "4b")
    return h


def main():
    with open(INPUT_CSV, newline="") as f:
        rows = list(csv.reader(f))

    header = [shorten_header(h) for h in rows[0]]
    data = rows[1:]

    num_cols = len(header)

    latex = []

    latex.append(r"\begin{table*}[ht]")
    latex.append(r"\centering")
    latex.append(r"\scriptsize")
    latex.append(r"\resizebox{\textwidth}{!}{%")

    colspec = "l" + "r" * (num_cols - 1)

    latex.append(r"\begin{tabular}{" + colspec + "}")
    latex.append(r"\hline")

    latex.append(" & ".join(escape_latex(h) for h in header) + r" \\")
    latex.append(r"\hline")

    for row in data:
        escaped = [escape_latex(str(x)) for x in row]
        latex.append(" & ".join(escaped) + r" \\")

    latex.append(r"\hline")
    latex.append(r"\end{tabular}%")
    latex.append(r"}")
    latex.append(r"\caption{Flip-flop distribution across different alpha values.}")
    latex.append(r"\label{tab:ff_distribution}")
    latex.append(r"\end{table*}")

    with open(OUTPUT_TEX, "w") as f:
        f.write("\n".join(latex))

    print(f"Saved LaTeX table to: {OUTPUT_TEX}")


if __name__ == "__main__":
    main()