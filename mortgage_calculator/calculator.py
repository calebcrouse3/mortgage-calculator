from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import numpy_financial as npf

from utils import *
from utils_finance import *
from session_state_interface import SessionStateInterface, ALT_INVESTMENTS


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
            lambda: dollar_input("Rehab", ss.rehab.key, min_value=0, max_value=5e5, step=2e3,
                help="Cost of repairs or renovations right after buying."),
        ], 2)
        populate_columns([
            lambda: dollar_input("Down Payment", ss.down_payment.key, min_value=0, max_value=1e6, step=5e3),
            lambda: rate_input("Interest Rate", ss.interest_rate.key),
        ], 2)
        populate_columns([
            lambda: rate_input("Closing Costs", ss.closing_costs_rate.key, 
                help="Calculated as a percentage of home price"),
            lambda: rate_input("PMI Rate", ss.pmi_rate.key, 
                help="If down payment is less than 20% of home price, youll have to pay PMI"),
        ], 2)


def expenses_inputs():
    with st.expander("Expenses", expanded=False):
        populate_columns([
            lambda: rate_input("Property Tax", ss.yr_property_tax_rate.key),
            lambda: rate_input("Insurance Rate", ss.yr_insurance_rate.key, 
                help="Yearly insurance as a percentage of home value"),
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
        st.write("Assumptions about growth rates in the economy and housing market.")
        populate_columns([
            lambda: rate_input("Home Appreciation", ss.yr_home_appreciation.key),
            lambda: rate_input("Inflation Rate", ss.yr_inflation_rate.key),   
        ], 2)
        populate_columns([
            lambda: rate_input("Yearly Rent Increase", ss.yr_rent_increase.key)
        ], 2)


def rent_income_inputs():
    with st.expander("Rental Income", expanded=False):
        populate_columns([
            lambda: dollar_input("Mo. Rental Income", ss.mo_rent_income.key, max_value=1e5, step=50),
            lambda: dollar_input("Mo. Misc Income", ss.mo_other_income.key, max_value=1e4, step=50),
        ], 2)
        populate_columns([
            lambda: rate_input("Vacancy Rate", ss.vacancy_rate.key,
                help="Percentage of the year the property is vacant"),
            lambda: rate_input("Management Fee", ss.management_rate.key,
                help="Percentage of rental income paid to property management"),
        ], 2)


def selling_inputs():
    with st.expander("Selling Fees/Taxes", expanded=False):
        populate_columns([
            lambda: rate_input("Income Tax", ss.income_tax_rate.key, 
                help="If rental property cash flows, that profit is taxed at this rate"),
            lambda: rate_input("Realtor Fee", ss.realtor_rate.key),
        ], 2)
        populate_columns([
            lambda: rate_input("Capital Gains Tax", ss.capital_gains_tax_rate.key, 
                help="Tax on profits from selling property or stock"),
        ], 2)


def reset_inputs():
    populate_columns([
        lambda: st.button("Reset Inputs", on_click=ss.clear),
    ], 2)


def chart_disaply_inputs():
    with st.expander("Chart Options", expanded=False):
        populate_columns([
            lambda: st.number_input("X-axis Max (Years)", min_value=5, max_value=30, step=5, key=ss.xlim.key),
            lambda: st.selectbox("Chart Mode", ["Lines", "Dots"], key=ss.chart_mode.key),
        ], 2)


def rent_vs_own_inputs():
    with st.form("rent_vs_own_form", border=False):
        st.form_submit_button('Update Rent Payment')
        populate_columns([
            lambda: dollar_input("Mo. Rent Payment", ss.rent_exp.key, min_value=0, max_value=1e5, step=100,
                help="This is the monthly rent you would pay instead of buying the home in consideration."),
        ], 1)
        populate_columns([
            lambda: rate_selectbox_input("Alt. Investment", options=ALT_INVESTMENTS.keys(), key=ss.rent_surplus_portfolio_growth.key,
                help="This is the growth rate an alternative investment with an acceptable risk factor. For example, a bond portfolio."),
        ], 1)


def extra_payment_inputs():
    with st.form("extra_payment_form", border=False):
        st.form_submit_button('Update Extra Payments')
        populate_columns([
            lambda: dollar_input("Mo. Payment Amount", ss.mo_extra_payment.key, 
                help="Extra payment paid monthly towards the principle of the loan"),
        ], 1)
        populate_columns([
            lambda: dollar_input("Number of Payments", ss.num_extra_payments.key, 
                help="Number of months to make extra payments starting from month 1"),
        ], 1)
        populate_columns([
            lambda: rate_selectbox_input("Alt. Investment", options=ALT_INVESTMENTS.keys(), key=ss.extra_payments_portfolio_growth.key,
                help="This is the growth rate on an alternate investment with simimlar low risk. For example, a bond portfolio."),
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
        rent_comparison_portfolio = add_growth(rent_comparison_portfolio, ss.rent_surplus_portfolio_growth.val, months=1)
        extra_payments_portfolio = add_growth(extra_payments_portfolio, ss.extra_payments_portfolio_growth.val, months=1)

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
            "extra_payment_exp": extra_payment_exp,
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
            "adj_total_income", "noi", "niaf", "rent_exp", "extra_payment_exp"
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
        "principal_exp",
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # VALIDATED: this is the amount of ownership of the home you have at the end of the year
    year_df["equity"] = year_df["home_value"] - year_df["loan_balance"]
    # VALIDATED: this gives the total income from selling the home in a particular year which factors in seling costs
    year_df["sale_income"] = year_df["equity"] - (year_df["home_value"] * ss.realtor_rate.val)
    
    # these need to be understood and validated
    year_df["capital_gains"] = year_df["sale_income"] + year_df["cum_principal_exp"] - ss.home_price.val - ss.down_payment.val
    year_df["return"] = year_df["capital_gains"] + year_df["cum_niaf"] - closing_costs - ss.rehab.val


    # VALIDATED: this gives the total return for the time period up to a particular year if the home is sold
    year_df["total_return"] = year_df["cum_niaf"] + year_df["sale_income"] - oop
    # ALMOST VALIDATED: This is the total net value of assets (cash and property) at the end of the year. 
    # Not sure if using sale income or equity is better. What does "net worth" imply?. 
    # Depends on if you still own the home or not I guess.
    year_df["net_worth_post_sale"] = year_df["cum_niaf"] + year_df["sale_income"] - ss.rehab.val - closing_costs
    
    
    # ALMOST VALIDATED: this gives the tota rate of return for the time period up to a particular year if the home is sold
    year_df["roi"] = year_df["total_return"] / oop
    # VALIDATED: Annualized yearly ROI for the time period up to a particular year if the home is sold at the end of that year.
    # Version of the CAGR formula. Also have to add 1 to index to make it number of years passed.
    year_df["annualized_roi"] = (1 + year_df["roi"]) ** (1 / (year_df.index + 1)) - 1
    # VALIDATED: this gives the coc return in a particular year ignoring home sale income
    year_df["annualized_coc_roi"] = year_df["niaf"] / oop
    # VALIDATE: Return on equity is the annual return divided by the equity in the home
    # This probably needs to be altered to reflect the equity at the beginning of the year, or even use the sale income at the beginning of the year
    # And the return should probably also include appreciation of the home
    #year_df["start_equity"] = year_df["equity"].shift(1)
    year_df["start_sale_income"] = year_df["sale_income"].shift(1)
    #year_df["start_sale_income"].iloc[0] = ss.down_payment.val * (1 - ss.realtor_rate.val)
    year_df["annual_roe"] = (year_df["sale_income"] - year_df["start_sale_income"] + year_df["niaf"]) / year_df["start_sale_income"]
    
    
    # parallel simulations. Need to get Net worth of these simulations
    year_df["renting_net_worth"] = year_df["rent_comparison_portfolio"] * (1 - ss.capital_gains_tax_rate.val) - year_df["cum_rent_exp"]
    year_df["extra_payments_portfolio"] = year_df["extra_payments_portfolio"] * (1 - ss.capital_gains_tax_rate.val)

    return year_df


def get_mortgage_metrics(df, oop, loan_amount, closing_costs):
    return {
        #"Down Payment": format_currency(ss.down_payment.val),
        #"Rehab": format_currency(ss.rehab.val),
        "Closing Costs": format_currency(closing_costs),
        "Cash Outlay": format_currency(oop),
        "Loan Amount": format_currency(loan_amount),
        "Total PMI Paid": format_currency(df["pmi_exp"].sum()),
        "Total Taxes Paid": format_currency(df["property_tax_exp"].sum()),
        "Total Interest Paid": format_currency(df["interest_exp"].sum()),
    }


def get_investment_metrics(df, oop):
    # opr_metrics. Monthly income / OOP
    opr = df.loc[0, "rent_income_mo"] / ss.home_price.val
    formatted_opr = format_percent(opr)

    GRM = 0 
    if df.loc[0, "rent_income"] > 0:
        GRM = int(df.loc[0, "home_value"] / df.loc[0, "rent_income"])

    return  {
        "Gross Rental Multiplier": GRM,
        "Cap Rate": format_percent(df.loc[0, "noi"] / ss.home_price.val),
        "First Mo. Cash Flow": format_currency(df.loc[0, "niaf_mo"]),
        "5 Year Annualized ROI": format_percent(df.loc[4, "annualized_roi"]),
        "1% Rule": f"Yes {formatted_opr}" if opr >= 0.01 else f"No {formatted_opr}",
    }


def get_rent_vs_own_metrics(df):
    return {"TODO": "TODO"}
    # return {
    #     "One Year Ownership Upside": format_currency(df.loc[0, "profit"] - df.loc[0, "renting_profit"]),
    #     "Ten Year Ownership Upside": format_currency(df.loc[9, "profit"] - df.loc[9, "renting_profit"]),
    # }


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

    def get_plot_ss(df, cols, names, title, percent=False, line_config=None, annotation_config=None):
        """Helper function so we dont have to repeat the xlim amd chart mode for all plots"""
        get_plot(df, cols, names, title, ss.xlim.val, mode=ss.chart_mode.val, percent=percent, line_config=line_config, annotation_config=annotation_config)

    results = get_all_simulation_data(include_metrics=True)
    yearly_df = results["yearly_df"]

    (
        tab_expenses,
        tab_extra_payments,
        tab_rent_vs_own, 
        tab_investing,
        about,
    ) = st.tabs([
        "Expenses",
        "Extra Payments",
        "Rent vs Own",
        "Investing", 
        "About"
    ])


    ########################################################################
    #      Expenses                                          
    ########################################################################

    with tab_expenses:
        with st.expander("Description", expanded=True):
            st.write("""This category contains information about the costs of owning a home and 
                        mortgage and the value of your home overtime. It can be used as a simple 
                        mortgage calculator. If you've filled out the rental income section, you can 
                        also see some simple comparisons between youre costs and income. The 'Extra 
                        Payment Analysis' tab will show you the impact of making extra payments on your 
                        mortgage and whether it is a good idea given other investment options.""")

        col1, col2 = get_tab_columns()

        with col1:
            dict_to_metrics(results["mortgage_metrics"])

        with col2:
            pie_chart(yearly_df)
            # How do I make sure they see this down here
            stacked_bar(yearly_df)


    ########################################################################
    #      Extra Payments                                                  #
    ########################################################################

    with tab_extra_payments:
        with st.expander("Description", expanded=True):
            st.write("""Many home owners consider making extra payments towards there mortgage to save on interest.
                     This tab allows you to add extra monthly payments and see the effect of interest savings over time.
                     Its important to also consider if that extra money would have been better spent somewhere else.
                     This chart also tells you how much you could have made if you had instead invested that money in a 
                     stock portfolio with continuous growth. The main variables that effect the difference between these 
                     two options are the difference between interest rate on the loan and the growth rate of the stock portfolio.
                     In this scenario. Its also important to consider that the stock market is highly variable and returns, especially
                     in the short term, may not be continuous. Where as the interest savings from extra payments are guaranteed.
                     Conversely, the savings on interest from extra payments take time to accumulate, 
                     where as the stock portfolio has the potential to grow immediately. Extra mortgage payments 
                     with have a greater effect on the interest savings the earlier they are made.""")

        extra_payments_df = get_all_simulation_data(extra_payments=True)["yearly_df"]
        append_cols = ["net_worth_post_sale", "extra_payments_portfolio", "loan_balance", "extra_payment_exp"]
        merged_df = merge_simulations(yearly_df, extra_payments_df, append_cols, "ep")

        # add regular profit with extra payment portfolio from extra_payments_df which has been joined
        merged_df["portfolio_nw"] = merged_df["net_worth_post_sale"] + merged_df["ep_extra_payments_portfolio"]

        # get delta for both simluations against just regulat profit
        merged_df["portfolio_nw_delta"] = merged_df["portfolio_nw"] - merged_df["net_worth_post_sale"]
        merged_df["ep_nw_delta"] = merged_df["ep_net_worth_post_sale"] - merged_df["net_worth_post_sale"]

        # remove any rows after the first row with a loan balance of 0
        zero_index = merged_df[merged_df["ep_loan_balance"] == 0].index[0]

        merged_df = merged_df.loc[:zero_index]

        crossover = min_crossover(merged_df["ep_nw_delta"].values, merged_df["portfolio_nw_delta"].values)
        df_len = len(merged_df)
        total_extra_payments = merged_df["ep_extra_payment_exp"].sum()

        col1, col2 = get_tab_columns()

        with col1:
            dict_to_metrics({
                "Reduced Payoff Time": f"{30 - df_len} Years",
                "Total Extra Payment": format_currency(total_extra_payments),
                "Total Interest Savings": format_currency(merged_df.loc[zero_index, "ep_nw_delta"])})
            st.container(height=20, border=False)
            st.write(":red[Additional Options]")
            extra_payment_inputs()

        with col2:
            ypos = max(merged_df.loc[df_len-1, "portfolio_nw_delta"], merged_df.loc[df_len-1, "ep_nw_delta"])
            line_config = dict(
                type='line', 
                x0=df_len, x1=df_len, y0=0, y1=ypos*1.15, 
                line=dict(dash='dot', color='white', width=2),
            )

            annotation_config = dict(
                x=df_len-1, y=ypos*1.2, xref='x', yref='y', text='Mortgage Paid Off', showarrow=False
            )
            cols = ["portfolio_nw_delta", "ep_nw_delta"]
            names= ["Contribute to Stocks", "Pay Down Loan"]
            title = "Added Net Worth From Extra Payments"
            get_plot_ss(merged_df, cols, names, title, percent=False, line_config=line_config, annotation_config=annotation_config)

            if total_extra_payments == 0:
                st.write(f":orange[Analysis] Add some extra payments to see results.")              
            elif crossover == -1:
                st.write(":orange[Analysis] Over the long run, you would probably have more money if you had invested in the stock market.")
            elif crossover >= 0:
                st.write(f":orange[Analysis] Making these extra payments is a smart idea if plan on living in this house for at least {crossover} years.")


    ########################################################################
    #      Rent vs Own                                                     #
    ########################################################################

    with tab_rent_vs_own:
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

        col1, col2 = get_tab_columns()

        with col1:
            dict_to_metrics(results["rental_comparison_metrics"])
            st.container(height=20, border=False)
            st.write(":red[Additional Options]")
            rent_vs_own_inputs()

        with col2:
            #yearly_df["rent_vs_own_net_worth"] = yearly_df["net_worth_post_sale"] - yearly_df["renting_net_worth"]
            cols = ["net_worth_post_sale", "renting_net_worth"]
            names= ["Own", "Rent"]
            title = "Rent vs Own Total Net Worth "
            get_plot_ss(yearly_df, cols, names, title)


    ########################################################################
    #      Investment                                                      #
    ########################################################################

    with tab_investing:
        st.write("""This catgory shows common figures and metrics used to asses the quality of a
                    rental investment. This will be most useful if you plan on making some rental income 
                    with this property, but many of the figures are still useful in just assessing
                    home ownership as an invesment. If you havent spent time analysing rental properties,
                    the terms and figures here might be confusing or unfamiliar. Navigate to the 'About' tab
                    to learn more about these concepts and how to use them.""")

        col1, col2 = get_tab_columns()

        with col1:
            dict_to_metrics(results["investment_metrics"])

        with col2:
            cols = ["niaf_mo", "total_exp_mo", "total_income_mo"]
            names= ["Mo Cashflow", "Mo Expenses", "Mo Income"]
            title = "Monthly Cashflow"
            get_plot_ss(yearly_df, cols, names, title)
    
            cols = ["annualized_roi", "annualized_coc_roi", "annual_roe"]
            names= ["Annualized ROI", "Annual COC ROI", "Annual ROE"]
            title = "Annualized ROI, ROE, and COC ROI"
            get_plot_ss(yearly_df, cols, names, title, percent=True)

        dollar_cols = ["total_income", "total_exp", "niaf", "home_value", 
                       "loan_balance", "equity", "sale_income", "total_return"]
        
        decimal_cols = ["annualized_roi", "annual_roe", "annualized_coc_roi"]

        polished_df = yearly_df[dollar_cols + decimal_cols]
        polished_df[dollar_cols] = polished_df[dollar_cols].round()
        polished_df[dollar_cols] = polished_df[dollar_cols].applymap(format_currency)
        polished_df[decimal_cols] = polished_df[decimal_cols].apply(lambda x: round(x * 100, 1))
        polished_df[decimal_cols] = polished_df[decimal_cols].astype(str) + "%"
        polished_df.index.name = "Year"
        polished_df.index += 1

        rename_dict = {
            "total_income": "Income",
            "total_exp": "Expenses",
            "niaf": "Cash FLow",
            "home_value": "Home Value",
            "equity": "Equity",
            "sale_income": "Sale Income",
            "total_return": "Total Return",
            "annualized_roi": "Annualized ROI",
            "annual_roe": "Annual ROE",
            "annualized_coc_roi": "Annual COC ROI"
        }

        polished_df.rename(columns=rename_dict, inplace=True)
        st.write("Year End Metrics")
        st.write(polished_df[list(rename_dict.values())])


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
        with st.form("my_form", border=False):
            st.form_submit_button('Update Calculation')
            st.markdown("### Input Fields")
            mortgage_inputs()
            expenses_inputs()
            rent_income_inputs()
            economic_factors_inputs()
            selling_inputs()
            chart_disaply_inputs()
        reset_inputs()
    
    calculate_and_display()


main()