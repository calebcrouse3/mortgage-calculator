import streamlit as st
import plotly.graph_objs as go


def format_currency(value):
    return "${:,.0f}".format(value)

def format_percent(value):
    return "{:.1%}".format(value)


def fig_display(fig):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=False)


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


def plot_dots(yearly_df, cols, names, colors, title, percent=False):

    hovertemplate = '$%{y:,.0f}'
    if percent:
        # Use this hovertemplate for percentages without multiplying y by 100
        hovertemplate = '%{y:.1%}'  # Formats y as a percentage

    yaxis = dict(title='Dollars ($)', tickformat='$,.0f')
    if percent:
        # This tickformat correctly formats y-values as percentages without needing to multiply them by 100
        yaxis = dict(title='Percent (%)', tickformat='.0%')

    fig = go.Figure()

    for i in range(len(cols)):
        fig.add_trace(go.Scatter(
            x=yearly_df.index + 1, 
            y=yearly_df[cols[i]],  # Do not multiply by 100, Plotly handles percentage formatting
            mode='markers', 
            name=names[i],
            hoverinfo='y',
            hovertemplate=hovertemplate,
            marker=dict(size=10, color=colors[i]),
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(title='Year'),
        yaxis=yaxis,
        height=700,
        hovermode='x'
    )

    fig_display(fig)





def format_label_string(label):
    """Format label string for display on plotly chart."""
    output = label.lower().replace("_", " ")
    stop_words = ["sum", "mean", "cum", "mo", "exp"]
    for word in stop_words:
        output = output.replace(f" {word}", "")
    output = output.title()
    acronyms = ["Pmi", "Hoa"]
    for acronym in acronyms:
        output = output.replace(acronym, acronym.upper())
    return output

