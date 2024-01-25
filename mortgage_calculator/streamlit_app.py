from math import *
from dataclasses import dataclass

import streamlit as st
from streamlit import session_state as ssts
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from utils import *
from utils_finance import *
from st_text import *
from session_state_keys import Key

st.set_page_config(layout="wide")

SHOW_TEXT = False
MONTHS = np.arange(360)


@st.cache_data
def load_housing_data():
    return pd.read_csv('./mortgage_calculator/data/city_housing_data.csv')

housing_db = load_housing_data()

@st.cache_data
def get_region_options():
    return housing_db["region"].unique()

region_options = get_region_options()


@dataclass
class HousingDataLookup:
    med_price: float
    med_ppsf: float
    med_price_cagr: float
    med_ppsf_cagr: float
    tax_rate: float


def get_associated_data(region):
    row = housing_db[housing_db["region"] == region]
    return HousingDataLookup(
        row["median_sale_price"].values[0], 
        row["median_ppsf"].values[0],
        row["median_sale_price_cagr"].values[0],
        row["median_ppsf_cagr"].values[0],
        row["property_tax_rate"].values[0],
    )


def ssts_rate(key):
    return ssts[key] / 100


def initialize_session_state():
    if 'initialized' not in ssts:
        # app management
        ssts['initialized'] = True

        # user data
        ssts[Key.region] = region_options[0]
        housing_data = get_associated_data(region_options[0])

        ssts[Key.init_home_value] = int(housing_data.med_price)
        ssts[Key.down_payment] = 50000
        ssts[Key.interest_rate] = 7.0
        ssts[Key.yearly_home_value_growth] = housing_data.med_price_cagr * 100
        ssts[Key.property_tax_rate] = housing_data.tax_rate

        ssts[Key.closing_costs_rate] = 3.0
        ssts[Key.pmi_rate] = 0.5
        ssts[Key.insurance_rate] = 0.35
        ssts[Key.init_hoa_fees] = 0
        ssts[Key.init_monthly_maintenance] = 0
        ssts[Key.inflation_rate] = 3.0

        ssts[Key.realtor_rate] = 6.0
        ssts[Key.sell_closing_costs_rate] = 1.0
        ssts[Key.additional_selling_costs] = 5000

        ssts[Key.rent] = 2000
        ssts[Key.rent_increase] = 6.0
        ssts[Key.stock_growth_rate] = 7.0
        ssts[Key.stock_tax_rate] = 15.0


### how do we run this whenever the region changes?
def update_region():
    """Unique function for updating region because it has to change other values."""

    housing_data = get_associated_data(ssts[Key.region])
    ssts[Key.init_home_value] = housing_data.med_price
    ssts[Key.yearly_home_value_growth] = housing_data.med_price_cagr * 100
    ssts[Key.property_tax_rate] = housing_data.tax_rate


def rate_input(label, key=None, min_value=0.0, max_value=99.0, step=0.1):
    percent = st.number_input(
        label=f"{label} (%)", 
        min_value=min_value, 
        max_value=max_value, 
        step=step,
        key=key
    )
    return percent


def dollar_input(label, key=None, min_value=0, max_value=1e8):
    """Function that will calculate the step input based on the default value.
    The step is 1eN where N is one less than the number of digits in the default value.
    """

    step=10
    #if default > 100:
    #    step = int(10 ** (floor(log10(default)) - 1))
    return st.number_input(
        f"{label} ($)",
        min_value=int(min_value), 
        max_value=int(max_value),
        step=step,
        key=key,
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


def mortgage_inputs():
    st.markdown("### Mortgage Inputs")
    populate_columns([
        lambda: st.selectbox("Region", key=Key.region, options=region_options, on_change=update_region),
        lambda: dollar_input("Home Price", Key.init_home_value),
        lambda: dollar_input("Down Payment", Key.down_payment),
    ])
    populate_columns([
        lambda: rate_input("Interest Rate", Key.interest_rate),
        lambda: rate_input("Yearly Home Value Growth", Key.yearly_home_value_growth),
        lambda: rate_input("Property Tax Rate", Key.property_tax_rate)
    ])


def other_inputs():
    with st.expander("Expand for More Inputs", expanded=False):
        populate_columns([
            lambda: rate_input("Closing Costs", Key.closing_costs_rate),
            lambda: rate_input("PMI Rate", Key.pmi_rate),
            lambda: rate_input("Insurance Rate", Key.insurance_rate),
        ], 3)
        populate_columns([
            lambda: dollar_input("HOA Fees", Key.init_hoa_fees),
            lambda: dollar_input("Monthly Maintenance", Key.init_monthly_maintenance),
            lambda: rate_input("Inflation Rate", Key.inflation_rate)
        ], 3)


def selling_inputs():
    with st.expander("Home Selling Inputs", expanded=False):
        populate_columns([
            lambda: rate_input("Realtor Fee", Key.realtor_rate),
            lambda: rate_input("Selling Closing Costs", Key.sell_closing_costs_rate),
            lambda: dollar_input("Additional Selling Costs", Key.additional_selling_costs)
        ], 3)


def renting_inputs():
    with st.expander("Renting Comparison Inputs", expanded=False):
        populate_columns([
            lambda: dollar_input("Current Monthly Rent", Key.rent),
            lambda: rate_input("Yearly Rent Increase", Key.rent_increase),
            lambda: rate_input("Stock Return Rate", Key.stock_growth_rate)
        ], 3)
        populate_columns([
            lambda: rate_input("Stock Tax Rate", Key.stock_tax_rate)
        ], 3)


def run_simulation():

    # set once
    closing_costs = ssts[Key.init_home_value] * ssts_rate(Key.closing_costs_rate)
    effective_down_payment = max(ssts[Key.down_payment] - closing_costs, 0)
    loan_amount = ssts[Key.init_home_value] - effective_down_payment
    monthly_payment = get_monthly_payment_amount(loan_amount, ssts_rate(Key.interest_rate))

    ### update yearly
    
    # home
    pmi_cost = get_monthly_pmi(ssts[Key.init_home_value], loan_amount, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
    property_tax_cost = ssts[Key.init_home_value] * ssts_rate(Key.property_tax_rate) / 12
    insurance_cost = ssts[Key.init_home_value] * ssts_rate(Key.insurance_rate) / 12
    hoa_costs = ssts[Key.init_hoa_fees]
    maintenance_costs = ssts[Key.init_monthly_maintenance]
    
    # rent / stock
    rent = ssts[Key.rent]
    portfolio_value = ssts[Key.down_payment]

    ### update monthly
    loan_balance = loan_amount
    home_value = ssts[Key.init_home_value]
    pmi_required = pmi_cost > 0

    # only wrinkle with cumulative values is that effective down payment is added to first principal payment
    # and closing costs are added to first misc payment
    # each row represents cost at the end of that month and the values at the end of that month
    # first row, 0 is the end of the first month since closing

    data = []
    for month in MONTHS:

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
        }

        # pay all your stuff at the beginning of the month
        month_data["interest"] = loan_balance * ssts_rate(Key.interest_rate) / 12
        month_data["principal"] = monthly_payment - month_data["interest"]
        month_data["property_tax"] = property_tax_cost
        month_data["insurance"] = insurance_cost
        month_data["hoa"] = hoa_costs
        month_data["maintenance"] = maintenance_costs
        if pmi_required:
            month_data["pmi"] = pmi_cost
        else:
            month_data["pmi"] = 0

        month_data["rent"] = rent

        # end of month, update values

        # update portfolio value
        contribution = (monthly_payment + property_tax_cost + insurance_cost + hoa_costs + maintenance_costs + month_data["pmi"]) - rent
        contribution = max(contribution, 0)
        portfolio_value = add_growth(portfolio_value, ssts_rate(Key.stock_growth_rate), 1, contribution)
        month_data["portfolio_value"] = portfolio_value

        # update loan balance
        loan_balance -= month_data["principal"]
        month_data["loan_balance"] = loan_balance

        # update home value
        home_value = add_growth(home_value, ssts_rate(Key.yearly_home_value_growth), months=1)
        month_data["home_value"] = home_value

        # update monthly maintenance costs
        maintenance_costs = add_growth(maintenance_costs, ssts_rate(Key.inflation_rate), months=1)

        # update if pmi is required but dont update value unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
        pmi_required = true_pmi > 0


        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_cost = home_value * ssts_rate(Key.property_tax_rate) / 12
            insurance_cost = home_value * ssts_rate(Key.insurance_rate) / 12
            hoa_costs = add_growth(hoa_costs, ssts_rate(Key.inflation_rate), 12)
            pmi_cost = true_pmi
            rent = add_growth(rent, ssts_rate(Key.rent_increase), 12)

        data.append(month_data)

    return pd.DataFrame(data)


COST_COLS = ["interest", "principal", "pmi", "insurance", "property_tax", "hoa", "maintenance"]


def post_process_sim_df(monthly_df):
    monthly_df = monthly_df.set_index("index")

    # add total and misc columns
    monthly_df["total"] = monthly_df[
        COST_COLS
    ].sum(axis=1)
    monthly_df["misc"] = monthly_df[
        ["pmi", "insurance", "property_tax", "hoa", "maintenance"]
    ].sum(axis=1)

    yearly_df = monthly_df.groupby("year").agg(
        # sum cols
        pmi_sum=("pmi", "sum"),
        insurance_sum=("insurance", "sum"),
        property_tax_sum=("property_tax", "sum"),
        hoa_sum=("hoa", "sum"),
        maintenance_sum=("maintenance", "sum"),
        interest_sum=("interest", "sum"),
        principal_sum=("principal", "sum"),
        misc_sum=("misc", "sum"),
        total_sum=("total", "sum"),
        rent_sum=("rent", "sum"),
        # mean cols
        pmi_mean=("pmi", "mean"),
        insurance_mean=("insurance", "mean"),
        property_tax_mean=("property_tax", "mean"),
        hoa_mean=("hoa", "mean"),
        maintenance_mean=("maintenance", "mean"),
        interest_mean=("interest", "mean"),
        principal_mean=("principal", "mean"),
        misc_mean=("misc", "mean"),
        total_mean=("total", "mean"),
        # home value max
        home_value_max=("home_value", "max"),
        loan_balance_max=("loan_balance", "max"),
        portfolio_max=("portfolio_value", "max"),
    )

    # cumulative cols for principal, interest, total, misc
    cumulative_df = yearly_df[["total_sum", "interest_sum", "principal_sum", "misc_sum", "rent_sum"]].cumsum()
    cumulative_df.columns = [f"cum_{colname}" for colname in cumulative_df.columns]

    yearly_df = pd.concat([yearly_df, cumulative_df], axis=1)

    realtor_rate = ssts_rate(Key.realtor_rate)
    sell_closing_costs_rate = ssts_rate(Key.sell_closing_costs_rate)
    additional_selling_costs = ssts[Key.additional_selling_costs]
    closing_costs = ssts_rate(Key.closing_costs_rate) * ssts[Key.init_home_value]

    yearly_df["equity"] = yearly_df["home_value_max"] - yearly_df["loan_balance_max"]
    yearly_df["cip_homeownership"] = \
        (yearly_df["equity"] * (1-realtor_rate-sell_closing_costs_rate)) \
            - closing_costs - yearly_df["cum_interest_sum"] - yearly_df["cum_misc_sum"] - additional_selling_costs
    
    yearly_df["cip_renting"] = yearly_df["portfolio_max"] * (1-ssts_rate(Key.stock_tax_rate)) - yearly_df["cum_rent_sum"]
    return yearly_df


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


def format_df_row_values(df, row_num, cols):
    """Take colums from row of dataframe and format for pie chart.
    
    Output is df with column:
        name: name of cost
        value: value of cost
        formatted_value: money formatted value of cost
    """
    row = df.loc[row_num:row_num, cols].T.reset_index().rename(columns={"index": "name", 0: "value"})
    row["formatted_value"] = row["value"].apply(lambda x: format_currency(x))
    row["name"] = row["name"].apply(lambda x: format_label_string(x))
    row = row[row["value"] > 0]
    row = row.sort_values(by=["value"], ascending=False)
    return row


def disaply_pie_chart(df):
    """df must have columns: name, value, formatted_value"""
    sum = format_currency(df["value"].sum())
    fig = px.pie(df, values='value', names='name', hole=0.7)
    fig.update_layout(showlegend=False, height=700, width=700)
    fig.update_layout(annotations=[dict(text=f"Total: {sum}", x=0.5, y=0.5, font_size=50, showarrow=False)])
    fig.update_traces(textposition='outside', text=df["formatted_value"], textinfo='label+text')
    fig_display(fig)


def display_stacked_bar_chart(df, cols, names, title):
    """df must have columns: name, value, formatted_value"""
    fig = go.Figure()
    
    for col, name in zip(cols, names):
        fig.add_trace(go.Bar(
            x=df.index + 1, 
            y=df[col], 
            name=name,
            hoverinfo='y',
            hovertemplate='$%{y:,.0f}'
        ))

    fig.update_layout(
        title=title,
        xaxis=dict(
            title='Years',
        ),
        yaxis=dict(
            title='Dollars',
            tickformat='$,.0f'
        ),
        barmode='stack',
        height=700
    )
    fig_display(fig)


def display_line_chart(df, cols, names, title):
    fig = go.Figure()

    for col, name in zip(cols, names):
        fig.add_trace(go.Scatter(
            x=df.index + 1, 
            y=df[col], 
            mode='lines', 
            name=name,
            hoverinfo='y',
            hovertemplate='$%{y:,.0f}'
        ))

    # Update layout
    fig.update_layout(
        title=title,
        xaxis=dict(
            title='Years',
        ),
        yaxis=dict(
            title='Dollars',
            tickformat='$,.0f'
        ),
        barmode='stack',
        height=700,
        legend=dict(x=0.1, y=0.95, xanchor='center', yanchor='top', orientation='v'),
        hovermode='x'
    )

    # Display the figure
    fig_display(fig)


def calculate_summary(yearly_df):
    # add table that shows summary of the mortgage stuff
    summary_values = {
        "home_price": ssts[Key.init_home_value],
        # TODO fix some things
        #"effective_down_payment": effective_down_payment,
        #"closing_costs": closing_costs,
        #"total_loan_amount": loan_amount,
        # excludes down payment and closing costs
        "total_home_paid": sum(yearly_df["total_sum"]),
        "total_interest_paid": sum(yearly_df["interest_sum"]),
        "total_tax_paid": sum(yearly_df["property_tax_sum"]),
        "total_pmi_paid": sum(yearly_df["pmi_sum"]),
        "number_of_pmi_payments": len([x for x in monthly_df["pmi"] if x > 0]),
    }

    # format keys and values as strings
    summary_values = {key.title().replace("_", " "): format_currency(value) for key, value in summary_values.items()}

    # Find the length of the longest key
    max_key_length = max(len(key) for key in summary_values.keys())
    max_value_length = max(len(value) for value in summary_values.values())

    # Pad each key to have the same length
    padded_dict = {key.ljust(max_key_length): value.rjust(max_value_length) for key, value in summary_values.items()}

    st.write(padded_dict)


def hide_fullscreen_button():
    hide_fs = '''
        <style>
        button[title="View fullscreen"]{
            visibility: hidden;}
        </style>
        '''
    st.markdown(hide_fs, unsafe_allow_html=True)


def drop_sum_zero(df, cols):
    """Drop columns in cols if the sum of the column is zero."""
    drop_cols = df[cols].sum() == 0
    return drop_cols[drop_cols].index


def main():

    initialize_session_state()
    hide_fullscreen_button()

    yearly_df = post_process_sim_df(run_simulation())

    mean_first_year_cost_cols = [f"{colname}_mean" for colname in COST_COLS]
    first_year_df = format_df_row_values(yearly_df, 0, mean_first_year_cost_cols)

    col1, _, col2 = st.columns([3, .5, 3])

    with col1:
        get_intro()
        mortgage_inputs()
        other_inputs()
        selling_inputs()
        renting_inputs()
    with col2:
        mp, mp_ot, summary, renting = st.tabs([
            "Monthly Payments", "Monthly Payments over Time", "Summary", "Rent Comparison"
            ])

        with mp:
            disaply_pie_chart(first_year_df)

        with mp_ot:
            cols = [f"{x}_mean" for x in COST_COLS]
            drop_cols = drop_sum_zero(yearly_df, cols)
            cols = [x for x in cols if x not in drop_cols]
            names = [format_label_string(x) for x in cols]

            display_stacked_bar_chart(
                yearly_df,
                cols=cols, 
                names=names,
                title="Monthly Costs"
            )

        with summary:
            st.header("An owl")
            #calculate_summary()
            st.image("https://static.streamlit.io/examples/owl.jpg", width=200, use_column_width=True)

        with renting:
            display_line_chart(
                yearly_df, 
                cols=["cip_homeownership", "cip_renting"], 
                names=["Own", "Rent"],
                title="Cumulative Net Cash in Pocket"
            )