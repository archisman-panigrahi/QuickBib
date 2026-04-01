import streamlit as st
from doi2bib3 import fetch_bibtex
# Import the button component
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
ICON_SIZE = 128
st.set_page_config(page_title="DOI to BibTeX", page_icon=icon_url)

# Trim top padding for a tighter layout
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 1rem;
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
    "Enter DOI or arXiv number or a link to the paper to generate the BibTeX entry. See <a href='https://archisman-panigrahi.github.io/QuickBib/#examples'>(examples)</a>"
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
            # Display the BibTeX in a code block for easy reading
            st.code(bibtex, language='latex')

            # Center the copy button in the middle column
            _, center_col, _ = st.columns([1, 1, 1])
            with center_col:
                st_copy_to_clipboard(bibtex, "Copy to Clipboard 📋")

        else:
            st.error(f"Failed to resolve DOI.")
            with st.expander("See error details"):
                st.write(error_msg)

st.markdown(
    """
    Please report bugs and suggest feature requests on <a href="https://github.com/archisman-panigrahi/QuickBib/issues">GitHub</a>.
    """,
    unsafe_allow_html=True,
)
st.markdown(
    """
    If you find this helpful, please add a star on GitHub &nbsp;
    <a href="https://github.com/archisman-panigrahi/QuickBib" target="_blank">
    <img src="https://img.shields.io/github/stars/archisman-panigrahi/QuickBib?style=social" alt="Star on GitHub">
    </a>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    "For an even faster DOI-to-BibTeX workflow, switch to the "
    "[native desktop app](https://archisman-panigrahi.github.io/QuickBib/)."
)
