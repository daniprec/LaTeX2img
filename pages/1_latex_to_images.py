import os

import streamlit as st

from tex2imgs.utils import read_tex


st.set_page_config(page_title="LaTeX to Images", page_icon="logo.png")


if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0


st.title("LaTeX to Images")
st.write(
    "Convert a LaTeX file with multiple-choice questions into a ZIP file of "
    "images ready for use in teaching material, quizzes, or exams."
)

with st.expander("How the conversion works", expanded=True):
    st.markdown(
        """
1. Export or prepare a `.tex` file containing questions in the expected format.
2. Upload the file below.
3. The tool reads each question and choice, renders the mathematical content,
   and packages the generated images in a ZIP file.
4. Download the ZIP file and use the images wherever the learning platform
   requires image-based question content.
"""
    )

file = st.file_uploader(
    "Upload a .tex file", type=["tex"], key=f"uploader_{st.session_state.uploader_key}"
)


def download_on_click():
    st.session_state.uploader_key += 1
    os.remove("output.zip")


if file is not None:
    file = file.getvalue().decode("utf-8").split("\n")

    bar = st.progress(0)
    generator = read_tex(
        path_file=file,
        path_output="output.zip",
        score_good=1.0,
        score_bad=None,
    )

    for progress in generator:
        bar.progress(progress)

    with open("output.zip", "rb") as fp:
        st.download_button(
            label="Download ZIP",
            data=fp,
            file_name="output.zip",
            mime="application/zip",
            on_click=download_on_click,
        )
