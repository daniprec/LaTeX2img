import os
from typing import List

import matplotlib.pyplot as plt


def tex_to_img(tex: str, fout: str):
    plt.figure(figsize=(8, 0.3))
    plt.text(-0.1, 0.0, tex, ha="left", va="bottom", fontsize=12)
    plt.axis("off")
    plt.savefig(fout)
    plt.close()


def process_question(lines: List[str], fout: str):
    idx_choice = 0
    for line in lines:
        if line.strip().startswith("\\choice"):
            idx_choice += 1
            if "\\choice[!]" in line:
                extra = "_correct"
            else:
                extra = ""
            # Extract the text inside "{}"
            txt = line[line.find("{") + 1 : line.rfind("}")]
            try:
                tex_to_img(txt, fout + f"_A{idx_choice}{extra}.png")
            except Exception as e:
                print(repr(e))


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
