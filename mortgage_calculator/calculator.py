from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

from utils import *
from utils_finance import *
from session_state_interface import SessionStateInterface


st.set_page_config(layout="wide")
ss = SessionStateInterface()

HEIGHT = 700
WIDTH = 800

# e6 = million
# e5 = hundred thousand
# e4 = ten thousand
# e3 = thousand

def mortgage_inputs():
    with st.expander("Mortgage", expanded=True):
        populate_columns([
            lambda: dollar_input("Home Price", ss.home_price.key, min_value=2e4, max_value=10e6, step=2e4),
            lambda: dollar_input("Rehab", ss.rehab.key, min_value=0, max_value=5e5, step=2e3),
        ], 2)
        populate_columns([
            lambda: dollar_input("Down Payment", ss.down_payment.key, min_value=0, max_value=1e6, step=5e3),
            lambda: rate_input("Interest Rate", ss.interest_rate.key),
        ], 2)
        populate_columns([
            lambda: rate_input("Closing Costs", ss.closing_costs_rate.key),
            lambda: rate_input("PMI Rate", ss.pmi_rate.key),
        ], 2)


def expenses_inputs():
    with st.expander("Expenses", expanded=False):
        populate_columns([
            lambda: rate_input("Property Tax", ss.yr_property_tax_rate.key),
            lambda: rate_input("Insurance Rate", ss.yr_insurance_rate.key),
        ], 2)
        populate_columns([
            lambda: dollar_input("Mo. HOA Fees", ss.mo_hoa_fees.key, max_value=1e4, step=50),
            lambda: dollar_input("Mo. Utilities", ss.mo_utility.key, max_value=1e4, step=50),
        ], 2)
        populate_columns([
            lambda: rate_input("Maintenance", ss.yr_maintenance.key, 
                               help="Yearly maintenance as a percentage of home value"),     
        ], 2)


def economic_factors_inputs():
    with st.expander("Economy", expanded=False):
        populate_columns([
            lambda: rate_input("Home Appreciation", ss.yr_home_appreciation.key),
            lambda: rate_input("Inflation Rate", ss.yr_inflation_rate.key),   
        ], 2)
        populate_columns([
            lambda: rate_input("Yearly Rent Increase", ss.yr_rent_increase.key),
            lambda: rate_input("Stock Growth Rate", ss.stock_growth_rate.key),
        ], 2)


def rent_income_inputs():
    with st.expander("Rental Income", expanded=False):
        populate_columns([
            lambda: dollar_input("Mo. Rental Income", ss.mo_rent_income.key, max_value=1e5, step=50),
            lambda: dollar_input("Mo. Misc Income", ss.mo_other_income.key, max_value=1e4, step=50),
        ], 2)
        populate_columns([
            lambda: rate_input("Vacancy Rate", ss.vacancy_rate.key),
            lambda: rate_input("Management Fee", ss.management_rate.key),
        ], 2)


def selling_inputs():
    with st.expander("Selling Fees/Taxes", expanded=False):
        populate_columns([
            lambda: rate_input("Income Tax", ss.income_tax_rate.key),
            lambda: rate_input("Realtor Fee", ss.realtor_rate.key),
        ], 2)
        populate_columns([
            lambda: rate_input("Capital Gains Tax", ss.capital_gains_tax_rate.key),
        ], 2)


def reset_inputs():
    populate_columns([
        lambda: st.button("Reset Inputs", on_click=ss.clear),
        #lambda: st.button("Calculate"),
    ], 2)


def chart_disaply_inputs():
    with st.expander("Chart Options", expanded=False):
        populate_columns([
            lambda: st.number_input("X-axis Max (Years)", min_value=5, max_value=30, step=5, key=ss.xlim.key),
            lambda: st.selectbox("Chart Mode", ["Lines", "Dots"], key=ss.chart_mode.key),
        ], 2)


def rent_vs_own_inputs():
    populate_columns([
        lambda: dollar_input("Mo. Rent Payment", ss.rent_exp.key, min_value=0, max_value=1e5, step=100,
        help="This is the current monthly rent you would pay instead of buying the home in consideration."),
    ], 1)


def extra_payment_inputs():
    populate_columns([
        lambda: dollar_input("Mo. Payment Amount", ss.mo_extra_payment.key)
    ], 1)
    populate_columns([
        lambda: dollar_input("Number of Payments", ss.num_extra_payments.key)
    ], 1)


def get_monthly_sim_df(oop, loan_amount, monthly_payment, extra_payments):
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.

    Extra payments will apply extra payments to the principle of the loan and also add the extra payment
    to the extra payments portfolio.

    PMI is a little tricky to follow because it can be cancelled anytime based on the price of PMI 
    returned by the function but the price paid is updated once a year.
    pmi_true:     holds the value of PMI if it was recalculated
    pmi_exp:      holds the actual PMI paid and is updated yearly
    pmi_required: is not required if the true_pmi <= 0 and will cancel the pmi_exp

    The simulation will track additional portfolios in parallel for comparison whose value 
    do not effect the mortgage and expenses itself.
    """

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_exp = get_monthly_pmi(ss.home_price.val, loan_amount, ss.pmi_rate.val, ss.home_price.val)
    property_tax_exp = ss.home_price.val * ss.yr_property_tax_rate.val / 12
    insurance_exp = ss.home_price.val * ss.yr_insurance_rate.val / 12
    maintenance_exp = ss.home_price.val * ss.yr_maintenance.val / 12
    hoa_exp = ss.mo_hoa_fees.val
    utility_exp = ss.mo_utility.val
    rent_income = ss.mo_rent_income.val
    other_income = ss.mo_other_income.val
    management_exp = ss.management_rate.val * rent_income
    rent_exp = ss.rent_exp.val

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    loan_balance = loan_amount
    home_value = ss.home_price.val
    pmi_required = pmi_exp > 0

    # Stock portfolio comparisons
    total_expense_portfolio = oop # portfolio funded with all homeownership expenses. Captured by ROE?
    rent_comparison_portfolio = oop # portfolio funded with money saved from renting
    extra_payments_portfolio = 0 # portfolio funded with extra payments


    data = []
    for month in np.arange(12 * 30):

        ########################################################################
        #      Principle and Interest                                          #
        ########################################################################

        interest_exp = loan_balance * ss.interest_rate.val / 12
        principal_exp = monthly_payment - interest_exp
        extra_payment_exp = 0

        # extra payments are the only time we might need to adjust principle exp
        if extra_payments:
            if principal_exp >= loan_balance:
                principal_exp = loan_balance
            elif month < ss.num_extra_payments.val:
                extra_payment_exp = min(loan_balance - principal_exp, ss.mo_extra_payment.val)

        loan_balance -= principal_exp
        loan_balance -= extra_payment_exp

        ########################################################################
        #      Expenses                                                        #
        ########################################################################

        # pay pmi if required
        if not pmi_required:
            pmi_exp = 0

        op_exp = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp +
            utility_exp +
            management_exp
        )

        total_exp = op_exp + interest_exp + principal_exp + extra_payment_exp
        total_income = rent_income + other_income
        adj_total_income = total_income * (1 - ss.vacancy_rate.val)
        noi = adj_total_income - op_exp
        niaf = adj_total_income - total_exp

        # apply income tax to profits
        if niaf > 0:
            niaf *= (1 - ss.income_tax_rate.val)

        # update pmi_required, but dont update pmi cost unless its end of year
        pmi_true = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = pmi_true > 0

        ########################################################################
        #      Growth During Month                                             #
        ########################################################################

        # contribute to portfolio if money saved from renting
        if total_exp > rent_exp:
            rent_comparison_portfolio += total_exp - rent_exp

        # contribute any extra payments to portfolio
        if extra_payment_exp > 0:
            extra_payments_portfolio += extra_payment_exp

        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)
        rent_comparison_portfolio = add_growth(rent_comparison_portfolio, ss.stock_growth_rate.val, months=1)
        extra_payments_portfolio = add_growth(extra_payments_portfolio, ss.stock_growth_rate.val, months=1)

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # Costs, payments, revenue. Monthly Totals.
            "interest_exp": interest_exp,
            "principal_exp": principal_exp,
            "property_tax_exp": property_tax_exp,
            "insurance_exp": insurance_exp,
            "hoa_exp": hoa_exp,
            "maintenance_exp": maintenance_exp,
            "pmi_exp": pmi_exp,
            "utility_exp": utility_exp,
            "management_exp": management_exp,
            "op_exp": op_exp,
            "total_exp": total_exp,
            "rent_income": rent_income,
            "other_income": other_income,
            "total_income": total_income,
            "adj_total_income": adj_total_income,
            "noi": noi,
            "niaf": niaf,
            "rent_exp": rent_exp,
            # Balances and values. End of month.
            "loan_balance": loan_balance,
            "home_value": home_value,
            "rent_comparison_portfolio": rent_comparison_portfolio,
            "extra_payments_portfolio": extra_payments_portfolio
        }
        data.append(month_data)

        ########################################################################
        #      Growth End of Year - Applies to next month values               #
        ########################################################################

        if (month + 1) % 12 == 0 and month > 0:
            property_tax_exp = home_value * ss.yr_property_tax_rate.val / 12
            insurance_exp = home_value * ss.yr_insurance_rate.val / 12
            hoa_exp = add_growth(hoa_exp, ss.yr_inflation_rate.val, 12)
            utility_exp = add_growth(utility_exp, ss.yr_inflation_rate.val, 12)
            maintenance_exp = home_value * ss.yr_maintenance.val / 12
            pmi_exp = pmi_true
            rent_income = add_growth(rent_income, ss.yr_rent_increase.val, 12)
            other_income = add_growth(other_income, ss.yr_rent_increase.val, 12)
            management_exp = ss.management_rate.val * rent_income
            rent_exp = add_growth(rent_exp, ss.yr_rent_increase.val, 12)

    return pd.DataFrame(data).set_index("index")


def get_yearly_agg_df(sim_df, oop, closing_costs):
    """
    After running the simulation, we want to aggregate the data to a yearly level for easier
    analysis and visualization. This function also calculates some derived metrics for plotting.
    """

    # List of columns for sum and mean aggregations
    sum_mean_cols = [
            "interest_exp", "principal_exp", "property_tax_exp", "insurance_exp",
            "hoa_exp", "maintenance_exp", "pmi_exp", "utility_exp", "management_exp",
            "op_exp", "total_exp", "rent_income", "other_income", "total_income",
            "adj_total_income", "noi", "niaf", "rent_exp"
    ]

    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}

    agg_dict.update({
        "loan_balance": "min", # min if the end of year for loan balance
        "home_value": "max",
        "rent_comparison_portfolio": "max",
        "extra_payments_portfolio": "max"
    })

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    def rename_columns(df):
        # remove sum from columns.
        # Value is implied total for the year,
        # mean value is implied for monthly.
        # also remove min and max from loan balance and home value,
        # its implied that these columns are values at the end of the year
        new_columns = {}
        for col in df.columns:
            if col.endswith('_sum') or col.endswith('_max') or col.endswith('_min'):
                new_columns[col] = col[:-4]
            elif col.endswith('_mean'):
                new_columns[col] = col[:-5] + '_mo'
        df.rename(columns=new_columns, inplace=True)

    rename_columns(year_df)

    cumsum_cols = [
        "niaf",
        "rent_exp",
        "interest_exp",
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    year_df["equity"] = year_df["home_value"] * (1 - ss.realtor_rate.val) - year_df["loan_balance"] 
    year_df["coc_roi"] = year_df["cum_niaf"] / oop
    year_df["profit"] = year_df["cum_niaf"] + year_df["equity"] - ss.rehab.val - closing_costs
    year_df["roi"] = year_df["profit"] / oop

    # parallel simulations
    year_df["renting_profit"] = year_df["rent_comparison_portfolio"] * (1- ss.capital_gains_tax_rate.val) - year_df["cum_rent_exp"]
    year_df["extra_payments_portfolio"] = year_df["extra_payments_portfolio"] * (1 - ss.capital_gains_tax_rate.val)

    # columns for plotting
    year_df["ownership_upside"] = year_df["profit"] - year_df["renting_profit"]

    return year_df


def get_mortgage_metrics(df, oop, loan_amount, closing_costs):
    return {
        #"Down Payment": format_currency(ss.down_payment.val),
        #"Rehab": format_currency(ss.rehab.val),
        #"Closing Costs": format_currency(closing_costs),
        "Cash Outlay": format_currency(oop),
        "Loan Amount": format_currency(loan_amount),
        "Total PMI Paid": format_currency(df["pmi_exp"].sum()),
        "Total Taxes Paid": format_currency(df["property_tax_exp"].sum()),
        "Total Interest Paid": format_currency(df["interest_exp"].sum()),
        "Default Interest Paid": format_currency(get_total_interest_paid(loan_amount, ss.interest_rate.val)),
    }


def get_investment_metrics(df, oop):
    # opr_metrics. Monthly income / OOP
    opr = df.loc[0, "rent_income_mo"] / oop
    formatted_opr = format_percent(opr)

    GRM = 0 
    if df.loc[0, "rent_income"] > 0:
        GRM = int(df.loc[0, "home_value"] / df.loc[0, "rent_income"])

    return  {
        "GRM": GRM,
        "Cap Rate": format_percent(df.loc[0, "noi"] / ss.home_price.val),
        "Year One Cash Flow": format_currency(df.loc[0, "niaf"]),
        "Year One ROI": format_percent(df.loc[0, "roi"]),
        "1% Rule": f"Yes {formatted_opr}" if opr >= 0.01 else f"No {formatted_opr}",
    }


def get_rent_vs_own_metrics(df):
    return {
        "One Year Ownership Upside": format_currency(df.loc[0, "profit"] - df.loc[0, "renting_profit"]),
        "Ten Year Ownership Upside": format_currency(df.loc[9, "profit"] - df.loc[9, "renting_profit"]),
    }


def get_all_simulation_data(include_metrics=False, extra_payments=False):
    closing_costs = ss.home_price.val * ss.closing_costs_rate.val
    cash_outlay = closing_costs + ss.down_payment.val + ss.rehab.val
    loan_amount = ss.home_price.val - ss.down_payment.val
    monthly_payment = get_amortization_payment(loan_amount, ss.interest_rate.val)

    monthly_df = get_monthly_sim_df(cash_outlay, loan_amount, monthly_payment, extra_payments)
    yearly_df = get_yearly_agg_df(monthly_df, cash_outlay, closing_costs)

    mortgage_metrics = get_mortgage_metrics(yearly_df, cash_outlay, loan_amount, closing_costs)
    investment_metrics = get_investment_metrics(yearly_df, cash_outlay)
    rental_comparison_metrics = get_rent_vs_own_metrics(yearly_df)

    results = {
        "yearly_df": yearly_df,
    }

    if include_metrics:
        results.update({
            "mortgage_metrics": mortgage_metrics,
            "investment_metrics": investment_metrics,
            "rental_comparison_metrics": rental_comparison_metrics,
        })

    return results


def calculate_and_display():

    def plot_data_ss(df, cols, names, title, percent=False):
        """Helper function so we dont have to repeat the xlim amd chart mode for all plots"""
        plot_data(df, cols, names, title, ss.xlim.val, mode=ss.chart_mode.val, percent=percent)

    results = get_all_simulation_data(include_metrics=True)
    yearly_df = results["yearly_df"]

    st.write("Select Category:")

    (
        top_tab_expenses,
        top_tab_investment, 
        top_tab_rent_vs_own,
        about,
    ) = st.tabs([
        "Mortgage and Expenses", 
        "Investment Analysis", 
        "Rent vs Own",
        "About"
    ])

    ########################################################################
    #      Mortgage and Expenses                                           #
    ########################################################################

    with top_tab_expenses:
        st.write("Select Chart:")

        (
            intro,
            tab_exp,
            tab_exp_over_time, 
            tab_home_value,
            tab_extra_payment
        ) = st.tabs([ 
            "Category Intro",
            "Expenses First Year", 
            "Expenses Over Time", 
            "Home Value",
            "Extra Payment Analysis"
        ])

        with intro:
            st.write("""This category contains information about the costs of owning a home and 
                     mortgage and the value of your home overtime. It can be used as a simple 
                     mortgage calculator. If you've filled out the rental income section, you can 
                     also see some simple comparisons between youre costs and income. The 'Extra 
                     Payment Analysis' tab will show you the impact of making extra payments on your 
                     mortgage and whether it is a good idea given other investment options.""")

        with tab_exp:
            col1, col2 = get_tab_columns()
            
            with col1:
                dict_to_metrics(results["mortgage_metrics"])

            with col2:
                pie_chart(yearly_df)


        with tab_exp_over_time:
            col1, col2 = get_tab_columns()
            
            with col1:
                dict_to_metrics(results["mortgage_metrics"])

            with col2:                
                stacked_bar(yearly_df)


        with tab_home_value:
            col1, col2 = get_tab_columns()
            
            with col1:
                dict_to_metrics(results["mortgage_metrics"])

            with col2:
                cols = ["home_value", "equity"]
                names= ["Home Value", "Equity"]
                title = "Home Value   <i>&</i>   Equity"
                plot_data_ss(yearly_df, cols, names, title)


        with tab_extra_payment:
            extra_payments_df = get_all_simulation_data(extra_payments=True)["yearly_df"]
            append_cols = ["profit", "extra_payments_portfolio"]
            merged_df = merge_simulations(yearly_df, extra_payments_df, append_cols, "ep")

            # add regular profit with extra payment portfolio from extra_payments_df which has been joined
            merged_df["portfolio_profit"] = merged_df["profit"] + merged_df["ep_extra_payments_portfolio"]

            # get delta for both simluations against just regulat profit
            merged_df["portfolio_profit_delta"] = merged_df["portfolio_profit"] - merged_df["profit"]
            merged_df["ep_profit_delta"] = merged_df["ep_profit"] - merged_df["profit"]

            col1, col2 = get_tab_columns()

            with col1:
                dict_to_metrics({"todo": "TODO"})
                st.container(height=20, border=False)
                st.write(":red[Additional Options]")
                extra_payment_inputs()

            with col2:
                cols = ["portfolio_profit_delta", "ep_profit_delta"]
                names= ["Addl. Profit Contribute to Stocks", "Addl. Profit Pay Down Loan"]
                title = "Additional Profit From Extra Payments"
                plot_data_ss(merged_df, cols, names, title, percent=False)


    ########################################################################
    #      Investment                                                      #
    ########################################################################

    with top_tab_investment:
        st.write("Select Chart:")
        (
            intro,
            tab_roi,
            tab_profits,
            tab_net_income,
        ) = st.tabs([ 
            "Category Intro",
            "ROI",
            "Profit",
            "Net Income",
        ])

        with intro:
            st.write("""This catgory shows common figures and metrics used to asses the quality of a
                     rental investment. This will be most useful if you plan on making some rental income 
                     with this property, but many of the figures are still useful in just assessing
                     home ownership as an invesment. If you havent spent time analysing rental properties,
                     the terms and figures here might be confusing or unfamiliar. Navigate to the 'About' tab
                     to learn more about these concepts and how to use them.""")

        with tab_net_income:
            col1, col2 = get_tab_columns()

            with col1:
                dict_to_metrics(results["investment_metrics"])

            with col2:
                cols = ["noi_mo", "niaf_mo"]
                names= ["Monthly NOI", "Monthly NIAF"]
                title = "Monthly Net Income"
                plot_data_ss(yearly_df, cols, names, title)


        with tab_roi:
            col1, col2 = get_tab_columns()
            
            with col1:
                dict_to_metrics(results["investment_metrics"])

            with col2:
                cols = ["roi", "coc_roi"]
                names= ["ROI", "Cash on Cash ROI"]
                title = "Return on Investment (ROI)"
                plot_data_ss(yearly_df, cols, names, title, percent=True)


        with tab_profits:
            col1, col2 = get_tab_columns()
            
            with col1:
                dict_to_metrics(results["investment_metrics"])

            with col2:
                cols = ["profit", "cum_niaf"]
                names= ["Total Profit (With Equity)", "Total Cash"]
                title = "Investment Profit/Loss"
                plot_data_ss(yearly_df, cols, names, title)


    ########################################################################
    #      Rent vs Own                                                     #
    ########################################################################

    with top_tab_rent_vs_own:
        st.write("Select Chart:")
        (
            intro,
            tab_rent_vs_own,
            tab_rent_vs_own_delta,
        ) = st.tabs([ 
            "Category Intro",
            "Rent vs Own",
            "Rent vs Own Delta",
        ])

        with intro:
            st.write("""
                This tab compares the total returns of owning a home versus renting.
                In this scenario, instead of buying a home, you would have put all the out of pocket cash into the stock market
                and live in a rental. In any month, if the expenses of owning
                a home are greater than rent, that extra cash is invested into the stock market.
                This captures the opportunity cost of capital. In many situations, if you arent house hacking,
                you should expect a loss in the short to medium term for either decision, but by comparing the two,
                you can figure out which one saves you more money in the long run, and how long you 
                have to live in a home to make it worth it over renting.
                """)

        with tab_rent_vs_own:
            col1, col2 = get_tab_columns()

            with col1:
                dict_to_metrics(results["rental_comparison_metrics"])
                st.container(height=20, border=False)
                st.write(":red[Additional Options]")
                rent_vs_own_inputs()

            with col2:
                cols = ["profit", "renting_profit"]
                names= ["Own", "Rent"]
                title = "Rent vs Own Profit/Loss"
                plot_data_ss(yearly_df, cols, names, title)


        with tab_rent_vs_own_delta:
            col1, col2 = get_tab_columns()

            with col1:
                dict_to_metrics(results["rental_comparison_metrics"])

            with col2:
                cols = ["ownership_upside"]
                names= ["Ownership Upside"]
                title = "Home Ownership Upside Over Renting"
                plot_data_ss(yearly_df, cols, names, title)


    ########################################################################
    #      About                                                           #
    ########################################################################

    with about:
        st.write("Made you look")



def main():
    local_css("./mortgage_calculator/style.css")

    st.title("Uncompromising Mortgage Calculator")

    with st.expander("Introduction", expanded=True):
        st.write("""
                Not your fathers mortgage calculator. This tools runs a month over month 
                simulation accounting for all factors and the 
                interplay between them. Expenses, rental income, reinvestment, 
                growth rates, taxes and fees, opportunity costs, and house hacking are all 
                considered.""")
        st.header("Example Use Cases")
        st.write("""
                - What are the short and long term costs of owning a home?
                - Is this rental property a good deal?
                - Should I rent or buy for my primary residence?
                - Should I pay down my loan with rental profits?
                - How much of my mortgage can I offset by house hacking?
                """)
        st.header("Getting Started")
        st.write("""
                - Fill out the fields in sidebar. They are ogranized into logical groups. Many inputs are prepopulated with reasonable defaults.
                - Start by adding a home price and down payment. If youre going to rent out any part of this property, fill out the fields in the rental income exapnder.
                - Click across the tabs to see different charts and metrics. 
                - Some tabs are straightforward and some might require familiazing yourself with certain concepts which you can explore in the 'About' tab. 
                - Look at tooltips for more information if youre unsure what to do with an input. 
                - For more in depth details, navigate to the 'About' tab.
                """)
        st.header("Tech Tips")
        st.write("""
                - Hover over charts to see exact values
                - Click and drag to zoom in on a particular area 
                - Adjust chart settings in the sidebar under the chart options expander
                - Collapse the sidebar by clicking the x in the top right corner of the sidebar 
                - Expanders have a ^ in the top corner of the box and can be collapsed by clicking the top of the box
                """)

    with st.sidebar:
        #run_it = st.button("Calculate")
        reset_inputs()
        st.markdown("### Input Fields")
        mortgage_inputs()
        expenses_inputs()
        economic_factors_inputs()
        rent_income_inputs()
        selling_inputs()
        chart_disaply_inputs()

    calculate_and_display()


main()