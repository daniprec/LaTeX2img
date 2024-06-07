import os
import re
from typing import List, Tuple

import matplotlib.pyplot as plt
import typer


def latex2image(
    latex_expression: str,
    image_name: str,
    image_size_px: Tuple[int, int] = (1000, 200),
    fontsize: int = 16,
    dpi: int = 200,
):
    """
    A simple function to generate an image from a LaTeX language string.
    Source: https://medium.com/@ealbanez/how-to-easily-convert-latex-to-images-with-python-9062184dc815

    Parameters
    ----------
    latex_expression : str
        Equation in LaTeX markup language.
    image_name : str or path-like
        Full path or filename including filetype.
        Accepeted filetypes include: png, pdf, ps, eps and svg.
    image_size_in : tuple of float, optional
        Image size. Tuple which elements, in inches, are: (width_in, vertical_in).
    fontsize : float or str, optional
        Font size, that can be expressed as float or
        {'xx-small', 'x-small', 'small', 'medium', 'large', 'x-large', 'xx-large'}.
    """
    image_size_in = (image_size_px[0] / dpi, image_size_px[1] / dpi)

    fig = plt.figure(figsize=image_size_in, dpi=dpi)
    # Runtime Configuration Parameters
    plt.rc("text", usetex=True)
    plt.rc("font", family="cmu-serif")
    w = str(image_size_in[0] * 0.9)
    preamble = r"""
        \usepackage{amsmath}
        \usepackage{amssymb}
        \usepackage{pifont}
        \usepackage{xcolor}
        \usepackage{tkz-euclide}
        \usepackage{graphicx}
        \setlength\parindent{0pt}
        \setlength\textwidth{$in}
        """.replace(
        "$", w
    )
    plt.rc("text.latex", preamble=preamble)

    text = fig.text(
        x=0.05,
        y=0.5,
        s=latex_expression,
        horizontalalignment="left",
        verticalalignment="center",
        fontsize=fontsize,
    )
    renderer = fig.canvas.get_renderer()
    bbox = text.get_window_extent(renderer=renderer)
    fig.set_size_inches(image_size_in[0], bbox.height / dpi + 0.2)
    plt.savefig(image_name)
    plt.close()


def process_question(lines: List[str], fout: str):
    """
    Process a question and its choices.
    """
    idx_choice = 0
    ls_question = []
    for line in lines:
        if line.startswith("%"):
            continue
        elif line.startswith("\\choice"):
            idx_choice += 1
            if "\\choice[!]" in line:
                extra = "_correct"
            else:
                extra = ""
            # Extract the text inside "{}"
            txt = line[line.find("{") + 1 : line.rfind("}")]
            latex2image(txt, fout + f"_A{idx_choice}{extra}.png")
        else:
            ls_question.append(line)
    # Extract the question
    txt = "".join(ls_question)
    latex2image(txt, fout + ".png")


def read_tex(path_file: str, path_output: str):
    """
    Read a LaTeX file and extract the questions and choices.
    """
    if not os.path.exists(path_output):
        os.makedirs(path_output)

    with open(path_file, "r") as f:
        lines = f.readlines()

    question_index = 0
    section = None
    subsection = None
    for line in lines:
        line = line.strip()
        if line.startswith("\\begin{multiplechoice}"):
            # Example: \begin{multiplechoice}[title={Algebra}, resetcounter=no]
            section = re.search(r"title={(.+?)}", line).group(1)
            section = section.replace(" ", "_")
            question_index = 0  # Reset
            subsection = None  # Reset
        elif line.startswith("\\subsection{"):
            subsection = re.search(r"subsection{(.+?)}", line).group(1)
            subsection = subsection.replace(" ", "_")
            question_index = 0  # Reset
        elif line.startswith("\\begin{question}"):
            question_index += 1
            line = line.replace("\\begin{question}", "").strip()
            question_lines = [line]  # Reset
        elif line.endswith("\\end{question}"):
            line = line.replace("\\end{question}", "").strip()
            question_lines.append(line)
            fout = path_output + "/"
            if section is not None:
                fout += f"{section}_"
            if subsection is not None:
                fout += f"{subsection}_"
            fout += f"Q{question_index:03d}"
            process_question(question_lines, fout)
        elif question_index > 0:
            question_lines.append(line)


def main(file: str = "examples/examplea.tex", output: str = "output"):
    read_tex(file, output)


if __name__ == "__main__":
    typer.run(main)
