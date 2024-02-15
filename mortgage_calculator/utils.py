import streamlit as st
import plotly.graph_objs as go
import pandas as pd
import numpy as np


HEIGHT = 700
WIDTH = 800

BLUE = "#1f77b4"
ORANGE = "#ff7f0e"
GREEN = "#2ca02c"

PLOT_COLORS = [BLUE, ORANGE, GREEN]

COLOR_MAP = {
    "interest_exp_mo":      "#0068C9",  # Blue
    "principal_exp_mo":     "#83C9FF",  # Light Blue
    "property_tax_exp_mo":  "#FF2A2B",  # Red
    "insurance_exp_mo":     "#FFABAB",  # Light Red
    "hoa_exp_mo":           "#2AB09D",  # Light Green
    "maintenance_exp_mo":   "#7EEFA1",  # Green
    "utility_exp_mo":       "#FF8700",  # Organe
    "management_exp_mo":    "#FFD16A",  # Light Orange
    "pmi_exp_mo":           "#9030A1",  # Purple
}

TITLE_FONT = dict(family="Arial, sans-serif", size=24)

def merge_simulations(sim_df_a, sim_df_b, append_cols, prefix):
        """
        Sim df A keeps all it columns
        Sim df B keeps the merge columns with a prefix and is joined to sim df A on index
        """
        sim_df_b = sim_df_b[append_cols]
        sim_df_b = sim_df_b.rename(columns={col: f"{prefix}_{col}" for col in append_cols})
        return sim_df_a.join(sim_df_b)


def local_css(file_name):
    with open(file_name) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def dict_to_metrics(data_dict):
    st.container(height=10, border=False)
    for key, value in data_dict.items():
        st.metric(label=f":orange[{key}]", value=value)


def get_tab_columns():
    col1, _, col2 =  st.columns([4, .3, 12])
    return col1, col2


###########################################################
#               Input field functions                     #
###########################################################


def rate_selectbox_input(label, options, key, help=None):
    percent = st.selectbox(
        label=f"{label} (%)",
        key=key,
        options=options,
        help=help
    )
    return percent


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


def get_plot(yearly_df, cols, names, title, xlim, mode, 
             percent=False, height=HEIGHT, width=WIDTH, 
             colors=PLOT_COLORS, line_config=None, annotation_config=None
    ):
    hovertemplate = '$%{y:,.0f}'
    if percent:
        hovertemplate = '%{y:.2%}'  # Formats y as a percentage

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
        title_font=TITLE_FONT
    )

    fig.update_xaxes(range=[0, xlim+1])

    if line_config:
        fig.add_shape(**line_config)

    if annotation_config:
        fig.add_annotation(**annotation_config)


    fig_display(fig)


def pie_chart(yearly_df):
    df = yearly_df.loc[0:0, list(COLOR_MAP.keys())]
    df = df.T.reset_index().rename(columns={"index": "name", 0: "value"})
    df = df.join(pd.DataFrame.from_dict(COLOR_MAP, orient='index', columns=["color"]), on="name")
    df['order'] = df['name'].apply(lambda x: list(COLOR_MAP.keys()).index(x))
    df = df.sort_values('order').drop('order', axis=1)
    df["formatted_value"] = df["value"].apply(lambda x: format_currency(x))
    df["name"] = df["name"].apply(lambda x: format_label_string(x))
    df = df[df["value"] > 0]

    total = format_currency(df["value"].sum())

    fig = go.Figure()

    fig.add_trace(go.Pie(
        values=df['value'].values, 
        labels=df['name'].values,
        marker_colors=df["color"].values,
        hole=0.6,
        direction ='clockwise', 
        sort=False,
        textposition='outside',
        text=df["formatted_value"], 
        textinfo='label+text',
        marker=dict(line=dict(color='#000000', width=2)),
        hoverinfo = 'none'
    ))

    fig.add_annotation(dict(
        text=f"Total: {total}", 
        x=0.5, y=0.5, font_size=30, showarrow=False
    ))

    fig.update_layout(
        title="Monthly Expenses in First Year",
        showlegend=False, 
        height=HEIGHT,
        width=WIDTH,
        title_font=TITLE_FONT
    )

    fig_display(fig)


def stacked_bar(yearly_df):
    zero_sum_cols = [k for k in COLOR_MAP.keys() if yearly_df[k].sum() == 0]
    color_map_redux = {k: v for k, v in COLOR_MAP.items() if k not in zero_sum_cols}

    fig = go.Figure()

    for col, color in color_map_redux.items():
        fig.add_trace(go.Bar(
            x=yearly_df.index + 1, 
            y=yearly_df[col], 
            name=format_label_string(col),
            hoverinfo='y',
            hovertemplate='$%{y:,.0f}',
            marker_color=color
        ))

    if yearly_df["total_income"].sum() > 0:
        fig.add_trace(go.Scatter(
            x=yearly_df.index + 1, 
            y=yearly_df["adj_total_income_mo"], 
            mode='markers',
            name="Total Rental Income",
            hoverinfo='y',
            hovertemplate='$%{y:,.0f}',
            # add a black boarder to the markers
            marker=dict(size=12, color='white', line=dict(color='black', width=3)),
        ))
        
    fig.update_layout(
        title="Monthly Expenses Over Time (Hope they see this down here)",
        yaxis=dict(title='Dollars ($)', tickformat='$,.0f'),
        barmode='stack',
        height=HEIGHT,
        width=WIDTH,
        xaxis=dict(title='Year', tickmode='array', tickvals=np.arange(5, 31, 5)),
        title_font=TITLE_FONT
    )

    fig.update_xaxes(range=[0, 31])
    fig_display(fig)


###########################################################
#               Plot Analysis                             #
###########################################################
    
def min_crossover(list_a, list_b):
    """Return the index of the first element in list_a that is greater than list_b."""
    for i in range(len(list_a)):
        if list_a[i] > list_b[i]:
            return i
    return -1