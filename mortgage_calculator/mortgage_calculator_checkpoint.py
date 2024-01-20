import streamlit as st
import numpy as np
import plotly.graph_objs as go
from PIL import Image
import pandas as pd

SHOW_MARKDOWN = False


# TODO how does compounding work for home value growth, rental price increase, stock market value growth.
# Need to investigate how to model this correctly. Compounding year/ month/ day?
# could calculate the growth based on the year increase, time passed, and inital price.

# need to update some things on yearly basis like rent, tax, and insurance
# assumption - you start with your downpayment and make no other money. Have no salary

# add part for additional payments to principle early on. Which would also be added to stock market
# what taxes and fees need to be added to the selling of a home to mirror the taxes applied to stock market profits

# can rent out you house, poket the rent based on current price, and buy another house???

st.set_page_config(layout="wide")




st.title("Mortgage Simulator")

if SHOW_MARKDOWN:
    st.markdown("""
    ### Introduction to Using the Mortgage Simulator

    Welcome to the Mortgage Simulator! This interactive tool is designed to help you navigate the financial landscape of home ownership. Whether you're a first-time homebuyer, a current homeowner considering refinancing, or simply exploring the cost-benefit analysis of owning versus renting, this simulator offers valuable insights into the complexities of mortgages and real estate investments.

    To get started, you'll enter various parameters that affect the cost of buying and owning a home. These include:

    1. **Home Price ($)**: The purchase price of the home you're considering.
    2. **Down Payment ($)**: The upfront cash payment towards the home purchase.
    3. **Interest Rate (%)**: The annual interest rate of your mortgage.
    4. **Closing Costs (%)**: Additional costs incurred during the mortgage process, typically a percentage of the home price.
    5. **PMI Rate (%)**: If your down payment is less than 20% of the home price, Private Mortgage Insurance (PMI) applies.
    6. **State Property Tax**: Select your state to apply its specific property tax rate.
    7. **Homeowners Insurance Rate (%)**: Annual insurance rate based on the home's value.

    In addition to these home-buying specifics, you can also input data related to renting and investing in the stock market. This allows you to compare the long-term financial outcomes of owning a home versus renting and investing the surplus money.

    1. **Yearly Home Value Growth (%)**: The expected annual appreciation rate of your home's value.
    2. **Current Monthly Rent ($)**: If renting, your current monthly rent payment.
    3. **Yearly Rent Increase (%)**: The expected annual increase in your rent.
    4. **Stock Return Rate (%)**: Annual rate of return if you were to invest in the stock market.
    5. **Stock Tax Rate (%)**: The tax rate applied to stock market profits.

    As you input your data, the simulator dynamically calculates and displays:

    - **Monthly Mortgage Breakdown**: See how your payment is split between principal, interest, PMI, property tax, and insurance.
    - **Cumulative Costs Over Time**: Track the total cost of owning a home versus renting over the years.
    - **Net Cash in Pocket**: This graph compares the potential financial benefits of home ownership against renting and investing in the stock market.

    By adjusting these inputs, you can explore various scenarios and understand how different factors like interest rates, home price appreciation, and stock market returns can impact your financial future. This tool is a great way to experiment with different strategies and make more informed decisions about one of life's most significant investments – your home.
    """)

    # Load the photo
    photo = np.array(Image.open("mortgage_calculator/bad_house.jpg"))

    # Display the photo
    st.image(photo, caption="Recently Listed")


def calculate_pmi(home_value, principal, pmi_rate, init_home_value):
    # PMI gets cancelled when equity >= 20% of the home value, or loan balance <= 80% of the init home value
    equity = home_value - principal
    if equity < 0.2 * home_value or principal > 0.8 * init_home_value:
        return (principal * pmi_rate / 100) / 12
    else:
        return 0
    

def total_value(initial_value, growth_rate, time):
    """
    initial_value: The initial value of the asset
    growth_rate: The yearly growth rate of the asset
    time: The time in years
    """
    return initial_value * (1 + growth_rate / 100)**time


def calculate_portfolio_value(initial_investment, yearly_return, months, monthly_contribution):
    """
    Calculate the value of a stock portfolio over a period of time.

    Parameters:
    initial_investment (float): The initial amount of money invested.
    yearly_return (float): The yearly rate of return as a decimal (e.g., 0.07 for 7%).
    months (int): The number of months the money is invested.
    monthly_contribution (float): The amount of money added to the investment every month.

    Returns:
    float: The total value of the stock portfolio after the specified period.
    """
    monthly_return = yearly_return / 12
    total_value = initial_investment

    for month in range(1, months + 1):
        total_value = total_value * (1 + monthly_return) + monthly_contribution

    return total_value


def calculate_mortgage_and_costs(loan_amount, principal, interest_rate, home_value, property_tax_rate, insurance_rate, years=30):
    """
    Desribe Parameters:
    loan_amount: The amount of money borrowed from the bank
    principal: The remaining amount of money owed to the bank
    interest_rate: The interest rate on the loan
    init_home_value: The initial value of the home
    home_value: The current value of the home
    pmi_rate: The PMI rate
    property_tax_rate: The property tax rate
    insurance_rate: The homeowners insurance rate
    years: The number of years of the loan

    PMI can be cancelled when you reach 20% equity in your home. Equity is the difference between 
    the value of your home and the amount you still owe on your home loan. You can calculate your.
    I.e., any increase in home value or decrease in loan amount will increase your equity.
    The 20 percent for PMI calculation is equity / initial home value. There might be some instances
    where the bank assess equity / current home value instead. This is something to look into.
    """
    monthly_rate = interest_rate / 12 / 100
    n_payments = years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)

    # calculate principal interest rate break down
    interest_payment = principal * monthly_rate
    principal_payment = monthly_payment - interest_payment

    # Calculate and add property tax
    property_tax = (home_value * property_tax_rate / 100) / 12

    # Calculate and add homeowners insurance
    insurance = (home_value * insurance_rate / 100) / 12

    # TODO dont round these values until the end
    return round(principal_payment), round(interest_payment), round(property_tax), round(insurance)  # Rounded to whole dollars


state_property_tax_rates = {
    "Alabama": 0.42,
    "Alaska": 1.19,
    "Arizona": 0.68,
    "Arkansas": 0.62,
    "California": 0.77,
    "Colorado": 0.55,
    "Connecticut": 1.91,
    "Delaware": 0.56,
    "District of Columbia": 0.56,
    "Florida": 0.98,
    "Georgia": 0.91,
    "Massachusetts": 1.21,
}

state_property_tax_strings = [f"{state} ({rate}%)" for state, rate in state_property_tax_rates.items()]

with st.sidebar:
    st.title("Mortgage")
    init_home_value = st.number_input("Home Price ($)", min_value=0, max_value=1000000, value=300000, step=1000)
    down_payment = st.number_input("Down Payment ($)", min_value=0, value=50000, step=1000)
    interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
    closing_costs_rate = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
    st.title("Other Home Costs")
    state_selection = st.selectbox("State Property Tax", state_property_tax_strings)
    insurance_rate = st.number_input("Homeowners Insurance Rate (%)", min_value=0.0, max_value=3.0, value=0.35, step=0.1)
    st.title("Home Value Growth")
    yearly_home_value_growth = st.number_input("Yearly Home Value Growth (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    st.title("Rent")
    init_rent = st.number_input("Current Monthly Rent ($)", min_value=0, max_value=10000, value=1300, step=10)
    yearly_rent_increase = st.number_input("Yearly Rent Increase (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
    st.title("Stock")
    stock_market_growth_rate = st.number_input("Stock Return Rate (%)", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
    stock_tax_rate = st.number_input("Stock Tax Rate (%)", min_value=0.0, max_value=100.0, value=15.0, step=0.1)

months = np.arange(0, 361, 1)

# set once
property_tax_rate = state_property_tax_rates[state_selection.split(" (")[0]]
closing_costs = init_home_value * closing_costs_rate / 100
effective_down_payment = max(down_payment - closing_costs, 0)
loan_amount = init_home_value - effective_down_payment
# init_home_value
# init_rent
init_stock_value = down_payment - init_rent

# update each year
yearly_pmi = calculate_pmi(init_home_value, loan_amount, pmi_rate, init_home_value)

# udpate each month
principal = loan_amount
home_value = init_home_value
rent = init_rent
stock_value = init_stock_value

# hold monthly values
monthpay_principal = []
monthpay_interest = []
monthpay_pmi = []
monthpay_tax = []
monthpay_insurance = []
monthpay_misc = []
monthpay_total = []
monthpay_rent = []

# hold cumulative values
cum_principal = []
cum_interest = []
cum_misc = []
cum_total = []
cum_rent = []

# hold cum delta values
cumdelt_home_ownership = []
cumdelt_renting = []

# other
stock_portfolio_value = []


for month in months:

    pmi = yearly_pmi
    current_pmi = calculate_pmi(home_value, principal, pmi_rate, init_home_value)

    if month % 12 == 0:
        yearly_pmi = calculate_pmi(home_value, principal, pmi_rate, init_home_value)
        pmi = yearly_pmi

    if current_pmi == 0:
        pmi = 0

    # need to adjust home price as months go on
    principal_payment, interest_payment, property_tax, insurance = calculate_mortgage_and_costs(
        loan_amount, principal, interest_rate, home_value, property_tax_rate, insurance_rate
    )

    misc_payments = pmi + property_tax + insurance
    total_monthly = principal_payment + interest_payment + misc_payments

    # append current payments
    monthpay_principal.append(principal_payment)
    monthpay_interest.append(interest_payment)
    monthpay_pmi.append(pmi)
    monthpay_tax.append(property_tax)
    monthpay_insurance.append(insurance)
    monthpay_misc.append(misc_payments)
    monthpay_total.append(total_monthly)
    monthpay_rent.append(rent)

    # append cumulative payments
    if month == 0:
        init_misc_payment = misc_payments + closing_costs
        init_principal_payment = principal_payment + effective_down_payment
        init_total_payment = init_principal_payment + init_misc_payment + interest_payment
        cum_principal.append(init_principal_payment)
        cum_interest.append(interest_payment)
        cum_misc.append(init_misc_payment)
        cum_total.append(init_total_payment)
        cum_rent.append(rent)
    else:
        cum_principal.append(cum_principal[-1] + principal_payment)
        cum_interest.append(cum_interest[-1] + interest_payment)
        cum_misc.append(cum_misc[-1] + misc_payments)
        cum_total.append(cum_total[-1] + total_monthly)
        cum_rent.append(cum_rent[-1] + rent)


    # this portion simulates how much money you would have if you bought a home versus renting and
    # investing the difference in the stock market
    years_in_months = month / 12
    
    # collect home value growth through course of month
    new_home_value = total_value(init_home_value, yearly_home_value_growth, years_in_months)
    home_value_increase = new_home_value - home_value

    if month == 0:
        home_profit = effective_down_payment + principal_payment + home_value_increase
        home_costs = closing_costs + misc_payments + interest_payment
        home_net = home_profit - home_costs
        cumdelt_home_ownership.append(home_profit - home_costs)
    else:
        home_profit = principal_payment + home_value_increase
        home_costs = misc_payments + interest_payment
        cumdelt_home_ownership.append(cumdelt_home_ownership[-1] + home_profit - home_costs)

    if month > 0:
        left_over_money = max(total_monthly - rent, 0)
        stock_value = calculate_portfolio_value(stock_value, stock_market_growth_rate / 100.0, 1, left_over_money)
        stock_gains = stock_value - init_stock_value
        stock_after_tax = init_stock_value + (stock_gains * (1 - stock_tax_rate / 100))
        cumdelt_renting.append(stock_after_tax - sum(monthpay_rent[1:]))

    # increase rent at end of year
    if month % 12 == 0:
        rent = total_value(init_rent, yearly_rent_increase, years_in_months)

    # update variables for next month
    principal -= principal_payment
    home_value = new_home_value


# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas


# chart helpers
def fig_update(fig, title):
    year_labels = [f'{year}' for year in range(1, (len(months) // 12) + 1)]

    year_ticks = dict(
        tickmode='array',
        tickvals=[1 + 12 * i for i in range(len(year_labels))],
        ticktext=year_labels
    )

    fig.update_layout(
        title=title,
        xaxis_title="Year",
        yaxis_title="Dollars",
        xaxis=year_ticks,
        height=700
    )

    for trace in fig.data:
        trace.hovertemplate = f"{trace.name}: " + "%{y:$,.0f}<extra></extra>"

def fig_display(fig):
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})


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
    #"total_rent_paid": sum(monthpay_rent),
}

# format keys and values as strings
summary_values = {key.title().replace("_", " "): format_currency(value) for key, value in summary_values.items()}

# Find the length of the longest key
max_key_length = max(len(key) for key in summary_values.keys())
max_value_length = max(len(value) for value in summary_values.values())

# Pad each key to have the same length
padded_dict = {key.ljust(max_key_length): value.rjust(max_value_length) for key, value in summary_values.items()}

st.write(padded_dict)


# Create monthly plot
st.markdown("""
#### Monthly Costs Breakdown
This section displays a detailed breakdown of your monthly costs when owning a home. It includes the principal and interest payments, PMI (if applicable), property tax, and homeowners insurance. Understanding these costs is crucial in determining the monthly affordability of a home and how your payments are allocated over time.
""")

fig = go.Figure()
fig.add_trace(go.Scatter(x=months, y=monthpay_total, mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=months, y=monthpay_principal, mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=months, y=monthpay_interest, mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=months, y=monthpay_misc, mode='lines', name='Misc'))
fig.add_trace(go.Scatter(x=months, y=monthpay_rent, mode='lines', name='Rent'))
fig_update(fig, "")#"Monthly Costs")
fig_display(fig)


# Create cumulative plot
st.markdown("""
#### Cumulative Costs Over Time
Here, you can see the cumulative costs of owning a home versus renting over time. This visualization helps you to understand the long-term financial commitment of a mortgage and compare it with the cumulative cost of renting. It's a vital tool for assessing the total financial impact of your housing decisions over the years.
""")

fig = go.Figure()
fig.add_trace(go.Scatter(x=months, y=cum_total, mode='lines', name='Total Home'))
fig.add_trace(go.Scatter(x=months, y=cum_principal, mode='lines', name='Principal'))
fig.add_trace(go.Scatter(x=months, y=cum_interest, mode='lines', name='Interest'))
fig.add_trace(go.Scatter(x=months, y=cum_misc, mode='lines', name='Misc'))
fig.add_trace(go.Scatter(x=months, y=cum_rent, mode='lines', name='Rent'))
fig_update(fig, "") #"Cumulative Costs")
fig_display(fig)


# Create profit plot
st.markdown("""
#### Net Cash In Pocket Comparison
This graph compares the potential financial benefits of home ownership against renting and investing in the stock market. It provides a visual representation of the net cash in pocket over time, considering factors like home value growth, rent increases, and stock market returns. In this simulation, any surplus money from renting is invested in the stock market.
""")

fig = go.Figure()
fig.add_trace(go.Scatter(x=months, y=cumdelt_home_ownership, mode='lines', name='Home Ownership'))
fig.add_trace(go.Scatter(x=months, y=cumdelt_renting, mode='lines', name='Rent + Stock Portfolio'))
fig_update(fig, "") #"Net Cash In Pocket")
fig_display(fig)