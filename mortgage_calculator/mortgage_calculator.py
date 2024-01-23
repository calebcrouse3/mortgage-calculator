import streamlit as st
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from math import *
from utils import *
from utils_finance import *
from st_text import *
from dataclasses import dataclass


SHOW_TEXT = False
MONTHS = np.arange(360)
CURRENT_YEAR = 2024


@st.cache_data
def load_housing_data():
    return pd.read_csv('./mortgage_calculator/data/city_housing_data.csv')


@st.cache_data
def get_region_options(housing_df):
    return housing_df["region"].unique()


@dataclass
class HousingDataLookup:
    med_price: float
    med_ppsf: float
    med_price_cagr: float
    med_ppsf_cagr: float
    tax_rate: float


def get_associated_data(selected_options, housing_df):
    row = housing_df[housing_df["region"] == selected_options]
    return HousingDataLookup(
        row["median_sale_price"].values[0], 
        row["median_ppsf"].values[0],
        row["median_sale_price_cagr"].values[0],
        row["median_ppsf_cagr"].values[0],
        row["property_tax_rate"].values[0],
    )


def rate_input(label, default, min_value=0.0, max_value=99.0, step=0.1):
    percent = st.number_input(
        label=f"{label} (%)", 
        min_value=min_value, 
        max_value=max_value, 
        value=default, 
        step=step
    )
    return percent / 100


def dollar_input(label, default, min_value=0, max_value=1e8):
    """Function that will calculate the step input based on the default value.
    The step is 1eN where N is one less than the number of digits in the default value.
    """

    step=10
    if default > 100:
        step = int(10 ** (floor(log10(default)) - 1))
    return st.number_input(
        f"{label} ($)", 
        min_value=min_value, 
        max_value=int(max_value), 
        value=int(default), 
        step=step
    )


def get_columns(n=6):
    return st.columns(n)


def populate_columns(values, dataclass):
    output_vals = []
    columns = get_columns()
    for col, value_func in zip(columns[:len(values)], values):
        with col:
            val = value_func()
            output_vals.append(val)
    return dataclass(*output_vals)


@dataclass
class MortgageInputs:
    region: str
    init_home_value: float
    down_payment: float
    interest_rate: float
    yearly_home_value_growth: float
    property_tax_rate: float


@dataclass
class OtherFactorsInputs:
    closing_costs_rate: float
    pmi_rate: float
    insurance_rate: float
    init_hoa_fees: float
    init_monthly_maintenance: float
    inflation_rate: float


@dataclass
class HomeSellingCostsInputs:
    realtor_rate: float
    sell_closing_costs_rate: float
    additional_selling_costs: float

    
@dataclass
class RentStockInputs:
    init_rent: float
    yearly_rent_increase: float
    stock_market_growth_rate: float
    stock_tax_rate: float


def get_mortgage_inputs(region_options, housing_df):
    st.header("Mortgage", anchor="mortgage")

    # if no region selected, default to first region
    if 'region' not in st.session_state:
        st.session_state['region'] = region_options[0]

    # get defaults from selected region
    housing_data = get_associated_data(st.session_state['region'], housing_df)

    # function to create region select box and update session state
    def region_select():
        region = st.selectbox("Region", region_options, key="region")
        return region

    return populate_columns(
        [
            lambda: region_select(),
            lambda: dollar_input("Home Price", housing_data.med_price),
            lambda: dollar_input("Down Payment", 50000),
            lambda: rate_input("Interest Rate", 7.0),
            lambda: rate_input("Yearly Home Value Growth", housing_data.med_price_cagr*100),
            lambda: rate_input("Property Tax Rate", housing_data.tax_rate)
        ],
        MortgageInputs
    )


# TODO need to keep session state even when they uncheck the box
def get_other_factors_inputs(show_other_factors):
    if show_other_factors:
        return populate_columns(
            [
                lambda: rate_input("Closing Costs", 3.0),
                lambda: rate_input("PMI Rate", 0.5),
                lambda: rate_input("Homeowners Insurance Rate", 0.35),
                lambda: dollar_input("HOA Fees", 0),
                lambda: dollar_input("Monthly Maintenance", 0),
                lambda: rate_input("Inflation Rate", 3.0)
            ],
            OtherFactorsInputs
        )
    else:
        # have to convert rates for defaults to decimal. 3.0% -> 0.03
        return OtherFactorsInputs(0.003, 0.005, 0.0035, 0, 0, 0.03)


def get_home_selling_costs_inputs():
    st.header("Home Selling Costs")
    return populate_columns(
        [
            lambda: rate_input("Realtor Fee", 6.0),
            lambda: rate_input("Selling Closing Costs", 1.0),
            lambda: dollar_input("Additional Selling Costs", 5000)
        ],
        HomeSellingCostsInputs
    )


def get_rent_stock_inputs():
    st.header("Rent + Stock")
    return populate_columns(
        [
            lambda: dollar_input("Current Monthly Rent", 2000),
            lambda: rate_input("Yearly Rent Increase", 3.0),
            lambda: rate_input("Stock Return Rate", 7.0),
            lambda: rate_input("Stock Tax Rate", 15.0)
        ],
        RentStockInputs
    )


def run_simluation(mort, other, sell, rent_stock):

    # set once
    closing_costs = mort.init_home_value * other.closing_costs_rate
    effective_down_payment = max(mort.down_payment - closing_costs, 0)
    loan_amount = mort.init_home_value - effective_down_payment
    monthly_payment = get_monthly_payment_amount(loan_amount, mort.interest_rate)

    # update yearly
    # home
    pmi_cost = get_monthly_pmi(mort.init_home_value, loan_amount, other.pmi_rate, mort.init_home_value)
    property_tax_cost = mort.init_home_value * mort.property_tax_rate / 12
    insurance_cost = mort.init_home_value * other.insurance_rate / 12
    hoa_costs = other.init_hoa_fees
    maintenance_costs = other.init_monthly_maintenance
    # rent / stock
    rent = rent_stock.init_rent
    portfolio_value = mort.down_payment

    # update monthly
    loan_balance = loan_amount
    home_value = mort.init_home_value
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
        month_data["interest"] = loan_balance * mort.interest_rate / 12
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
        portfolio_value = add_growth(portfolio_value, rent_stock.stock_market_growth_rate, 1, contribution)
        month_data["portfolio_value"] = portfolio_value

        # update loan balance
        loan_balance -= month_data["principal"]
        month_data["loan_balance"] = loan_balance

        # update home value
        home_value = add_growth(home_value, mort.yearly_home_value_growth, months=1)
        month_data["home_value"] = home_value

        # update monthly maintenance costs
        maintenance_costs = add_growth(maintenance_costs, other.inflation_rate, months=1)

        # update if pmi is required but dont update value unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, other.pmi_rate, mort.init_home_value)
        pmi_required = true_pmi > 0


        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_cost = home_value * mort.property_tax_rate / 12
            insurance_cost = home_value * other.insurance_rate / 12
            hoa_costs = add_growth(hoa_costs, other.inflation_rate, 12)
            pmi_cost = true_pmi
            rent = add_growth(rent, rent_stock.yearly_rent_increase, 12)

        data.append(month_data)

    return pd.DataFrame(data)


COST_COLS = ["interest", "principal", "pmi", "insurance", "property_tax", "hoa", "maintenance"]


def get_sim_monthly_df(monthly_df):
    """Append additional columns to the data frame. Get yearly dataframe summary."""

    monthly_df = monthly_df.set_index("index")

    # add total and misc columns
    monthly_df["total"] = monthly_df[
        COST_COLS
    ].sum(axis=1)
    monthly_df["misc"] = monthly_df[
        ["pmi", "insurance", "property_tax", "hoa", "maintenance"]
    ].sum(axis=1)
    return monthly_df


def get_sim_yearly_df(monthly_df):
    # sum and mean for each year
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
    return yearly_df


def add_cip(df, mort, other, sell, rent):
    """
    Your money: equity - (closing costs, interest, misc, realtor fees)
    """

    # having to calculate twice. Organize that more.
    closing_costs = mort.init_home_value * other.closing_costs_rate

    df["equity"] = df["home_value_max"] - df["loan_balance_max"]
    df["cip_homeownership"] = \
        (df["equity"] * (1-sell.realtor_rate-sell.sell_closing_costs_rate)) \
            - closing_costs - df["cum_interest_sum"] - df["cum_misc_sum"] - sell.additional_selling_costs
    
    df["cip_renting"] = df["portfolio_max"] * (1-rent.stock_tax_rate) - df["cum_rent_sum"]


def format_df_row_values(df, row_num, cols):
    """Take colums from row of dataframe and format for pie chart.
    
    Output is df with column:
        name: name of cost
        value: value of cost
        formatted_value: money formatted value of cost
    """
    row = df.loc[row_num:row_num, cols].T.reset_index().rename(columns={"index": "name", 0: "value"})
    row["formatted_value"] = row["value"].apply(lambda x: format_currency(x))
    row["name"] = row["name"].apply(lambda x: x.replace("_", " ").title())
    row = row[row["value"] > 0]
    row = row.sort_values(by=["value"], ascending=False)
    return row


def disaply_pie_chart(df):
    """df must have columns: name, value, formatted_value"""
    fig = px.pie(first_year_df, values='value', names='name', hole=0.7)
    fig.update_layout(height=600, showlegend=False)
    fig.update_traces(textposition='outside', text=first_year_df["formatted_value"], textinfo='label+text')
    fig_display(fig)


def display_stacked_bar_chart(df, cols, names, title):
    """df must have columns: name, value, formatted_value"""
    fig = go.Figure()
    
    for col, name in zip(cols, names):
        fig.add_trace(go.Bar(x=df.index, y=df[col], name=name))

    fig.update_layout(title=title,
                      xaxis=get_xaxis(CURRENT_YEAR),
                      yaxis=get_yaxis(),
                      barmode='stack',
                      height=700)
    fig_display(fig)


def display_line_chart(df, cols, names, title):
    """df must have columns: name, value, formatted_value"""
    fig = go.Figure()
    
    for col, name in zip(cols, names):
        fig.add_trace(go.Scatter(x=df.index, y=df[col], mode='lines', name=name))

    fig.update_layout(title=title,
                      xaxis=get_xaxis(CURRENT_YEAR),
                      yaxis=get_yaxis(),
                      barmode='stack',
                      height=700)
    fig_display(fig)


def calculate_summary(mort, other, sell, rent):
    # add table that shows summary of the mortgage stuff
    summary_values = {
        "home_price": mort.init_home_value,
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


st.set_page_config(layout="wide")
st.title("Mortgage Simulator")

if SHOW_TEXT:
    get_intro()

# get dataframes
housing_df = load_housing_data()
region_options = get_region_options(housing_df)
mortgage_inputs = get_mortgage_inputs(region_options, housing_df)
show_other_factors = st.checkbox("Show Other Costs")
other_factors_inputs = get_other_factors_inputs(show_other_factors)
sell_inputs = get_home_selling_costs_inputs()
rent_inputs = get_rent_stock_inputs()

sim_df = run_simluation(mortgage_inputs, other_factors_inputs, sell_inputs, rent_inputs)
monthly_df = get_sim_monthly_df(sim_df)
yearly_df = get_sim_yearly_df(monthly_df)
add_cip(yearly_df, mortgage_inputs, other_factors_inputs, sell_inputs, rent_inputs)
mean_first_year_cost_cols = [f"{colname}_mean" for colname in COST_COLS]
first_year_df = format_df_row_values(yearly_df, 0, mean_first_year_cost_cols)


# display dataframes for debug
#st.write(monthly_df)
#st.write(yearly_df)
#st.write(first_year_df)


if SHOW_TEXT:
    get_monthly_intro()


# monthly payment pie chart
disaply_pie_chart(first_year_df)

calculate_summary(mortgage_inputs, other_factors_inputs, sell_inputs, rent_inputs)

# Monthly

display_stacked_bar_chart(
    yearly_df, 
    cols=[f"{x}_mean" for x in COST_COLS], 
    names=COST_COLS,
    title="Monthly Costs"
)

# Cumulative

if SHOW_TEXT:
    get_cumulative_intro()


# cash in pocket
# equity - money lost (closing costs, interest, misc, realtor fees, taxes?)
# vs
# portfolio value - rent and taxes paid
display_line_chart(
    yearly_df, 
    cols=["cip_homeownership", "cip_renting"], 
    names=["cip_homeownership", "cip_renting"],
    title="Equity - Money Lost"
)