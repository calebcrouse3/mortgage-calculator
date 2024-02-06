import streamlit as st
import plotly.graph_objs as go


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def dict_to_metrics(data_dict):
    st.container(height=20, border=False)
    for key, value in data_dict.items():
        st.metric(label=f":orange[{key}]", value=value)


def get_tab_columns():
    col1, _, col2 =  st.columns([1, .5, 5])
    return col2, col1


###########################################################
#               Input field functions                     #
###########################################################


def rate_input(label, key=None, min_value=0.0, max_value=99.0, step=0.1, asterisk=False, help=None):
    if asterisk:
        label = ":orange[**]" + label
    
    percent = st.number_input(
        label=f"{label} (%)",
        min_value=min_value,
        max_value=max_value,
        step=step,
        key=key,
        help=help,
        on_change=None
    )
    return percent


def dollar_input(label, key=None, min_value=0, max_value=1e8, step=10, asterisk=False, help=None):
    if asterisk:
        label = ":orange[**]" + label

    return st.number_input(
        f"{label} ($)",
        min_value=int(min_value), 
        max_value=int(max_value),
        step=int(step),
        key=key,
        help=help,
        on_change=None
    )


def populate_columns(values, cols=3):
    output_vals = []
    columns = st.columns(cols)
    assert len(columns) >= len(values)
    for col, value_func in zip(columns[:len(values)], values):
        with col:
            val = value_func()
            output_vals.append(val)
    return output_vals


###########################################################
#               String formatting functions               #
###########################################################

def format_currency(value):
    return "${:,.0f}".format(value)


def format_percent(value):
    return "{:.1%}".format(value)


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


###########################################################
#               Plotly figure functions                   #
###########################################################


def fig_display(fig, use_container_width=False):
    st.plotly_chart(fig, config={'displayModeBar': False}, use_container_width=use_container_width)


def plot_data(yearly_df, cols, names, colors, title, height, width, xlim, mode, percent=False):
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
    fig_display(fig)