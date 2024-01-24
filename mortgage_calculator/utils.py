import streamlit as st

# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas


def get_xaxis(current_year, num_years=30):
    tick_positions = list(range(0, num_years, 5))
    tick_labels = [i + current_year for i in tick_positions]
    return dict(title='Year',
        tickmode='array',
        tickvals=tick_positions,
        ticktext=tick_labels
    )


def get_yaxis():
    return dict(
        title='Dollars',
        tickformat='$,.0f'
    )


# chart helpers
def fig_update(fig):
    for trace in fig.data:
        trace.hovertemplate = f"{trace.name}: " + "%{y:$,.0f}<extra></extra>"


def fig_display(fig):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=False)

