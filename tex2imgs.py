import os
import re
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union

import matplotlib.pyplot as plt
import pandas as pd
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
        \usepackage{caption}
        \usepackage{subcaption}
        \usepackage{graphicx}
        \usepackage{mathtools}
        \usepackage{pgfplots}
        \usepackage{pifont}
        \usepackage{tikz}
        \usepackage{tkz-euclide}
        \usetikzlibrary{calc}
        \usepackage{xcolor}
        \usepackage{wrapfig}
        \setlength\parindent{0pt}
        \setlength\textwidth{$in}
        \linespread{1.5}
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
    # Check if the text overflows the image
    if bbox.width > image_size_px[0]:
        raise ValueError(f"The text overflows the image width:\n{latex_expression}")
    plt.savefig(image_name)
    plt.close()


def process_question(
    lines: List[str],
    fout: str,
    separate_choices: bool = False,
    score_good: float = 1,
    score_bad: Optional[float] = None,
) -> Dict:
    """
    Process a question and its choices.

    Parameters
    ----------
    lines : List[str]
        List of lines of the question.
    fout : str
        Output filename (for the images).
    separate_choices : bool, optional
        Whether to create a separate image for each choice.
    score_good : float, optional
        Score for the correct answer.
    score_bad : float, optional
        Score for the wrong answers.
        If None, it will be set to -score_good / number_of_choices.
    """
    fout_question = Path(fout + ".png")
    dict_question = {"Item": fout_question.stem}
    idx_choice = 0
    ls_question = []
    for line in lines:
        if line.startswith("%"):
            continue
        elif line.startswith("\\choice"):
            idx_choice += 1

            if "\\choice[!]" in line:
                extra = "_correct"
                score = score_good
            else:
                extra = ""
                score = score_bad
            dict_question[f"Score for answer {idx_choice}"] = score

            if separate_choices:
                # Extract the text inside "{}"
                txt = line[line.find("{") + 1 : line.rfind("}")]
                fout_choice = Path(fout + f"_A{idx_choice}{extra}.png")
                dict_question[f"answer_{idx_choice}"] = fout_choice.stem
                latex2image(txt, fout_choice)
            else:
                # Remove the "\\choice[!]"
                line = line.replace("\\choice[!]", "").replace("\\choice", "")
                # Add the letter and a new line
                line = r"\\\\ \textbf{" + chr(65 + idx_choice - 1) + r")} " + line
                ls_question.append(line)
        else:
            ls_question.append(line)
    # Remove comments "%" at the end of every line, unless they are "\%"
    ls_question = [re.sub(r"(?<!\\)%.*", "", line) for line in ls_question]
    # Extract the question
    txt = "".join(ls_question)
    latex2image(txt, fout_question)
    # Replace the None in the dictionary by the formula below
    score_bad = round(-score_good / idx_choice, 2)
    for k, v in dict_question.items():
        if v is None:
            dict_question[k] = score_bad
    return dict_question


def read_tex(
    path_file: Union[str, List[str]],
    path_output: str,
    separate_choices: bool = False,
    score_good: float = 1,
    score_bad: Optional[float] = None,
):
    """
    Read a LaTeX file and extract the questions and choices.

    Parameters
    ----------
    path_file : str
        Path to the LaTeX file.
    path_output : str
        Path to the output folder or zip file.
    separate_choices : bool, optional
        Whether to create a separate image for each choice.
    score_good : float, optional
        Score for the correct answer.
    score_bad : float, optional
        Score for the wrong answers.
        If None, it will be set to -score_good / number_of_choices.
    """
    if path_output.endswith(".zip"):
        out_folder = path_output[:-4]
    else:
        out_folder = path_output

    if not os.path.exists(out_folder):
        os.makedirs(out_folder)

    if isinstance(path_file, str):
        with open(path_file, "r") as f:
            lines = f.readlines()
    else:
        # Assume it is a list of strings
        lines = path_file

    ls_dict_questions = []
    question_index = 0
    version_index = None
    section = None
    subsection = None
    for idx, line in enumerate(lines):
        line = line.strip()
        if line.startswith("%#original"):
            version_index = 0
        if line.startswith("%"):
            continue
        elif line.startswith("\\begin{multiplechoice}"):
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
            if version_index is None:
                question_index += 1
            elif version_index == 0:
                question_index += 1
                version_index += 1
            else:
                version_index += 1
            line = line.replace("\\begin{question}", "").strip()
            question_lines = [line]  # Reset
        elif line.endswith("\\end{question}"):
            line = line.replace("\\end{question}", "").strip()
            question_lines.append(line)
            fout = out_folder + "/"
            if section is not None:
                fout += f"{section}_"
            if subsection is not None:
                fout += f"{subsection}_"
            fout += f"Q{question_index:03d}"
            if version_index is not None:
                fout += f"_V{version_index:02d}"
            try:
                dict_question = process_question(
                    question_lines,
                    fout,
                    separate_choices=separate_choices,
                    score_good=score_good,
                    score_bad=score_bad,
                )
                ls_dict_questions.append(dict_question)
            except Exception as e:
                print(f"Error in question {fout}, line {idx}")
                # Save a traceback
                with open(out_folder + f"/error_{idx:04d}.txt", "w") as f:
                    f.write(str(e))
        elif question_index > 0:
            question_lines.append(line)
        # Yield the progress (this makes a generator)
        yield idx / len(lines)

    # Turn the list of dictionaries into a DataFrame
    df = pd.DataFrame(ls_dict_questions)
    df.to_csv(out_folder + "/questions.csv", index=False)

    # Zip the images
    if path_output.endswith(".zip"):
        with zipfile.ZipFile(path_output, "w") as zipf:
            for root, dirs, files in os.walk(out_folder):
                for file in files:
                    if (
                        file.endswith(".png")
                        or file.endswith(".csv")
                        or file.endswith(".txt")
                    ):
                        zipf.write(os.path.join(root, file), file)
                        os.remove(os.path.join(root, file))
        # Remove the folder
        os.rmdir(out_folder)


def main(
    file: str = "examples/real.tex",
    output: str = "output",
    separate: bool = False,
    good: float = 1,
    bad: Optional[float] = None,
):
    gen = read_tex(
        file,
        output,
        separate_choices=separate,
        score_good=good,
        score_bad=bad,
    )
    for p in gen:
        sys.stdout.write("\r%d%%" % (p * 100))
        sys.stdout.flush()


if __name__ == "__main__":
    typer.run(main)
