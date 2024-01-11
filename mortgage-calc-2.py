import streamlit as st
import numpy as np
import plotly.graph_objs as go


# Function to calculate monthly mortgage payment and additional costs
def calculate_mortgage_and_costs(loan_amount, principal, interest_rate, init_home_value, home_value, pmi_rate, property_tax_rate, insurance_rate, years=30):
    monthly_rate = interest_rate / 12 / 100
    n_payments = years * 12
    monthly_payment = loan_amount * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)

    # TODO does PMI get calculated based off on the price of the home when you bought it or the current price of the home
    # Might need to include initial home price vs current home price as parameters
    # calculate PMI first since the principal depends on it
    equity = home_price - principal
    pmi = 0
    # Calculate PMI if the effective down payment is less than 20% of the home price
    if equity < 0.2 * init_home_value:
        pmi = (principal * pmi_rate / 100) / 12

    # calculate principal interest rate break down
    interest_payment = principal * monthly_rate
    principal_payment = monthly_payment - interest_payment

    # Calculate and add property tax
    property_tax = (home_value * property_tax_rate / 100) / 12

    # Calculate and add homeowners insurance
    insurance = (home_value * insurance_rate / 100) / 12

    return round(principal_payment), round(interest_payment), round(pmi), round(property_tax), round(insurance)  # Rounded to whole dollars


# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas

# Buttons
st.title("30-Year Fixed Rate Mortgage Calculator with PMI, Property Tax, and Insurance")
down_payment = st.number_input("Down Payment ($)", min_value=0, value=50000, step=1000)
closing_costs_percentage = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)
pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)
property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)
insurance_rate = st.number_input("Homeowners Insurance Rate (%)", min_value=0.0, max_value=3.0, value=0.35, step=0.1)
interest_rate = st.number_input("Interest Rate (%)", min_value=0.0, max_value=10.0, value=7.0, step=0.1)
home_price = st.number_input("Home Price ($)", min_value=0, max_value=1000000, value=300000, step=1000)


# Create Plotly figure
fig = go.Figure()

months = np.arange(0, 361, 1)

closing_costs = home_price * closing_costs_percentage / 100
effective_down_payment = max(down_payment - closing_costs, 0)  # Ensure non-negative
principal = home_price - effective_down_payment
loan_amount = principal

principal_payments = []
interest_payments = []
pmi_payments = []
property_tax_payments = []
insurance_payments = []

for month in months:
    # need to adjust home price as months go on
    principal_payment, interest_payment, pmi, property_tax, insurance = calculate_mortgage_and_costs(
        loan_amount, principal, interest_rate, home_price, home_price, pmi_rate, property_tax_rate, insurance_rate
    )
    principal_payments.append(principal_payment)
    interest_payments.append(interest_payment)
    pmi_payments.append(pmi)
    property_tax_payments.append(property_tax)
    insurance_payments.append(insurance)
    principal -= principal_payment

fig.add_trace(go.Scatter(x=months, y=principal_payments, mode='lines', name='Principal Payments'))
fig.add_trace(go.Scatter(x=months, y=interest_payments, mode='lines', name='Interest Payments'))
fig.add_trace(go.Scatter(x=months, y=pmi_payments, mode='lines', name='PMI Payments'))
fig.add_trace(go.Scatter(x=months, y=property_tax_payments, mode='lines', name='Property Tax Payments'))
fig.add_trace(go.Scatter(x=months, y=insurance_payments, mode='lines', name='Insurance Payments'))

# Update the layout of the figure
fig.update_layout(
    title="Monthly Payments",
    xaxis_title="Months",
    yaxis_title="Dollars",
    xaxis=dict(tickmode='linear', tick0=0, dtick=60),  # Show ticks for each year (12 months)
)

# Display the figure
st.plotly_chart(fig, use_container_width=True)