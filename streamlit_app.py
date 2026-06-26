import streamlit as st


st.set_page_config(
    page_title="BAM Professor Tools",
    page_icon="logo.png",
    layout="wide",
)


st.markdown(
    """
<style>
  .block-container {
    max-width: 1040px;
    padding-top: 2.5rem;
    padding-bottom: 3rem;
  }
  .bam-eyebrow {
    color: #52616f;
    font-size: 0.88rem;
    font-weight: 650;
    letter-spacing: 0;
    margin-bottom: 0.4rem;
    text-transform: uppercase;
  }
  .bam-title {
    color: #17202a;
    font-size: 2.45rem;
    font-weight: 720;
    line-height: 1.12;
    margin: 0 0 0.9rem;
  }
  .bam-lede {
    color: #36454f;
    font-size: 1.08rem;
    line-height: 1.65;
    max-width: 760px;
  }
  .tool-panel {
    border: 1px solid #d9dee7;
    border-radius: 8px;
    padding: 1rem 1rem 0.85rem;
    min-height: 160px;
    background: #ffffff;
  }
  .tool-panel h3 {
    color: #17202a;
    font-size: 1.05rem;
    margin: 0 0 0.45rem;
  }
  .tool-panel p {
    color: #4b5563;
    font-size: 0.95rem;
    line-height: 1.55;
    margin: 0;
  }
  .section-rule {
    border-top: 1px solid #e5e7eb;
    margin: 1.8rem 0 1.25rem;
  }
</style>
""",
    unsafe_allow_html=True,
)


st.markdown('<div class="bam-eyebrow">BAM teaching support</div>', unsafe_allow_html=True)
st.markdown(
    '<h1 class="bam-title">Professor Tools for Course Operations</h1>',
    unsafe_allow_html=True,
)
st.markdown(
    """
<p class="bam-lede">
This Streamlit site collects small, practical utilities for BAM professors.
The goal is to reduce repetitive formatting work around assessments, learning
platform uploads, and mathematical question preparation, while keeping the
process transparent enough to verify before using the final files with students.
</p>
""",
    unsafe_allow_html=True,
)

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

st.subheader("Available tools")
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(
        """
<div class="tool-panel">
  <h3>LaTeX to Images</h3>
  <p>Upload a complete LaTeX question file and download rendered image assets
  packaged in a ZIP file.</p>
</div>
""",
        unsafe_allow_html=True,
    )

with col2:
    st.markdown(
        """
<div class="tool-panel">
  <h3>Single Question Preview</h3>
  <p>Render one multiple-choice LaTeX question while adjusting output ratio and
  resolution.</p>
</div>
""",
        unsafe_allow_html=True,
    )

with col3:
    st.markdown(
        """
<div class="tool-panel">
  <h3>WebWork to Blackboard</h3>
  <p>Merge WebWork project scores into a Blackboard gradebook CSV and download
  the updated file.</p>
</div>
""",
        unsafe_allow_html=True,
    )

st.markdown('<div class="section-rule"></div>', unsafe_allow_html=True)

st.subheader("Working principle")
st.write(
    "Each tool keeps the source file as the reference point, produces a new "
    "downloadable output, and leaves the original material unchanged. Use the "
    "sidebar to open a tool, review the short workflow notes, upload your file, "
    "and inspect the result before importing it into a course platform."
)
