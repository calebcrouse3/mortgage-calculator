import streamlit as st
import numpy as np
import plotly.graph_objs as go

# Function to calculate monthly mortgage payment
def calculate_mortgage(principal, interest_rate, years):
    monthly_rate = interest_rate / 12 / 100
    n_payments = years * 12
    mortgage_payment = principal * (monthly_rate * (1 + monthly_rate)**n_payments) / ((1 + monthly_rate)**n_payments - 1)
    return round(mortgage_payment)  # Rounded to whole dollars

# Function to format currency
def format_currency(value):
    return "${:,.0f}".format(value)  # Formats the number with a dollar sign and commas

# Streamlit app
st.title("30-Year Fixed Rate Mortgage Calculator")

# Numerical input for down payment in dollars
down_payment = st.number_input("Down Payment ($)", min_value=0, value=40000, step=1000)

# Text input for interest rates
interest_rates_input = st.text_input("Interest Rates (%)", "5.5, 7.5")
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
    monthly_payments = [calculate_mortgage(price - down_payment, rate, 30) for price in home_prices]
    hover_texts = [f"Home Price: ${price:,.0f}<br>Monthly Payment: {format_currency(payment)}" for price, payment in zip(home_prices, monthly_payments)]
    fig.add_trace(go.Scatter(x=home_prices, y=monthly_payments, mode='lines+markers', name=f'{rate}%', hoverinfo='text', text=hover_texts))

fig.update_layout(
    title='Monthly Mortgage Payments by Home Price and Interest Rate',
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
