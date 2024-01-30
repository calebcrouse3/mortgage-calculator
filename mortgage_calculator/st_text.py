from PIL import Image
import streamlit as st
import numpy as np 

def get_intro():
    st.markdown("""
    ### Introduction to Using the Mortgage Simulator

    Welcome to the Mortgage Simulator! This interactive tool is designed to help you navigate the financial landscape of home ownership. Whether you're a first-time homebuyer, a current homeowner considering refinancing, or simply exploring the cost-benefit analysis of owning versus renting, this simulator offers valuable insights into the complexities of mortgages and real estate investments.
    """)

def get_monthly_intro():
    with st.expander("Description of this tab", expanded=True):
        st.write("""
        This section displays a breakdown of the monthly costs you can expect in your first year owning the home. This can help provide insight
        into how much house you can afford and some of the extra costs not captured by your mortgage payment to your lender.
        """)

def get_monthly_over_time_intro():
    with st.expander("Description of this tab", expanded=True):
        st.markdown("""
        This chart shows your average monthly costs over the course of 30 years. It can provide a window into 
        how the costs of home ownership change over time. Factors like homeowners insurance, maintenance and property taxes will
        increase over time as inflation effects prices and the value of your home changes. The total principle and interest paid each month
        will remain the same, however, as your pay off the principle on your loan, the amount of interest you pay will decrease. This is called
        amortization.
        """)

def get_home_value_intro():
    with st.expander("Description of this tab", expanded=True):
        st.markdown("""
        Your home will increase in value over time. Your equity, or the amount of ownership you have in your home, will 
        increase with your payments toward the principle and the increase in value of your home. This chart additionally shows the 
        your equity in your home minus all the costs that didnt go towards equity like PMI, interest, taxes, insurance, and maintenance.
        This gives you a sense for how much net cash stays in your pocket throughout the life of your mortgage.
        """)

def get_rental_comparison_intro():
    with st.expander("Description of this tab", expanded=True):
        st.markdown("""
        This chart gives a comparison of renting versus owning. In this scenario, instead of buying a home, you would instead put all the money you had for a down payment 
        into the stock market and rent a home. If the price of your rent is less than the mortgage payment and any additional costs of ownership, any left over funds would also 
        be invested into your stock portfolio. This way, we account for the opportunity costs of spending more cash on your home. Its important to factor in as well that
        the price of renting will also increase over time. This chart is helpful to compare the tradeoffs between renting and owning across different time frames.
        """)