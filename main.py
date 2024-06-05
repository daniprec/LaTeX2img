import os
from typing import List

import matplotlib
import matplotlib.pyplot as plt

def latex2image(
    latex_expression: str,
    image_name: str,
    image_size_px=(1000, 200),
    fontsize=16,
    dpi=200,
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

    Returns
    -------
    fig : object
        Matplotlib figure object from the class: matplotlib.figure.Figure.

    """
    image_size_in = (image_size_px[0] / dpi, image_size_px[1] / dpi)
    while latex_expression.endswith("\n") or latex_expression.endswith(" "):
        latex_expression = latex_expression.rstrip()
    while latex_expression.startswith("\n") or latex_expression.startswith(" "):
        latex_expression = latex_expression.lstrip()

    fig = plt.figure(figsize=image_size_in, dpi=dpi)
    # Runtime Configuration Parameters
    plt.rc("text", usetex=True)
    plt.rc("font", family="cmu-serif")
    w = str(image_size_in[0] * 0.9)
    preamble = r"""
        \usepackage{amsmath}
        \setlength\parindent{0pt}
        \setlength\textwidth{$in}
        """.replace("$", w)
    plt.rc("text.latex", preamble=preamble)

    try:
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
        scale = fontsize**(1/2) / dpi
        fig.set_size_inches(image_size_in[0], scale * bbox.height)
        plt.savefig(image_name)
        plt.close()
    except Exception as e:
        print(f"\n---\nError in latex2image: {image_name}")
        print(repr(e))
        return None


def process_question(lines: List[str], fout: str):
    idx_choice = 0
    ls_question = []
    for line in lines:
        if line.startswith("%"):
            continue
        elif line.strip().startswith("\\choice"):
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
                fout = path_output + f"/Q{question_index:03d}"
                process_question(lines[start_index + 1 : end_index], fout)
                start_index = None
                end_index = None


if __name__ == "__main__":
    read_tex("examples/examplea.tex", "output")
