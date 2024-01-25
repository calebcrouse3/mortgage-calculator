import streamlit as st


def format_currency(value):
    return "${:,.0f}".format(value)


def fig_display(fig):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=True)

