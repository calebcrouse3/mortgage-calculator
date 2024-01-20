import streamlit as st

# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas


# chart helpers
def fig_update(fig, title, months):
    year_labels = [f'{year}' for year in range(1, (len(months) // 12) + 1)]
    year_ticks = dict(
        tickmode='array',
        tickvals=[1 + 12 * i for i in range(len(year_labels))],
        ticktext=year_labels
    )
    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title="Dollars",
        xaxis=year_ticks,
        height=700
    )
    for trace in fig.data:
        trace.hovertemplate = f"{trace.name}: " + "%{y:$,.0f}<extra></extra>"


def fig_display(fig):
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})

