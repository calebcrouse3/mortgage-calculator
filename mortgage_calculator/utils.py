import streamlit as st
import plotly.graph_objs as go


def format_currency(value):
    return "${:,.0f}".format(value)

def format_percent(value):
    return "{:.1%}".format(value)


def fig_display(fig, use_container_width=False):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=use_container_width)


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


def plot_dots(yearly_df, cols, names, colors, title, height, width, xlim, mode, percent=False):
    hovertemplate = '$%{y:,.0f}'
    if percent:
        hovertemplate = '%{y:.1%}'  # Formats y as a percentage

    yaxis = dict(title='Dollars ($)', tickformat='$,.0f')
    if percent:
        yaxis = dict(title='Percent (%)', tickformat='.0%')

    # Slice the DataFrame to only include data up to the xlim
    filtered_df = yearly_df[yearly_df.index < xlim]

    # Calculate the min and max values across the specified columns within the xlim range
    min_val = filtered_df[cols].min().min()
    max_val = filtered_df[cols].max().max()

    # Adjusting the min and max values slightly for better y-axis visualization
    if not percent:
        min_val = min_val - (max_val - min_val) * 0.2  # Ensure min is not below 0 for dollar values
        max_val = max_val + (max_val - min_val) * 0.2
    else:
        min_val = min_val - (max_val - min_val) * 0.2  # Ensure min is not below 0% for percentages
        max_val = max_val + (max_val - min_val) * 0.2  # Ensure max is not above 100% for percentages


    fig = go.Figure()

    for i in range(len(cols)):
        trace = go.Scatter(
            x=yearly_df.index + 1, 
            y=yearly_df[cols[i]],
            name=names[i],
            hoverinfo='y',
            hovertemplate=hovertemplate,
        )

        if mode == "Lines":
            trace.update(mode="lines", line=dict(width=4, color=colors[i]))
        else:
            trace.update(mode="markers", marker=dict(size=10, color=colors[i]))

        fig.add_trace(trace)


    fig.update_layout(
        title=title,
        xaxis=dict(title='Year'),
        yaxis=dict(**yaxis, range=[min_val, max_val]),
        height=height,
        width=width,
        hovermode='x',
    )

    fig.update_xaxes(range=[0, xlim+1])

    # Assuming fig_display is a function you have defined to display the Plotly figure
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


def dict_to_metrics_old(data_dict, title):
    keys = list(data_dict.keys())
    values = list(data_dict.values())

    cells = dict(
        values=[keys, values],
        #line_color='rgba(0,0,0,0)',
        fill_color='rgba(255,255,255,0)'
    )

    header = dict(
        line_color="rgba(0,0,0,0)",
        fill_color='rgba(255,255,255,0)',
        height=0
    )

    fig = go.Figure(data=[go.Table(
        header=header,
        cells=cells,
    )])

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        width=300,
    )

    st.container(height=20, border=False)
    st.write(title)
    st.plotly_chart(fig)
    #fig_display(fig)