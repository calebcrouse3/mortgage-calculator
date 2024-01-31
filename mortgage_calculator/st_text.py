from PIL import Image
import streamlit as st
import numpy as np 

def get_intro():
    with st.expander("Intro", expanded=True):
        st.markdown("""
        Welcome to the uncompromising mortgage calculator. This tool leaves no stone unturned in helping you make the most informed decision about your home purchase.
        If you are new to real estate, spending time with this calculator is the fastest way to learn about the costs of buying a home.
        Say goodbye to jumping between calculators to get the full picture. Unlike other calculators, this tools provides a comprehensive view of the costs of home owndership. 
        The other guys leave out important considerations
        like home value appreciation, inflation, increasing rental prices, and regional specifics like property taxes and insurance. We provide various views of all the 
        associated costs of home ownership to help you make the most informed decision. This tool is specifically designed for anyone looking to buy a home, considering 
        whether or not to continue renting, or who is interested in making extra income on their property by renting out a portion of their home (House Hacking).
                    
        To get started, head over to the sidebar and selected the region of the home you are interested in, which will fill in related fields to that region. Then fill out the minimum 
        required fields in the sidebar and click the calculate button. Other fields can be modified by expanding the boxes in the sidebar.
        Weve tried to provide as many sensible default options as possible. All inputs have a tooltip to help you explain what the number youre adjusting is and 
        how it will effect your mortgage. Additionally each tab has an in depth description of what the chart is showing and what significance it has to you and
        your decision making process.
                    
        Tips:
        - Charts are interactive. Click and drag to zoom in on a specific area of the chart. Double click to zoom out. Click on the legend to hide or show different lines.
        - If you are interested in house hacking, try entering in some values in the side bar for rental income to see how it will affect your total monthly costs.
        - The sidebar is collapsible. Click the x in the corner for more space to view the charts.
        - Boxes like this intro text can be collapse to declutter the page. Click the arrow in the top right to collapse.
                    
        Happy house hunting!

        """)

def get_monthly_intro():
    with st.expander("Description", expanded=True):
        st.write("""
        This section displays a breakdown of the :red[average monthly costs you can expect in your first year owning the home]. This can help provide insight
        into how much house you can afford and some of the extra costs not captured by your mortgage payment to your lender. If youre interest in house hacking,
        try entering in some values in the side bar for rental income to see how it will affect your total monthly costs.
        """)

def get_monthly_over_time_intro():
    with st.expander("Description", expanded=True):
        st.markdown("""
        This chart shows your :red[average monthly costs over the course of 30 years]. Each bar shows the breakdown of monthly 
        costs for that year. It can provide a window into 
        how the costs of home ownership change over time. Factors like homeowners insurance, maintenance and property taxes will
        increase over time as inflation effects prices and the value of your home changes. The total principle and interest paid each month
        will remain the same. But noticed as your pay off the principle on your loan over time, the amount of interest you pay will decrease.
        Try entering numbers in the rental income section in the sidebar to see how your rental income will offset your monthly costs.
        """)

def get_home_value_intro():
    with st.expander("Description", expanded=True):
        st.markdown("""
            This chart shows the :red[total value of your home over time] as well as the :red[net profit after costs] of owning your home. 
            Your home will increase in value over time. Your equity, or the amount of ownership you have in your home, will 
            increase with your payments toward the principle and the increase in value of your home. You can think of equity as what would go to you 
            (and not the bank) if you chose to sell your home in any particular year. But its also important to consider
            the costs of owning your home and whether this offsets the increase in equity. This includes PMI, interest, taxes, insurance, and maintenance. 
            Renting out a portion of your home (House Hacking)
            can offset, or completely cover the costs of owning the home, and might even put extra cash in your pocket.
            
            This chart breaks down the numbers in four flavors:
            - :red[Home Value]: The total value of your home over time
            - :red[Equity]: The amount of ownership you have in your home
            - :red[Profit]: The amount of cash that stays in your pocket after all costs are accounted for
            - :red[Profit with Rental Income]: The amount of cash that stays in your pocket after all costs are accounted for, including rental income. 
                    Make sure you fill out the rental income numbers in the side bar.
        """)

def get_rental_comparison_intro(rent_percent_increase):
    with st.expander("Description", expanded=True):
        st.markdown(f"""
        This chart gives a :red[comparison of renting versus owning]. You might be wondering if renting is worth it for you and how much money you might be able to 
        save by owning a home. In this scenario, instead of buying a home, you would instead put all the money you had for a down payment 
        into the :red[stock market with 8% annual returns] and rent a home. If your rent is less than home ownership, any left over funds would also 
        be invested into your stock portfolio in that month. This way, we account for the opportunity costs of spending more cash on your home. 
        Like the value of your home, rent also incrases overtime. The current setting of :red[yearly rent increase is {round(rent_percent_increase, 2)}%] but you can adjust 
        it in the rental income tab in the sidebar. We choose to rent and own for different reasons. We might rent because
        were not sure where we want to live, or we might rent to try and be more thrifty. This makes it hard to select the amount of rental income to compare to 
        your home ownership costs. Thats why, in the future, wed like to add a feature to give you a compable rental costs based on the price of your home and the 
        region youve selected. For now, just take a guess!
        """)