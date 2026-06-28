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
st.set_page_config(page_title="QuickBib: DOI to BibTeX", page_icon=icon_url)

# Trim top padding for a tighter layout
st.markdown(
    """
    <style>
    .block-container {
        padding-top: 2rem;
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

st.markdown(
    f"""
    <style>
    .quickbib-header {{
        display: flex;
        align-items: center;
        gap: 1rem;
        margin: 0 0 0.75rem 0;
    }}
    .quickbib-header img {{
        width: 64px;
        height: 64px;
        object-fit: contain;
        flex: 0 0 auto;
    }}
    .quickbib-header h1 {{
        margin: 0;
        line-height: 1.05;
    }}
    </style>
    <div class='quickbib-header'>
        <img src='{icon_url}' alt='QuickBib icon' />
        <h1>QuickBib: DOI/arXiv to BibTeX</h1>
    </div>
    """,
    unsafe_allow_html=True,
)

doi_input = st.text_input(
    "DOI",
    placeholder="Paste a DOI, arXiv ID, or paper link here, e.g. https://journals.aps.org/prl/abstract/10.1103/v6r7-4ph9",
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

            left_col, right_col = st.columns([0.65, 0.35], gap="large")

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
st.markdown("View [examples](https://archisman-panigrahi.github.io/QuickBib/#examples).")
st.markdown("**No AI/ML-generated citations**: metadata comes from Crossref and arXiv APIs. Here is [how it works](https://github.com/archisman-panigrahi/doi2bib3/blob/main/docs/ALGORITHM_VISUALS.md#2-identifier-resolution-decision-tree).")
st.markdown(
    """
    **Bugs or feature requests**: <a href="https://github.com/archisman-panigrahi/QuickBib/issues">GitHub</a> &bull;
    Helpful? Star on GitHub &nbsp;
    <a href="https://github.com/archisman-panigrahi/QuickBib" target="_blank">
    <img src="https://img.shields.io/github/stars/archisman-panigrahi/QuickBib?style=social" alt="Star on GitHub">
    </a> &nbsp; &bull; Try the [QuickBib desktop app](https://archisman-panigrahi.github.io/QuickBib/).
    """,
    unsafe_allow_html=True,
)
