import os

import streamlit as st

from tex2imgs import process_question

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
    # Replace more than one " " with a single " "
    lines = " ".join(latex_expression.split())
    # Split the lines by "\n" right before the "\choice"
    # Keeping the "\choice" in the lines
    lines = lines.split(r"\choice")
    lines = [lines[0]] + [r"\choice" + line for line in lines[1:]]
    # Generate the image
    process_question(lines, "temp")

    # Display the image
    st.image("temp.png")

    # Remove the image
    os.remove("temp.png")
