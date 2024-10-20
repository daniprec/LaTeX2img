import json
import os
import re
import subprocess
import sys
import zipfile
from pathlib import Path
from typing import Dict, List, Optional, Union

import numpy as np
import pandas as pd
import typer
from pdf2image import convert_from_path
from PIL import ImageDraw, ImageFont

TXT_FULL = r"""
    \documentclass[$FONTSIZE$pt, aspectratio=$ASPECT$, fleqn]{beamer}
    \setbeamertemplate{navigation symbols}{}
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
    \linespread{$LINESPREAD$}

    \begin{document}

    """


def process_question(
    lines: List[str],
    fout: str,
    score_good: float = 1,
    score_bad: Optional[float] = None,
    score_noanswer: Optional[float] = None,
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
    score_noanswer : float, optional
        Score for not answering the question. This is added as a last option.
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
                score = score_good
            else:
                score = score_bad
            dict_question[f"Score for answer {idx_choice}"] = score

            # Remove the "\\choice[!]"
            line = line.replace("\\choice[!]", "").replace("\\choice", "")
            # Add the letter and a new line
            line = r"\\ \textbf{" + chr(65 + idx_choice - 1) + r")} " + line
            ls_question.append(line)
        else:
            ls_question.append(line)
    # Remove comments "%" at the end of every line, unless they are "\%"
    ls_question = [re.sub(r"(?<!\\)%.*", "", line) for line in ls_question]
    # Extract the question
    txt = "".join(ls_question)
    # Replace the None in the dictionary by the formula below
    score_bad = round(-score_good / idx_choice, 2)
    for k, v in dict_question.items():
        if v is None:
            dict_question[k] = score_bad
    # Add a last option of no-answer
    # Keys were uppercase letters, use the next one
    if score_noanswer is not None:
        k = f"Score for answer {len(dict_question)}"
        dict_question[k] = score_noanswer
    return txt, dict_question


def read_tex(
    path_file: Union[str, List[str]],
    path_output: str,
    score_good: float = 1,
    score_bad: Optional[float] = None,
    score_noanswer: Optional[float] = None,
    batch_size: int = 50,
    aspectratio: int = 169,
    fontsize: int = 12,
    linespread: float = 1.1,
    dpi: int = 200,
    crop: bool = False,
    show_size: bool = False,
):
    """
    Read a LaTeX file and extract the questions and choices.

    Parameters
    ----------
    path_file : str
        Path to the LaTeX file.
    path_output : str
        Path to the output folder or zip file.
    score_good : float, optional
        Score for the correct answer.
    score_bad : float, optional
        Score for the wrong answers.
        If None, it will be set to -score_good / number_of_choices.
    score_noanswer : float, optional
        Score for not answering the question. This is added as a last option.
    aspectratio : int, optional
        Aspect ratio for the images, default is 169.
        As of the 2022, arbitrary aspect ratios are available.
        Two-digit numbers will be interpreted as X:Y,
        three-digit numbers as XX:Y and four digit as XX:YY.
    fontsize : int, optional
        Font size for the images, default is 12.
    dpi : int, optional
        Dots per inch for the images, default is 200.
    crop : bool, optional
        Whether to crop the images, default is False.
    """
    # Insert the line in the preamble (third line)
    txt_full = TXT_FULL.replace("$ASPECT$", str(aspectratio), 1)
    txt_full = txt_full.replace("$FONTSIZE$", str(fontsize), 1)
    txt_full = txt_full.replace("$LINESPREAD$", str(linespread), 1)

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
    ls_fout = []
    question_index = 0
    version_index = None
    section = None
    subsection = None

    for idx, line in enumerate(lines):
        line = line.strip()
        if line.startswith("%#original"):
            version_index = 0
        if line.startswith("%topic="):
            # Extract the topic as a subsection
            # Warning: This conflicts with the subsections in the LaTeX file
            subsection = line.split("=")[1]
            question_index = 0  # Reset
        if line.startswith("%"):
            continue
        elif line.startswith("\\begin{multiplechoice}"):
            # Example: \begin{multiplechoice}[title={Algebra}, resetcounter=no]
            section = re.search(r"title={(.+?)}", line).group(1)
            question_index = 0  # Reset
            subsection = None  # Reset
        elif line.startswith("\\subsection{"):
            subsection = re.search(r"subsection{(.+?)}", line).group(1)
            question_index = 0  # Reset
        elif line.startswith("\\begin{question}"):
            if version_index is None:
                question_index += 1
            elif version_index == 0:
                question_index += 1
                version_index += 1
            else:
                version_index += 1
            line = line.replace("\\begin{question}", "\\begin{frame}\n")
            question_lines = [line]  # Reset
        elif line.endswith("\\end{question}"):
            line = line.replace("\\end{question}", "\\end{frame}\n")
            question_lines.append(line)
            fout = out_folder + "/"
            if section is not None:
                # Remove spaces, underscores and commas
                section = re.sub(r"[ _,]", "", section)
                fout += f"{section}_"
            if subsection is not None:
                # Remove spaces, underscores and commas
                subsection = re.sub(r"[ _,]", "", subsection)
                fout += f"{subsection}_"
            fout += f"Q{question_index:03d}"
            if version_index is not None:
                fout += f"_V{version_index:02d}"
            try:
                txt, dict_question = process_question(
                    question_lines,
                    fout,
                    score_good=score_good,
                    score_bad=score_bad,
                    score_noanswer=score_noanswer,
                )
                ls_dict_questions.append(dict_question)
                txt_full += txt
                ls_fout.append(fout)
            except Exception as e:
                print(f"Error in question {fout}, line {idx}")
                # Save a traceback
                with open(out_folder + f"/error_{idx:04d}.txt", "w") as f:
                    f.write(str(e))
        elif question_index > 0:
            question_lines.append(line)

    txt_full += "\n\end{document}"

    with open("cover.tex", "w") as f:
        f.write(txt_full)

    cmd = ["pdflatex", "-interaction", "nonstopmode", "cover.tex"]
    proc = subprocess.Popen(cmd)
    proc.communicate()

    retcode = proc.returncode
    if not retcode == 0:
        os.unlink("cover.pdf")
        raise ValueError(
            "Error {} executing command: {}".format(retcode, " ".join(cmd))
        )

    # Turn the list of dictionaries into a DataFrame
    df = pd.DataFrame(ls_dict_questions)
    # Split into sub-dataframes by section
    df["Section"] = df["Item"].apply(lambda x: x.split("_")[0])
    for section in df["Section"].unique():
        df_section = df[df["Section"] == section]
        df_section = df_section.drop(columns=["Section"])
        df_section.to_csv(out_folder + f"/questions_{section}.csv", index=False)
    df = df.drop(columns=["Section"])
    df.to_csv(out_folder + "/questions.csv", index=False)

    # Store the size of the images
    dict_sizes = {}
    # Convert the PDF to PNG
    j = 0
    for i, fout in enumerate(ls_fout):
        if i % batch_size == 0:
            images = convert_from_path(
                "cover.pdf", first_page=i + 1, last_page=i + batch_size, dpi=dpi
            )
            j = i
        img = images[i - j]

        # Find where the question ends
        whites = (255 - np.asarray(img)).sum(axis=2)
        # Find the first row with non-white pixels
        y1 = np.argmax(whites.sum(axis=1) > 0)
        # Find the last row with non-white pixels
        y2 = np.argmax(whites[::-1].sum(axis=1) > 0)
        w, h = img.size
        dict_sizes[fout.split("/")[-1]] = h - y2 - y1

        if crop:
            # Crop the image
            y2 = h - y2 + y1
            img = img.crop((0, 0, w, y2))

        if show_size:
            # Put the size in red at the bottom of the image
            draw = ImageDraw.Draw(img)
            font = ImageFont.truetype("arial.ttf", 30)
            draw.text(
                (0, 0),
                f"{img.size[0]}x{img.size[1]}",
                (255, 0, 0),
                font=font,
            )

        img.save(fout + ".png", "PNG")
        yield (i + 1) / len(ls_fout)

    # Save dict_sizes as a CSV file
    df_sizes = pd.DataFrame(dict_sizes.items(), columns=["Item", "Size"])
    # Sort by size
    df_sizes = df_sizes.sort_values("Size", ascending=True)
    df_sizes.to_csv(out_folder + "/sizes.csv", index=False)

    # Remove auxiliary files
    for ext in ["aux", "log", "nav", "out", "snm", "tex", "toc"]:
        if os.path.exists("cover." + ext):
            os.unlink("cover." + ext)

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
    config: str = "config.json",
    key: str = "169",
):
    dict_config = json.load(open(config))

    gen = read_tex(
        file,
        output,
        score_good=dict_config["score_good"],
        score_bad=dict_config["score_bad"],
        score_noanswer=dict_config["score_noanswer"],
        show_size=dict_config["show_size"],
        **dict_config[key],
    )

    for p in gen:
        sys.stdout.write("\r%d%%" % (p * 100))
        sys.stdout.flush()


if __name__ == "__main__":
    typer.run(main)
