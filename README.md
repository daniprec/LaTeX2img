# BAM Professor Tools

This repository contains a Streamlit site with small teaching-operation tools
for BAM professors. The site focuses on repetitive assessment workflows:
preparing mathematical questions, generating image assets, and moving grades
between learning platforms while keeping the original source files easy to
inspect.

Cloud version:
[https://ie-bam-latex2img.streamlit.app/](https://ie-bam-latex2img.streamlit.app/)

## Available Tools

### LaTeX to Images

Upload a `.tex` file containing multiple-choice questions and download a ZIP
file with the rendered images. This is useful when a quiz, exam, or learning
platform needs mathematical content as image files rather than raw LaTeX.

Basic process:

1. Prepare a `.tex` file with questions and `\choice{...}` answers.
2. Upload the file in the LaTeX to Images page.
3. Wait for the progress bar to complete.
4. Download the generated ZIP file.

### Single Question Preview

Paste one LaTeX multiple-choice question and preview the rendered image. Use
this before preparing a full file, especially when checking spacing, notation,
aspect ratio, or DPI.

### WebWork to Blackboard

Merge WebWork project scores into a Blackboard gradebook CSV. Blackboard stays
as the base table: all original Blackboard columns are preserved, and the tool
adds one new column per WebWork project.

Basic process:

1. Export the gradebook CSV from Blackboard.
2. Export the totals CSV from WebWork.
3. Open the WebWork to Blackboard page.
4. Optionally download the sample CSVs from the page to test the workflow.
5. Upload the Blackboard CSV and the WebWork CSV.
6. Leave key columns on automatic detection unless your exports use unusual
   column names.
7. Convert and download `blackboard_with_webwork.csv`.

To download the gradebook from Blackboard, go to your course, open
**Gradebook**, and find the top-right row of icons. The rightmost icon is a
configuration wheel. Next to it, click **Download Gradebook**, which looks like
a box with an arrow pointing down. Select **Full Gradebook**, **All Items**,
and **CSV** as the file type. Then click **Download**.

To upload the updated Blackboard file, follow a similar path but click
**Upload Gradebook**, the box with an arrow pointing up.

Matching rules:

- The app uses one matching key column from each file.
- Blackboard is usually matched by `Email`, `Username`, `User ID`, `login ID`,
  or `login`.
- WebWork is usually matched by `login ID`, `Email`, `Username`, `User ID`, or
  `login`.
- Matching first tries the full value, then the part before `@`, then common
  variants before a dot or underscore. For example, `john.smith@uni.edu` can
  match `john.smith`.
- Unmatched Blackboard rows are kept, with blank WebWork score cells.

Warnings:

- If a WebWork project column has the same name as an existing Blackboard
  column, except for the matching key column, the Blackboard column is
  overwritten with the WebWork value. If WebWork provides repeated values for
  that column, the last matching WebWork value is used.
- If students do not match, the app shows the unmatched Blackboard codes and
  the unmatched WebWork codes in red before download.

Reference files are available in [`examples/`](examples/):

- [`blackboard_gradebook_sample.csv`](examples/blackboard_gradebook_sample.csv)
- [`webwork_totals_sample.csv`](examples/webwork_totals_sample.csv)
- [`blackboard_with_webwork_sample.csv`](examples/blackboard_with_webwork_sample.csv)

## Running Locally

Install the Python dependencies:

```bash
pip install -r requirements.txt
```

Start the Streamlit site:

```bash
streamlit run streamlit_app.py
```

Then open:

```text
http://localhost:8501
```

## Project Structure

```text
streamlit_app.py                     Front page for the BAM tools site
pages/1_latex_to_images.py           Batch LaTeX image converter
pages/1_single_img.py                Single-question preview tool
pages/2_webwork_blackboard_converter.py
                                     WebWork to Blackboard CSV converter
tex2imgs/                            Shared conversion logic
examples/                            Sample CSV and LaTeX files
```
