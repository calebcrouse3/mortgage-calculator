import streamlit as st
import numpy as np
import plotly.graph_objs as go
import plotly.express as px
import pandas as pd
from math import *
from utils import format_currency, fig_update, fig_display
from utils_finance import *
from st_text import get_intro, get_monthly_intro, get_cumulative_intro 


SHOW_TEXT = False
MONTHS = np.arange(360)

st.set_page_config(layout="wide")
st.title("Mortgage Simulator")

if SHOW_TEXT:
    get_intro()

#Other than the string inputs, rates are always expressed as a decimal between 0 and 1
with st.sidebar:
    st.title("Mortgage")
    init_home_value = st.number_input("Home Price ($)", min_value=0, max_value=1000000, value=300000, step=1000)
    down_payment = st.number_input("Down Payment ($)", min_value=0, value=50000, step=1000)
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=10.0, value=7.0, step=0.1) / 100
    closing_costs_rate = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1) / 100
    pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1) / 100
    st.title("Other Home Costs")
    property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=3.0, value=1.0, step=0.1) / 100
    insurance_rate = st.number_input("Homeowners Insurance Rate (%)", min_value=0.0, max_value=3.0, value=0.35, step=0.1) / 100
    init_hoa_fees = st.number_input("HOA Fees ($)", min_value=0, max_value=10000, value=100, step=10)
    init_monthly_maintenance = st.number_input("Monthly Maintenance ($)", min_value=0, max_value=10000, value=50, step=10)
    st.title("Home Value Growth")
    yearly_home_value_growth = st.number_input("Yearly Home Value Growth (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1) / 100
    st.title("Home Value Growth")
    inflation_rate = st.number_input("Inflation Rate (%)", min_value=0.01, max_value=10.0, value=3.0, step=0.1) / 100

# set once
closing_costs = init_home_value * closing_costs_rate
effective_down_payment = max(down_payment - closing_costs, 0)
loan_amount = init_home_value - effective_down_payment
monthly_payment = get_monthly_payment_amount(loan_amount, interest_rate)

# update yearly
pmi_cost = get_monthly_pmi(init_home_value, loan_amount, pmi_rate, init_home_value)
property_tax_cost = init_home_value * property_tax_rate / 12
insurance_cost = init_home_value * insurance_rate / 12
hoa_costs = init_hoa_fees
maintenance_costs = init_monthly_maintenance

# update monthly
loan_balance = loan_amount
home_value = init_home_value
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
    month_data["interest"] = loan_balance * interest_rate / 12
    month_data["principal"] = monthly_payment - month_data["interest"]
    month_data["property_tax"] = property_tax_cost
    month_data["insurance"] = insurance_cost
    month_data["hoa"] = hoa_costs
    month_data["maintenance"] = maintenance_costs
    if pmi_required:
        month_data["pmi"] = pmi_cost

    # end of month, update values

    # update loan balance
    loan_balance -= month_data["principal"]
    month_data["loan_balance"] = loan_balance

    # update home value
    home_value = add_growth(home_value, yearly_home_value_growth, months=1)
    month_data["home_value"] = home_value

    # update monthly maintenance costs
    maintenance_costs = add_growth(maintenance_costs, inflation_rate, months=1)

    # update yearly values at end of last month in each year
    if (month + 1) % 12 == 0 and month > 0:
        property_tax_cost = home_value * property_tax_rate / 12
        insurance_cost = home_value * insurance_rate / 12
        pmi_cost = get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value)
        hoa_costs = add_growth(hoa_costs, inflation_rate, 12)

    data.append(month_data)


# commonly used column sets
COST_COLS = ["interest", "principal", "pmi", "insurance", "property_tax", "hoa", "maintenance"]
MISC_COLS = list(set(COST_COLS) - set(["interest", "principal"]))
COLS = COST_COLS + ["total", "misc"]


def get_sim_monthly_df(data):
    """Append additional columns to the data frame. Get yearly dataframe summary."""

    monthly_df = pd.DataFrame(data)
    monthly_df = monthly_df.set_index("index")
    monthly_df["total"] = monthly_df[COST_COLS].sum(axis=1)
    monthly_df["misc"] = monthly_df[MISC_COLS].sum(axis=1)
    return monthly_df


def get_sim_yearly_df(monthly_df):
    # sum and mean for each year
    yearly_df = monthly_df.groupby("year")[COLS].agg(["sum", "mean"])
    yearly_df.columns = [f"{colname}_{agg}" for colname, agg in yearly_df.columns]

    # cumulative cols for principal, interest, total, misc
    cumulative_df = yearly_df[["total_sum", "interest_sum", "principal_sum", "misc_sum"]].cumsum()
    cumulative_df.columns = [f"cum_{colname}" for colname in cumulative_df.columns]

    yearly_df = pd.concat([yearly_df, cumulative_df], axis=1)
    return yearly_df


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


# get dataframes
monthly_df = get_sim_monthly_df(data)
yearly_df = get_sim_yearly_df(monthly_df)
mean_first_year_cost_cols = [f"{colname}_mean" for colname in COST_COLS]
first_year_df = format_df_row_values(yearly_df, 0, mean_first_year_cost_cols)

# display dataframes for debug
st.write(monthly_df)
st.write(yearly_df)
st.write(first_year_df)

# monthly payment pie chart
disaply_pie_chart(first_year_df)


if SHOW_TEXT:
    get_monthly_intro()

fig = go.Figure()
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["total_mean"], mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["principal_mean"], mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["interest_mean"], mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["misc_mean"], mode='lines', name='Misc'))

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Dollars",
    height=700
)
fig_display(fig)


if SHOW_TEXT:
    get_cumulative_intro()

fig = go.Figure()
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["cum_total_sum"], mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["cum_principal_sum"], mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["cum_interest_sum"], mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=yearly_df.index, y=yearly_df["cum_misc_sum"], mode='lines', name='misc'))

fig.update_layout(
    xaxis_title="Year",
    yaxis_title="Dollars",
    height=700
)
fig_display(fig)


hi = """
def calculate_summary():
    # add table that shows summary of the mortgage stuff
    summary_values = {
        "home_price": init_home_value,
        "effective_down_payment": effective_down_payment,
        "closing_costs": closing_costs,
        "total_loan_amount": loan_amount,
        "total_interest_paid": sum(monthpay_interest),
        "total_pmi_paid": sum(monthpay_pmi),
        "number_of_pmi_payments": len([x for x in monthpay_pmi if x > 0]),
        "total_misc_paid": sum(monthpay_misc),
    }

    # format keys and values as strings
    summary_values = {key.title().replace("_", " "): format_currency(value) for key, value in summary_values.items()}

    # Find the length of the longest key
    max_key_length = max(len(key) for key in summary_values.keys())
    max_value_length = max(len(value) for value in summary_values.values())

    # Pad each key to have the same length
    padded_dict = {key.ljust(max_key_length): value.rjust(max_value_length) for key, value in summary_values.items()}

    st.write(padded_dict)
"""
