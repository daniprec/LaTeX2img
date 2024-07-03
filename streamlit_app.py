import os

import streamlit as st

from tex2imgs import read_tex

if "uploader_key" not in st.session_state:
    st.session_state.uploader_key = 0

# Streamlit container where user can drop a .tex file
st.title("LaTeX to Images")
st.write("Drop a .tex file to convert it to images.")
file = st.file_uploader(
    "Upload a .tex file", type=["tex"], key=f"uploader_{st.session_state.uploader_key}"
)


def download_on_click():
    # Make a new session state to avoid rerunning the script
    st.session_state.uploader_key += 1
    # Remove the output.zip file
    os.remove("output.zip")


if file is not None:
    # Get a list of strings
    file = file.getvalue().decode("utf-8").split("\n")

    # Initialize loading bar
    bar = st.progress(0)

    # Convert the .tex file to images
    generator = read_tex(
        path_file=file,
        path_output="output.zip",
        separate_choices=False,
        score_good=1.0,
        score_bad=None,
    )

    # Iterate over the generator to update the loading bar
    for progress in generator:
        bar.progress(progress)

    # Create a download link
    with open("output.zip", "rb") as fp:
        btn = st.download_button(
            label="Download ZIP",
            data=fp,
            file_name="output.zip",
            mime="application/zip",
            on_click=download_on_click,
        )
