from PIL import Image
import streamlit as st
import numpy as np 

def get_intro():
    st.markdown("""
    ### Introduction to Using the Mortgage Simulator

    Welcome to the Mortgage Simulator! This interactive tool is designed to help you navigate the financial landscape of home ownership. Whether you're a first-time homebuyer, a current homeowner considering refinancing, or simply exploring the cost-benefit analysis of owning versus renting, this simulator offers valuable insights into the complexities of mortgages and real estate investments.
    """)
        
def more_intro():
    st.markdown("""
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


def get_monthly_intro():
    st.markdown("""
    #### Monthly Costs Breakdown
    This section displays a detailed breakdown of your monthly costs when owning a home. It includes the principal and interest payments, PMI (if applicable), property tax, and homeowners insurance. Understanding these costs is crucial in determining the monthly affordability of a home and how your payments are allocated over time.
    """)


def get_cumulative_intro():
    st.markdown("""
    #### Cumulative Costs Over Time
    Here, you can see the cumulative costs of owning a home versus renting over time. This visualization helps you to understand the long-term financial commitment of a mortgage and compare it with the cumulative cost of renting. It's a vital tool for assessing the total financial impact of your housing decisions over the years.
    """)