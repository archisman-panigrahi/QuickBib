import streamlit as st
from doi2bib3 import fetch_bibtex, format_bibtex_to_aps_bibitem
from st_copy_to_clipboard import st_copy_to_clipboard

# --- Your Custom Function ---
def get_bibtex_for_doi(doi: str):
    try:
        bibtex = fetch_bibtex(doi)
        return True, bibtex, None
    except Exception as e:
        return False, "", str(e)

# --- Streamlit UI Layout ---
icon_url = "https://github.com/archisman-panigrahi/QuickBib/blob/main/assets/icon/128x128/io.github.archisman_panigrahi.QuickBib.png?raw=true"
ICON_SIZE = 96
st.set_page_config(page_title="QuickBib: DOI to BibTeX", page_icon=icon_url)

# Trim top padding for a tighter layout
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
        width: 80vw;
        max-width: 80vw;
        padding-left: 2rem;
        padding-right: 2rem;
        margin-left: auto;
        margin-right: auto;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

title_icon_col, title_text_col = st.columns([0.12, 0.82])
with title_icon_col:
    st.markdown(
        f"<div style='padding-top:30px; text-align:left;'>"
        f"<img src='{icon_url}' width='{ICON_SIZE}'/></div>",
        unsafe_allow_html=True,
    )
with title_text_col:
    st.title("QuickBib: DOI/arXiv to BibTeX")


# Input Field with enlarged label
st.markdown(
    "<div style='font-size:1.2rem; font-weight:400;'>"
    "Paste a DOI, arXiv ID, or paper link (APS, AMS, ACS, Science, Nature, ScienceDirect, PNAS, IOP Science, and SciPost group of journals. For others, use the DOI). See <a href='https://archisman-panigrahi.github.io/QuickBib/#examples'>examples</a>"
    "</div>",
    unsafe_allow_html=True,
)
doi_input = st.text_input(
    "DOI",
    placeholder="e.g. https://journals.aps.org/prl/abstract/10.1103/v6r7-4ph9",
    label_visibility="collapsed",  # or "hidden"
)
# Logic Trigger
if doi_input:
    with st.spinner("Fetching data..."):
        success, bibtex, error_msg = get_bibtex_for_doi(doi_input)

        if success:
            try:
                aps_bibitem = format_bibtex_to_aps_bibitem(bibtex)
                aps_success = True
            except Exception as e:
                aps_success = False
                aps_error_msg = str(e)

            left_col, right_col = st.columns(2, gap="large")

            with left_col:
                st.subheader("BibTeX")
                st.code(bibtex, language='latex', wrap_lines=True)
                st_copy_to_clipboard(bibtex, "Copy BibTeX")

            with right_col:
                st.subheader("APS style bibitem")
                if aps_success:
                    st.code(aps_bibitem, language='latex', wrap_lines=True)
                    st_copy_to_clipboard(aps_bibitem, "Copy bibitem")
                else:
                    st.error("Could not format the APS bibitem.")
                    with st.expander("See APS formatting error details"):
                        st.write(aps_error_msg)

        else:
            st.error("Could not resolve this input.")
            with st.expander("See error details"):
                st.write(error_msg)
st.markdown("No ML-generated citations: metadata comes from Crossref and arXiv APIs. Powered by [doi2bib3](https://github.com/archisman-panigrahi/doi2bib3). Here is [how it works](https://github.com/archisman-panigrahi/doi2bib3/blob/main/docs/ALGORITHM_VISUALS.md#2-identifier-resolution-decision-tree).")
st.markdown(
    """
    Bugs or feature requests: <a href="https://github.com/archisman-panigrahi/QuickBib/issues">GitHub</a>.
    Helpful? Star on GitHub &nbsp;
    <a href="https://github.com/archisman-panigrahi/QuickBib" target="_blank">
    <img src="https://img.shields.io/github/stars/archisman-panigrahi/QuickBib?style=social" alt="Star on GitHub">
    </a>
    """,
    unsafe_allow_html=True,
)
st.markdown(
    "For faster DOI-to-BibTeX workflow, try the "
    "[native desktop app](https://archisman-panigrahi.github.io/QuickBib/)."
)
