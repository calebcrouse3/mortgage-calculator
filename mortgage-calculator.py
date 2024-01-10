import streamlit as st
import numpy as np
import plotly.graph_objs as go

# Function to calculate monthly mortgage payment and additional costs
def calculate_mortgage_and_costs(principal, interest_rate, years, home_price, effective_down_payment, pmi_rate, property_tax_rate, insurance_rate):
    monthly_rate = interest_rate / 12 / 100
    n_payments = years * 12
    mortgage_payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)

    pmi = 0
    # Calculate PMI if the effective down payment is less than 20% of the home price
    if effective_down_payment < 0.2 * home_price:
        pmi = (principal * pmi_rate / 100) / 12
        mortgage_payment += pmi

    # Calculate and add property tax
    property_tax = (home_price * property_tax_rate / 100) / 12
    mortgage_payment += property_tax

    # Calculate and add homeowners insurance
    insurance = (home_price * insurance_rate / 100) / 12
    mortgage_payment += insurance

    return round(mortgage_payment), round(pmi), round(property_tax), round(insurance)  # Rounded to whole dollars

# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas

# Streamlit app
st.title("30-Year Fixed Rate Mortgage Calculator with PMI, Property Tax, and Insurance")

# Numerical input for down payment in dollars
down_payment = st.number_input("Down Payment ($)", min_value=0, value=50000, step=1000)

# Numerical input for closing costs as a percentage
closing_costs_percentage = st.number_input("Closing Costs (%)", min_value=0.0, max_value=10.0, value=3.0, step=0.1)

# Numerical input for PMI rate
pmi_rate = st.number_input("PMI Rate (%)", min_value=0.0, max_value=5.0, value=0.5, step=0.1)

# Numerical input for property tax rate
property_tax_rate = st.number_input("Property Tax Rate (%)", min_value=0.0, max_value=5.0, value=1.0, step=0.1)

# Numerical input for homeowners insurance rate
insurance_rate = st.number_input("Homeowners Insurance Rate (%)", min_value=0.0, max_value=3.0, value=0.35, step=0.1)

# Numerical input for monthly disposable income
monthly_income = st.number_input("Monthly Disposable Income ($)", min_value=0, value=8000, step=100)

# Default interest rates
default_rates = [5.0, 7.0]

# Text input for interest rates
interest_rates_input = st.text_input("Interest Rates (%)", ', '.join(map(str, default_rates)))
try:
    interest_rates = [float(rate.strip()) for rate in interest_rates_input.split(',')]
except ValueError:
    st.error("Please enter valid interest rates, separated by commas.")
    interest_rates = []

# Define range for home prices with $1,000 increments
home_prices = np.arange(200000, 801000, 1000)

# Create Plotly figure
fig = go.Figure()

for rate in interest_rates:
    monthly_payments = []
    hover_texts = []
    for price in home_prices:
        closing_costs = price * closing_costs_percentage / 100
        effective_down_payment = max(down_payment - closing_costs, 0)  # Ensure non-negative
        loan_amount = price - effective_down_payment
        total_payment, pmi, property_tax, insurance = calculate_mortgage_and_costs(loan_amount, rate, 30, price, effective_down_payment, pmi_rate, property_tax_rate, insurance_rate)
        monthly_payments.append(total_payment)
        payment_percentage_of_income = (total_payment / monthly_income) * 100 if monthly_income else 0
        hover_text = (f"Home Price: ${price:,.0f}<br>"
                      f"Effective Down Payment: {format_currency(effective_down_payment)}<br>"
                      f"Monthly Payment: {format_currency(total_payment)}<br>"
                      f"PMI Cost: {format_currency(pmi)}<br>"
                      f"Property Tax: {format_currency(property_tax)}<br>"
                      f"Insurance: {format_currency(insurance)}<br>"
                      f"Mortgage as % of Income: {payment_percentage_of_income:.2f}%")
        hover_texts.append(hover_text)

    fig.add_trace(go.Scatter(x=home_prices, y=monthly_payments, mode='lines+markers', name=f'{rate}%', hoverinfo='text', text=hover_texts))

fig.update_layout(
    title='Monthly Mortgage Payments by Home Price, Interest Rate, PMI, Property Tax, and Insurance',
    xaxis_title='Home Price ($)',
    yaxis_title='Monthly Mortgage Payment ($)',
    xaxis=dict(
        tickmode='array',
        tickvals=list(range(200000, 900000, 100000)),
        ticktext=[f'{int(val/1000)}K' for val in range(200000, 900000, 100000)]
    ),
    yaxis=dict(
        range=[0, 4000]
    ),
    showlegend=False,
    modebar_remove=['zoom', 'pan', 'select', 'zoomIn', 'zoomOut', 'autoScale', 'resetScale']
)

# Display the figure
st.plotly_chart(fig, use_container_width=True)
