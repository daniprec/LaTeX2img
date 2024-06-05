import os
from typing import List

import matplotlib.pyplot as plt


def plot_expression(latex_expression: str):
    """
    Source: https://medium.com/@ealbanez/how-to-easily-convert-latex-to-images-with-python-9062184dc815
    """
    # Ensure the expression is an r-string
    latex_expression = r"$" + latex_expression + r"$"
    text = plt.text(
        x=0.5,  # x-coordinate to place the text
        y=0.5,  # y-coordinate to place the text
        s=latex_expression,
        horizontalalignment="center",
        verticalalignment="center",
        fontsize=16,
    )
    return text


def process_question(lines: List[str], fout: str):
    text = " ".join(lines)
    # Caught the equations encapsulated by "$" or "\[\]" or "\begin{equation}"
    equations = [
        eq.strip() for eq in text.split("$")[1:] if eq.strip() and eq.strip()[0] != "\\"
    ]
    for idx, eq in enumerate(equations):
        plot_expression(eq)
        plt.savefig(fout + f"_equation_{idx:03d}.png")
        plt.close()


def read_tex(path_file: str, path_output: str):
    if not os.path.exists(path_output):
        os.makedirs(path_output)

    with open(path_file, "r") as f:
        lines = f.readlines()
        question_index = 0
        start_index = None
        end_index = None
        for i, line in enumerate(lines):
            if line.strip() == "\\begin{question}":
                question_index += 1
                start_index = i
            elif line.strip() == "\\end{question}":
                end_index = i
            if start_index is not None and end_index is not None:
                fout = path_output + f"/question_{question_index:03d}"
                process_question(lines[start_index : end_index + 1], fout)
                start_index = None
                end_index = None


if __name__ == "__main__":
    read_tex("examples/examplea.tex", "output")
