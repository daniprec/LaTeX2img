import html
from pathlib import Path

import streamlit as st

from tex2imgs.webwork_to_blackboard import (
    clean,
    convert_rows,
    read_csv_bytes,
    rows_to_csv_bytes,
)

st.set_page_config(page_title="WebWork to Blackboard Gradebook", page_icon="logo.png")


RESULT_KEY = "webwork_blackboard_conversion"
SIGNATURE_KEY = "webwork_blackboard_signature"
EXAMPLES_DIR = Path(__file__).resolve().parents[1] / "examples"
SAMPLE_FILES = [
    (
        "Blackboard sample",
        "blackboard_gradebook_sample.csv",
        "blackboard_gradebook_sample.csv",
    ),
    ("WebWork sample", "webwork_totals_sample.csv", "webwork_totals_sample.csv"),
    (
        "Expected output",
        "blackboard_with_webwork_sample.csv",
        "blackboard_with_webwork_sample.csv",
    ),
]


def uploaded_signature(blackboard_file, webwork_file, blackboard_bytes, webwork_bytes):
    return (
        blackboard_file.name if blackboard_file else None,
        len(blackboard_bytes or b""),
        webwork_file.name if webwork_file else None,
        len(webwork_bytes or b""),
    )


def preview_table(rows, limit=10):
    if not rows:
        return ""
    header = rows[0]
    preview_rows = []
    for row in rows[1 : limit + 1]:
        padded = list(row)
        while len(padded) < len(header):
            padded.append("")
        preview_rows.append(padded[: len(header)])

    if not preview_rows:
        return ""

    header_cells = "".join(
        f"<th>{html.escape(str(cell or ''))}</th>" for cell in header
    )
    body_rows = []
    for row in preview_rows:
        cells = "".join(f"<td>{html.escape(str(cell or ''))}</td>" for cell in row)
        body_rows.append(f"<tr>{cells}</tr>")

    return f"""
<div class="csv-preview-table" style="overflow-x:auto; margin-top: 0.75rem;">
  <table style="border-collapse: collapse; width: 100%; font-size: 0.9rem;">
    <thead>
      <tr>{header_cells}</tr>
    </thead>
    <tbody>
      {"".join(body_rows)}
    </tbody>
  </table>
</div>
<style>
  .csv-preview-table table th {{
    background: #f6f8fa;
    font-weight: 600;
  }}
  .csv-preview-table table th, .csv-preview-table table td {{
    border: 1px solid #d0d7de;
    padding: 0.45rem 0.6rem;
    text-align: left;
    white-space: nowrap;
  }}
</style>
"""


def format_code_list(codes):
    if not codes:
        return "None"
    return ", ".join(f"`{code}`" for code in codes)


st.title("WebWork to Blackboard Gradebook")
st.write(
    "Append WebWork project scores to a Blackboard gradebook without changing "
    "the original Blackboard columns."
)

with st.expander("How the conversion works", expanded=True):
    st.markdown(
        """
1. Download the gradebook CSV from Blackboard. This is the base file: every
   original Blackboard column is kept in the same order.
2. Download the totals CSV from WebWork. The tool looks for the WebWork header
   row and reads the project columns, such as `Problem_Set_1`.
3. Upload both files below. In most cases the key columns are detected
   automatically as the Blackboard email or username column and the WebWork
   login/email column.
4. If your exports use different names, choose the Blackboard key column and
   type the WebWork key column manually.
5. Convert and download the new CSV. The output adds one column per WebWork
   project and leaves unmatched Blackboard students blank.
"""
    )

with st.expander("How to download and upload Blackboard gradebooks"):
    st.markdown(
        """
To download the gradebook from Blackboard, go to your course, open
**Gradebook**, and find the top-right row of icons. The rightmost icon is a
configuration wheel. Next to it, click **Download Gradebook**, which looks like
a box with an arrow pointing down. Select **Full Gradebook**, **All Items**,
and **CSV** as the file type. Then click **Download**.

To upload the updated Blackboard file, follow a similar path but click
**Upload Gradebook**, the box with an arrow pointing up.
"""
    )

st.subheader("Sample files")
st.write(
    "Use these files to test the workflow before using a real gradebook. The "
    "expected output shows the Blackboard sample after the WebWork scores are "
    "appended."
)
sample_cols = st.columns(len(SAMPLE_FILES))
for col, (label, filename, download_name) in zip(sample_cols, SAMPLE_FILES):
    sample_path = EXAMPLES_DIR / filename
    with col:
        if sample_path.exists():
            st.download_button(
                label,
                data=sample_path.read_bytes(),
                file_name=download_name,
                mime="text/csv",
            )
        else:
            st.button(label, disabled=True)

col1, col2 = st.columns(2)
with col1:
    blackboard_file = st.file_uploader(
        "Blackboard CSV",
        type=["csv"],
        key="webwork_blackboard_blackboard_csv",
    )
with col2:
    webwork_file = st.file_uploader(
        "WebWork CSV",
        type=["csv"],
        key="webwork_blackboard_webwork_csv",
    )

blackboard_bytes = blackboard_file.getvalue() if blackboard_file else None
webwork_bytes = webwork_file.getvalue() if webwork_file else None
signature = uploaded_signature(
    blackboard_file, webwork_file, blackboard_bytes, webwork_bytes
)
if st.session_state.get(SIGNATURE_KEY) != signature:
    st.session_state[SIGNATURE_KEY] = signature
    st.session_state.pop(RESULT_KEY, None)

blackboard_rows = None
blackboard_key = None
can_convert = bool(blackboard_bytes and webwork_bytes)

if blackboard_bytes:
    try:
        blackboard_rows = read_csv_bytes(blackboard_bytes)
        if not blackboard_rows:
            can_convert = False
            st.error("The Blackboard CSV is empty.")
        else:
            header = [clean(cell) for cell in blackboard_rows[0]]
            key_options = ["Auto-detect"] + header
            key_choice = st.selectbox("Blackboard key column", key_options)
            if key_choice != "Auto-detect":
                blackboard_key = key_choice
    except ValueError as exc:
        can_convert = False
        st.error(f"Could not read the Blackboard CSV: {exc}")
else:
    st.selectbox(
        "Blackboard key column",
        ["Upload a Blackboard CSV first"],
        disabled=True,
    )

webwork_key = st.text_input(
    "WebWork key column",
    value="",
    placeholder="Auto-detect login ID",
    help="Leave blank unless your WebWork export uses a custom key column name.",
)

if st.button("Convert CSV", type="primary", disabled=not can_convert):
    try:
        if blackboard_rows is None:
            blackboard_rows = read_csv_bytes(blackboard_bytes or b"")
        webwork_rows = read_csv_bytes(webwork_bytes or b"")
        result = convert_rows(
            blackboard_rows=blackboard_rows,
            webwork_rows=webwork_rows,
            blackboard_key=blackboard_key,
            webwork_key=clean(webwork_key) or None,
        )
        st.session_state[RESULT_KEY] = {
            "data": rows_to_csv_bytes(result.rows),
            "matched": result.matched,
            "unmatched": result.unmatched,
            "appended_columns": result.appended_columns,
            "overwritten_headers": getattr(result, "overwritten_headers", []),
            "unmatched_blackboard_keys": getattr(
                result, "unmatched_blackboard_keys", []
            ),
            "unmatched_webwork_keys": getattr(result, "unmatched_webwork_keys", []),
            "blackboard_key": result.blackboard_key,
            "webwork_key": result.webwork_key,
            "rows": result.rows,
        }
    except ValueError as exc:
        st.session_state.pop(RESULT_KEY, None)
        st.error(str(exc))

conversion = st.session_state.get(RESULT_KEY)
if conversion:
    st.success(
        "Added "
        f"{conversion['appended_columns']} new WebWork columns. "
        f"Matched {conversion['matched']} Blackboard rows; "
        f"{conversion['unmatched']} unmatched."
    )
    st.caption(
        f"Matched with Blackboard `{conversion['blackboard_key']}` "
        f"and WebWork `{conversion['webwork_key']}`."
    )

    overwritten_headers = conversion.get("overwritten_headers", [])
    if overwritten_headers:
        st.error(
            "The following Blackboard columns were overwritten with WebWork "
            "values, taking the last matching value from WebWork: "
            f"{format_code_list(overwritten_headers)}."
        )

    unmatched_blackboard = conversion.get("unmatched_blackboard_keys", [])
    if unmatched_blackboard:
        st.error(
            "These Blackboard codes did not match any WebWork row: "
            f"{format_code_list(unmatched_blackboard)}."
        )

    unmatched_webwork = conversion.get("unmatched_webwork_keys", [])
    if unmatched_webwork:
        st.error(
            "These WebWork codes did not match any Blackboard row: "
            f"{format_code_list(unmatched_webwork)}."
        )

    st.download_button(
        "Download Blackboard CSV",
        data=conversion["data"],
        file_name="blackboard_with_webwork.csv",
        mime="text/csv",
    )

    table = preview_table(conversion["rows"])
    if table:
        st.markdown(table, unsafe_allow_html=True)
