import os
import shutil

import streamlit as st

from tex2imgs import read_tex

st.title("Single Question")
# Text block where the user can input the LaTeX expression
latex_expression = st.text_area(
    "Please input a question with choices in LaTeX format:",
    r"""Calculate $\frac{10}{20}$:
\choice{$\log{10}$}
\choice{$1+i$}
\choice{2}
\choice[!]{0.5}""",
)

# Button
if st.button("Generate Image"):
    path_file = "temp.tex"
    path_folder = "temp"
    # Include the \begin{question} and \end{question} tags
    latex_expression = r"\begin{question}" + latex_expression + r"\end{question}"

    # Generate a tex file containing the LaTeX expression
    with open(path_file, "w") as f:
        f.write(latex_expression)
    # Generate the image
    gen = read_tex(path_file, path_folder)
    for _ in gen:
        pass

    # Find the png image inside the folder
    for file in os.listdir(path_folder):
        if file.endswith(".png"):
            path_img = os.path.join(path_folder, file)
            break

    # Display the image
    st.image(path_img)

    os.remove(path_file)
    shutil.rmtree(path_folder)
