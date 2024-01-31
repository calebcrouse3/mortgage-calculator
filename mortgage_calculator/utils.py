import streamlit as st


def format_currency(value):
    return "${:,.0f}".format(value)


def fig_display(fig):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=True)


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def display_metrics_in_row(metrics, num_cols):
    metric_key = list(metrics.keys())
    for idx, col in enumerate(st.columns(num_cols)):
        with col:
            with st.container(height=110):
                key = metric_key[idx]
                value = metrics[key]
                st.metric(label=key, value=value, delta="")


def format_label_string(label):
    """Format label string for display on plotly chart."""
    output = label.lower().replace("_", " ")
    stop_words = ["sum", "mean", "cum"]
    for word in stop_words:
        output = output.replace(f" {word}", "")
    output = output.title()
    acronyms = ["Pmi", "Hoa"]
    for acronym in acronyms:
        output = output.replace(acronym, acronym.upper())
    return output

