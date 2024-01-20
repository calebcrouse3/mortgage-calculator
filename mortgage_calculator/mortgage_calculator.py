import streamlit as st
import numpy as np
import plotly.graph_objs as go
import pandas as pd
from utils import format_currency, fig_update, fig_display
from utils_finance import *
from st_text import get_intro, get_monthly_intro, get_cumulative_intro 

SHOW_TEXT = False
MONTHS = np.arange(0, 361, 1)

st.set_page_config(layout="wide")
st.title("Mortgage Simulator")

if SHOW_TEXT:
    get_intro()

with st.sidebar:
    st.title("Mortgage")
    init_home_value = st.number_input("Home Price ($)", min_value=0, max_value=1000000, value=300000, step=1000)
    down_payment = st.number_input("Down Payment ($)", min_value=0, value=50000, step=1000)
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
    closing_costs_rate = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    st.title("Other Home Costs")
    property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=3.0, value=1.0, step=0.1)
    insurance_rate = st.number_input("Homeowners Insurance Rate (%)", min_value=0.0, max_value=3.0, value=0.35, step=0.1)
    init_hoa_fees = st.number_input("HOA Fees ($)", min_value=0, max_value=10000, value=0, step=10)
    init_monthly_maintenance = st.number_input("Monthly Maintenance ($)", min_value=0, max_value=10000, value=100, step=10)
    st.title("Home Value Growth")
    yearly_home_value_growth = st.number_input("Yearly Home Value Growth (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)

# set once
closing_costs = init_home_value * closing_costs_rate / 100
effective_down_payment = max(down_payment - closing_costs, 0)
loan_amount = init_home_value - effective_down_payment
monthly_payment = get_monthly_payment_amount(loan_amount, interest_rate)

# update yearly
pmi_cost = get_monthly_pmi(init_home_value, loan_amount, pmi_rate, init_home_value)
property_tax_cost = get_monthly_property_tax(init_home_value, property_tax_rate)
insurance_cost = get_monthly_insurance_cost(init_home_value, insurance_rate)
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
    month_data["interest"] = get_monthly_interest_payment(loan_balance, interest_rate)
    month_data["principal"] = get_monthly_principal_payment(monthly_payment, month_data["interest"])
    month_data["property_tax"] = property_tax_cost
    month_data["insurance"] = insurance_cost
    month_data["hoa"] = hoa_costs
    month_data["maintenance"] = maintenance_costs
    if pmi_required:
        month_data["pmi"] = pmi_cost

    month_data["total"] = sum([month_data[key] for key in month_data.keys() if not key in ["index", "year", "month"]])

    # end of month, update values

    # update loan balance
    loan_balance -= month_data["principal"]
    month_data["loan_balance"] = loan_balance

    # update home value
    home_value = get_asset_monthly_growth(home_value, yearly_home_value_growth / 100)
    month_data["home_value"] = home_value

    # update yearly values at end of last month in each year
    if (month + 1) % 12 == 0 and month > 0:
        property_tax_cost = get_monthly_property_tax(home_value, property_tax_rate)
        insurance_cost = get_monthly_insurance_cost(home_value, insurance_rate)
        pmi_cost = get_monthly_pmi(home_value, loan_balance, pmi_rate, init_home_value)
        # TODO add inflation to HOA and maintenance costs
        hoa_costs = init_hoa_fees
        maintenance_costs = init_monthly_maintenance

    data.append(month_data)

df = pd.DataFrame(data)
st.write(df)

# TODO
# smooth out lines on yearly updated stuff
# get cumulative costs

if SHOW_TEXT:
    get_monthly_intro()

fig = go.Figure()
fig.add_trace(go.Scatter(x=MONTHS, y=df["total"], mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["principal"], mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["interest"], mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["pmi"], mode='lines', name='pmi'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["insurance"], mode='lines', name='Insurance'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["property_tax"], mode='lines', name='Property Tax'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["hoa"], mode='lines', name='Hoa'))
fig.add_trace(go.Scatter(x=MONTHS, y=df["maintenance"], mode='lines', name='Maintenance'))
fig_update(fig, "", MONTHS)
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


# Create cumulative plot
if SHOW_TEXT:
    get_cumulative_intro()

fig = go.Figure()
fig.add_trace(go.Scatter(x=months, y=cum_total, mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=months, y=cum_principal, mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=months, y=cum_interest, mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=months, y=cum_misc, mode='lines', name='Misc'))
fig_update(fig, "") #"Cumulative Costs")
fig_display(fig)
"""