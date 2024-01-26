from math import *
from dataclasses import dataclass
from time import sleep

import streamlit as st
from streamlit import components
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

        #ssts[Key.init_home_value] = int(housing_data.med_price)
        ssts[Key.init_home_value] = 300000
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
        ssts[Key.extra_monthly_payments] = 0
        ssts[Key.number_of_payments] = 0

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
    #ssts[Key.init_home_value] = housing_data.med_price
    ssts[Key.yearly_home_value_growth] = housing_data.med_price_cagr * 100
    ssts[Key.property_tax_rate] = housing_data.tax_rate


def rate_input(label, key=None, min_value=0.0, max_value=99.0, step=0.1, asterisk=False):
 
    if asterisk:
        label = ":orange[**]" + label
    
    percent = st.number_input(
        label=f"{label} (%)", 
        min_value=min_value, 
        max_value=max_value, 
        step=step,
        key=key
    )
    return percent


def dollar_input(label, key=None, min_value=0, max_value=1e8, step=10, asterisk=False):
    """Function that will calculate the step input based on the default value.
    The step is 1eN where N is one less than the number of digits in the default value.
    """

    if asterisk:
        label = ":orange[**]" + label

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
        lambda: rate_input("Interest", Key.interest_rate),
        lambda: rate_input("Home Value Growth", Key.yearly_home_value_growth, asterisk=True),
        lambda: rate_input("Property Tax", Key.property_tax_rate, asterisk=True)
    ])


def other_inputs():
    with st.expander("Additional Mortgage Inputs", expanded=False):
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


def extra_mortgage_payment_inputs():
    with st.expander("Extra Monthly Principal Payments", expanded=False):
        populate_columns([
            lambda: dollar_input("Extra Monthly Payments", Key.extra_monthly_payments),
            lambda: st.number_input("Number of Payments", min_value=0, max_value=int(1e4), key=Key.number_of_payments),
        ], 3)


def renting_inputs():
    with st.expander("Renting Comparison Inputs", expanded=False):
        populate_columns([
            lambda: dollar_input("Current Monthly Rent", Key.rent),
            lambda: rate_input("Yearly Rent Increase", Key.rent_increase),
            lambda: rate_input("Stock Return Rate", Key.stock_growth_rate)
        ], 3)


def selling_inputs():
    with st.expander("Home Selling Inputs", expanded=False):
        populate_columns([
            lambda: rate_input("Realtor Fee", Key.realtor_rate),
            lambda: rate_input("Selling Closing Costs", Key.sell_closing_costs_rate),
            lambda: dollar_input("Additional Selling Costs", Key.additional_selling_costs)
        ], 3)
        populate_columns([
            lambda: rate_input("Stock Tax Rate", Key.stock_tax_rate)
        ], 3)


def run_simulation():
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.
    """

    ########################################################################
    #      set once, these dont change throughout the simulation           #
    ########################################################################

    # TODO, these should be saved at state initialization. Maybe. 
    # State is closely tied to inputs, not derived values, so maybe not.
    CLOSING_COSTS = ssts[Key.init_home_value] * ssts_rate(Key.closing_costs_rate)
    EFFECTIVE_DOWN_PAYMENT = max(ssts[Key.down_payment] - CLOSING_COSTS, 0)
    LOAN_AMOUNT = ssts[Key.init_home_value] - EFFECTIVE_DOWN_PAYMENT
    MONTHLY_PAYMENT = get_monthly_payment_amount(LOAN_AMOUNT, ssts_rate(Key.interest_rate))

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_cost = get_monthly_pmi(ssts[Key.init_home_value], LOAN_AMOUNT, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
    property_tax_cost = ssts[Key.init_home_value] * ssts_rate(Key.property_tax_rate) / 12
    insurance_cost = ssts[Key.init_home_value] * ssts_rate(Key.insurance_rate) / 12
    hoa_cost = ssts[Key.init_hoa_fees]
    rent_cost = ssts[Key.rent]
    portfolio_value = ssts[Key.down_payment]

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    maintenance_cost = ssts[Key.init_monthly_maintenance]
    loan_balance = LOAN_AMOUNT
    home_value = ssts[Key.init_home_value]
    pmi_required = pmi_cost > 0
    extra_payment = ssts[Key.extra_monthly_payments]


    data = []
    for month in np.arange(12 * 30):

        interest_paid = loan_balance * ssts_rate(Key.interest_rate) / 12
        
        # cant pay more principal than loan balance
        principal_paid = MONTHLY_PAYMENT - interest_paid
        if principal_paid >= loan_balance:
            principal_paid = loan_balance

        loan_balance -= principal_paid

        # stop paying extra payments after allotted number of payments
        # cant pay more extra payments than loan balance
        if month > ssts[Key.number_of_payments] - 1:
            extra_payment = 0
        elif extra_payment >= loan_balance:
                extra_payment = loan_balance

        loan_balance -= extra_payment

        # pay pmi if required
        pmi_paid = 0
        if pmi_required:
            pmi_paid = pmi_cost

        # update portfolio value
        contribution = (
            interest_paid +
            principal_paid +
            extra_payment +
            property_tax_cost +
            insurance_cost +
            hoa_cost +
            maintenance_cost +
            pmi_paid
        ) - rent_cost

        contribution = max(contribution, 0)
        portfolio_value = add_growth(
            portfolio_value, 
            ssts_rate(Key.stock_growth_rate), 
            months=1, 
            monthly_contribution=contribution
        )

        # update home value
        home_value = add_growth(home_value, ssts_rate(Key.yearly_home_value_growth), months=1)

        # update monthly maintenance costs
        maintenance_cost = add_growth(maintenance_cost, ssts_rate(Key.inflation_rate), months=1)

        # update monthly payments with inflation TODO keep this? Make Yearly?
        extra_payment = add_growth(extra_payment, ssts_rate(Key.inflation_rate), months=1)

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
        pmi_required = true_pmi > 0

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_cost = home_value * ssts_rate(Key.property_tax_rate) / 12
            insurance_cost = home_value * ssts_rate(Key.insurance_rate) / 12
            hoa_cost = add_growth(hoa_cost, ssts_rate(Key.inflation_rate), 12)
            rent_cost = add_growth(rent_cost, ssts_rate(Key.rent_increase), 12)
            pmi_cost = true_pmi

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # costs and payments
            "interest": interest_paid,
            "principal": principal_paid,
            "extra_payment": extra_payment,
            "property_tax": property_tax_cost,
            "insurance": insurance_cost,
            "hoa": hoa_cost,
            "maintenance": maintenance_cost,
            "pmi": pmi_paid,
            "rent": rent_cost,
            # balances and values
            "loan_balance": loan_balance,
            "home_value": home_value,
            "portfolio_value": portfolio_value,
        }

        data.append(month_data)

    return pd.DataFrame(data).set_index("index")


COST_COLS = ["interest", "principal", "pmi", "insurance", "property_tax", "hoa", "maintenance", "extra_payment"]


def post_process_sim_df(sim_df):
    # only wrinkle with cumulative values is that effective down payment is added to first principal payment
    # and closing costs are added to first misc payment

    # add total and misc columns
    sim_df["total"] = sim_df[COST_COLS].sum(axis=1)
    sim_df["misc"] = sim_df[["pmi", "insurance", "property_tax", "hoa", "maintenance"]].sum(axis=1)

    # List of columns for sum and mean aggregations
    sum_mean_cols = [
        "pmi", "insurance", "property_tax", "hoa", 
        "maintenance", "interest", "principal", 
        "misc", "total", "rent", "extra_payment"
    ]

    # Columns for max aggregation
    max_cols = ["home_value", "loan_balance", "portfolio_value"]

    # Generate aggregation dictionary
    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}
    agg_dict.update({col: 'max' for col in max_cols})

    # Group and aggregate
    year_df = sim_df.groupby("year").agg(agg_dict)

    # Renaming columns for clarity
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    # cumulative cols for principal, interest, total, misc
    cols_to_cumsum = ["total_sum", "interest_sum", "principal_sum", "extra_payment_sum", "misc_sum", "rent_sum"]

    for col in cols_to_cumsum:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # Define rates and costs upfront for clarity
    realtor_rate = ssts_rate(Key.realtor_rate)
    sell_closing_costs_rate = ssts_rate(Key.sell_closing_costs_rate)
    closing_costs = ssts_rate(Key.closing_costs_rate) * ssts[Key.init_home_value]
    additional_selling_costs = ssts[Key.additional_selling_costs]
    stock_tax_rate = ssts_rate(Key.stock_tax_rate)

    # Calculate equity
    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_max"]

    # money you pay that doesnt go towards equity
    year_df["home_costs"] = closing_costs + year_df["cum_interest_sum"] + year_df["cum_misc_sum"]
    #year_df["selling_costs"] = year_df["equity"] * (realtor_rate + sell_closing_costs_rate) + additional_selling_costs
    year_df["equity_less_costs"] = year_df["equity"] - year_df["home_costs"] #- year_df["selling_costs"]

    # TODO should incorperate selling costs and stock taxes?
    # TODO maybe have a button that automatically adds stock/home selling costs with no custom inputs?
    # could there be other exist strategies

    # Calculate cost of selling property (Cost Incurred from Property Sale)
    # year_df["cip_homeownership"] = year_df["equity_less_costs"] - year_df["home_costs"]

    # Calculate cost of renting (Cost Incurred from Renting)
    # year_df["cip_renting"] = year_df["portfolio_value_max"] * (1 - stock_tax_rate) - year_df["cum_rent_sum"]

    #year_df["stocks_less_renting"] = year_df["portfolio_value_max"] * (1 - stock_tax_rate) - year_df["cum_rent_sum"]
    year_df["stocks_less_renting"] = year_df["portfolio_value_max"] - year_df["cum_rent_sum"]

    return year_df


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
    """Take values from single row of dataframe and formats for pie chart.
    
    Output is df with column:
        name: name of column
        value: value of column
        formatted_value: money formatted value
    """
    row = df.loc[row_num:row_num, cols].T.reset_index().rename(columns={"index": "name", 0: "value"})
    row["formatted_value"] = row["value"].apply(lambda x: format_currency(x))
    row["name"] = row["name"].apply(lambda x: format_label_string(x))
    row = row[row["value"] > 0]
    row = row.sort_values(by=["value"], ascending=False)
    return row


def summary_metrics(yearly_df):

    closing_costs = ssts[Key.init_home_value] * ssts_rate(Key.closing_costs_rate)
    effective_down_payment = max(ssts[Key.down_payment] - closing_costs, 0)
    loan_amount = ssts[Key.init_home_value] - effective_down_payment

    # total amount of interest paid with no extra payments
    default_interest_paid = get_total_interest_paid(loan_amount, ssts_rate(Key.interest_rate))
    actual_interest_paid = sum(yearly_df['interest_sum'])

    metrics_col1 = {
        "Loan Amount": loan_amount,
        "Closing Costs": closing_costs,
        "Effective Down Payments": effective_down_payment,
        "Monthly Payments": 1,
    }

    metrics_col2 = {
        "Mortgage Payments": sum(yearly_df['total_sum']),
        "Interest Paid": actual_interest_paid,
        "Interest Default": default_interest_paid,
        "Interest Saved": max(0, default_interest_paid - actual_interest_paid),
        "Taxes Paid": sum(yearly_df['property_tax_sum']),  
        "Other Expenses Paid": sum(yearly_df['misc_sum']),
        "PMI": sum(yearly_df['pmi_sum']),
    }
    
    def format_values(metrics):
        for key in metrics:
            metrics[key] = format_currency(metrics[key])

    format_values(metrics_col1)
    format_values(metrics_col2)

    # Using columns to layout the summary values
    _, col1, col2 = st.columns([1, 2, 2])

    with col1:
        for key, value in metrics_col1.items():
            st.metric(label=key, value=value, delta="")

    with col2:
        for key, value in metrics_col2.items():
            st.metric(label=key, value=value)



def hide_fullscreen_button():
    hide_fs = '''
        <style>
        button[title="View fullscreen"]{
            visibility: hidden;}
        </style>
        '''
    st.markdown(hide_fs, unsafe_allow_html=True)


def get_zero_sum_cols(df, cols):
    """Finds columns in cols that have a sum of zero in the df."""
    return [col for col in cols if df[col].sum() == 0]


def run_calculator():

    initialize_session_state()
    hide_fullscreen_button()

    yearly_df = post_process_sim_df(run_simulation())

    col1, _, col2 = st.columns([10, 1, 12])

    with col1:
        get_intro()
        mortgage_inputs()
        other_inputs()
        extra_mortgage_payment_inputs()
        renting_inputs()
        #selling_inputs()

    with col2:
        tab_mp, tab_mpot, tab_hv, tab_rent, tab_summary = st.tabs([ 
            "Monthly Payments", 
            "Monthly Payments Over Time", 
            "Home Value",
            "Rent Comparison", 
            "Summary"
        ])

        # like the way that principle and interest are blues and everything else stands apart from them
        col_color_map = {
                "interest_mean":      "#1b9e77",  # Teal Blue
                "principal_mean":     "#d95f02",  # Orange
                "property_tax_mean":  "#e6ab02",  # Burnt Yellow
                "insurance_mean":     "#66a61e",  # Grass Green
                "hoa_mean":           "#a6761d",  # Dark Brown
                "maintenance_mean":   "#6666ff",  # Deep Blue
                "pmi_mean":           "#e7298a",  # Pinkish Red
                "extra_payment_mean": "#7570b3",  # Purple
        }


        ########################################################################
        #      Pie                                                             #
        ########################################################################

        # TODO use a sunburst that groups the money spent into equity and costs?
        # use a sunburst for little gaps in the pie chart.
        # map colors and order correctly

        with tab_mp:
            pie_df = format_df_row_values(yearly_df, 0, col_color_map.keys())
            sum = format_currency(pie_df["value"].sum())
            fig = px.pie(pie_df, values='value', names='name', hole=0.7)
            fig.update_layout(
                showlegend=False, height=700, width=700,
                annotations=[dict(text=f"Total: {sum}", x=0.5, y=0.5, font_size=50, showarrow=False)],
                title="Average Monthly Costs in First Year"
            )
            fig.update_traces(textposition='outside', text=pie_df["formatted_value"], textinfo='label+text')
            fig_display(fig)


        ########################################################################
        #      Stacked Bar                                                     #
        ########################################################################

        with tab_mpot:
            zero_sum_cols = get_zero_sum_cols(yearly_df, col_color_map.keys())
            col_color_map = {k: v for k, v in col_color_map.items() if k not in zero_sum_cols}

            fig = go.Figure()
            for col, color in col_color_map.items():
                fig.add_trace(go.Bar(
                    x=yearly_df.index + 1, 
                    y=yearly_df[col], 
                    name=format_label_string(col),
                    hoverinfo='y',
                    hovertemplate='$%{y:,.0f}',
                    marker_color=color
                ))

            fig.update_layout(
                title="Average Monthly Costs Over Time",
                xaxis=dict(
                    title='Year',
                ),
                yaxis=dict(
                    title='Average Monthly Cost',
                    tickformat='$,.0f'
                ),
                barmode='stack',
                height=700
            )
            fig_display(fig)


        ########################################################################
        #      Home Value                                                      #
        ########################################################################

        with tab_hv:
            cols=["equity", "equity_less_costs", "home_value_max"]
            names=["Equity", "Equity minus Costs", "Home Value"]

            fig = go.Figure()

            for col, name in zip(cols, names):
                fig.add_trace(go.Scatter(
                    x=yearly_df.index + 1, 
                    y=yearly_df[col], 
                    mode='lines', 
                    name=name,
                    hoverinfo='y',
                    hovertemplate='$%{y:,.0f}'
                ))

            # Update layout
            fig.update_layout(
                title="Home Value and Equity Over Time",
                xaxis=dict(
                    title='Year',
                ),
                yaxis=dict(
                    title='Value at End of Year',
                    tickformat='$,.0f'
                ),
                height=700,
                #legend=dict(x=0.3, y=0.92, xanchor='center', yanchor='top', orientation='v'),
                hovermode='x'
            )

            # Display the figure
            fig_display(fig)


        ########################################################################
        #      Renting                                                         #
        ########################################################################

        with tab_rent:
            cols=["equity_less_costs", "stocks_less_renting"]
            names=["Equity - Costs", "Stocks - Renting"]
            fig = go.Figure()

            for col, name in zip(cols, names):
                fig.add_trace(go.Scatter(
                    x=yearly_df.index + 1, 
                    y=yearly_df[col], 
                    mode='lines', 
                    name=name,
                    hoverinfo='y',
                    hovertemplate='$%{y:,.0f}'
                ))

            # Update layout
            fig.update_layout(
                title="Renting vs. Homeownership",
                xaxis=dict(
                    title='Year',
                ),
                yaxis=dict(
                    title='Value at End of Year',
                    tickformat='$,.0f'
                ),
                height=700,
                #legend=dict(x=0.3, y=0.92, xanchor='center', yanchor='top', orientation='v'),
                hovermode='x'
            )

            # Display the figure
            fig_display(fig)


        ########################################################################
        #      Summary                                                         #
        ########################################################################

        with tab_summary:
            summary_metrics(yearly_df)

run_calculator()