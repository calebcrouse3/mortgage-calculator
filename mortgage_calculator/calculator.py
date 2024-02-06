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
WIDTH = 700

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
        # populate_columns([
        #     lambda: st.checkbox("Paydown Loan with Profit", key=ss.paydown_with_profit.key),
        # ], 2)


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
    populate_columns([
        lambda: rate_input("Stock Growth Rate", ss.stock_growth_rate.key),
    ], 1)


def extra_payment_inputs():
    populate_columns([
        lambda: dollar_input("Mo. Payment Amount", ss.mo_extra_payment.key),
        lambda: dollar_input("Number of Payments", ss.num_extra_payments.key),
    ], 2)




def get_monthly_sim_df(oop, loan_amount, monthly_payment, paydown_with_profit=False, extra_payments=False):
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.
    """

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_price = get_monthly_pmi(ss.home_price.val, loan_amount, ss.pmi_rate.val, ss.home_price.val)
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
    pmi_required = pmi_price > 0

    # Stock portfolio comparisons
    total_expense_portfolio = oop # portfolio funded with all homeownership expenses
    rent_comparison_portfolio = oop # portfolio funded with money saved from renting
    reinvest_portfolio = 0 # portfolio funded with all positive cash flow
    extra_payments_portfolio = 0 # portfolio funded with extra payments


    data = []
    for month in np.arange(12 * 30):

        interest_exp = loan_balance * ss.interest_rate.val / 12

        # if youre ahead on payments, you cant pay more principal than the loan balance
        principal_exp = monthly_payment - interest_exp
        if principal_exp >= loan_balance:
            principal_exp = loan_balance

        loan_balance -= principal_exp

        # optionally make extra payments
        extra_payments_portfolio = add_growth(extra_payments_portfolio, ss.stock_growth_rate.val, months=1)
        # either make extra payments or add to portfolio
        if extra_payments:
            if month < ss.num_extra_payments.val:
                if loan_balance < ss.num_extra_payments.val:
                    loan_balance = 0
                else:
                    loan_balance -= ss.mo_extra_payment.val
        else:
            if month < ss.num_extra_payments.val:
                if loan_balance < ss.num_extra_payments.val:
                    extra_payments_portfolio += loan_balance
                else:
                    extra_payments_portfolio += ss.mo_extra_payment.val

        # pay pmi if required
        pmi_exp = 0
        if pmi_required:
            pmi_exp = pmi_price

        op_exp = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp +
            utility_exp +
            management_exp
        )

        total_exp = op_exp + interest_exp + principal_exp
        total_income = rent_income + other_income
        adj_total_income = total_income * (1 - ss.vacancy_rate.val)
        noi = adj_total_income - op_exp
        niaf = adj_total_income - total_exp

        # apply income tax to profits
        if niaf > 0:
            niaf *= (1 - ss.income_tax_rate.val)

        # optionally use niaf to pay down loan
        if niaf > 0 and paydown_with_profit:
            if niaf > loan_balance:
                loan_balance = 0
            else:
                loan_balance -= niaf

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = true_pmi > 0

        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)
        rent_comparison_portfolio = add_growth(rent_comparison_portfolio, ss.stock_growth_rate.val, months=1)

        # contribute to portfolio is money saved from renting
        if total_exp > rent_exp:
            rent_comparison_portfolio += total_exp - rent_exp

        # profit reinvestment stock portfolio
        # since sim represent end of month, always grow first then add contribution
        reinvest_portfolio = add_growth(reinvest_portfolio, ss.stock_growth_rate.val, months=1)
        if niaf > 0:
            reinvest_portfolio += niaf

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
            "reinvest_portfolio": reinvest_portfolio,
            "extra_payments_portfolio": extra_payments_portfolio
        }
        data.append(month_data)

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_exp = home_value * ss.yr_property_tax_rate.val / 12
            insurance_exp = home_value * ss.yr_insurance_rate.val / 12
            hoa_exp = add_growth(hoa_exp, ss.yr_inflation_rate.val, 12)
            utility_exp = add_growth(utility_exp, ss.yr_inflation_rate.val, 12)
            maintenance_exp = home_value * ss.yr_maintenance.val / 12
            pmi_price = true_pmi
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
            "interest_exp",
            "principal_exp",
            "property_tax_exp",
            "insurance_exp",
            "hoa_exp",
            "maintenance_exp",
            "pmi_exp",
            "utility_exp",
            "management_exp",
            "op_exp",
            "total_exp",
            "rent_income",
            "other_income",
            "total_income",
            "adj_total_income",
            "noi",
            "niaf",
            "rent_exp"
    ]

    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}

    agg_dict.update({
        "home_value": 'max', # end of year is max
        "loan_balance": 'min', # end of year is min
        "rent_comparison_portfolio": 'max',
        "reinvest_portfolio": 'max',
        "extra_payments_portfolio": 'max'
    })

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    year_df.rename(columns={
        "home_value_max": "home_value",
        "loan_balance_min": "loan_balance",
        "rent_comparison_portfolio_max": "rent_comparison_portfolio",
        "reinvest_portfolio_max": "reinvest_portfolio",
        "extra_payments_portfolio_max": "extra_payments_portfolio"
    }, inplace=True)

    def rename_columns(df):
        # remove sum from columns.
        # Value is implied total for the year,
        # mean value is implied for monthly
        new_columns = {}
        for col in df.columns:
            if col.endswith('_sum'):
                new_columns[col] = col[:-4]
            elif col.endswith('_mean'):
                new_columns[col] = col[:-5] + '_mo'
        df.rename(columns=new_columns, inplace=True)

    rename_columns(year_df)

    # get the niaf for any months that were a loss. For the reinvestment analysis
    year_df["niaf_neg"] = year_df["niaf"].apply(lambda x: x if x < 0 else 0)
    
    cumsum_cols = [
        "niaf",
        "niaf_neg",
        "rent_exp",
        "interest_exp",
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    year_df["equity"] = year_df["home_value"] * (1 - ss.realtor_rate.val) - year_df["loan_balance"] 
    year_df["coc_roi"] = year_df["cum_niaf"] / oop
    year_df["profit"] = year_df["cum_niaf"] + year_df["equity"] - ss.rehab.val - closing_costs
    year_df["roi"] = year_df["profit"] / oop
    year_df["renting_profit"] = year_df["rent_comparison_portfolio"] * (1- ss.capital_gains_tax_rate.val) - year_df["cum_rent_exp"]
    year_df["ownership_upside"] = year_df["profit"] - year_df["renting_profit"]

    # metrics for reinvestment analysis
    year_df["profit_reinvest"] = (
        year_df["reinvest_portfolio"] * (1 - ss.capital_gains_tax_rate.val)
        + year_df["equity"] 
        + year_df["cum_niaf_neg"]
        - ss.rehab.val
        - closing_costs
    )

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


def get_all_simulation_data(include_metrics=True, paydown_with_profit=False, extra_payments=False):
    CLOSING_COSTS = ss.home_price.val * ss.closing_costs_rate.val
    OOP = CLOSING_COSTS + ss.down_payment.val + ss.rehab.val
    LOAN_AMOUNT = ss.home_price.val - ss.down_payment.val
    MONTHLY_PAYMENT = get_amortization_payment(LOAN_AMOUNT, ss.interest_rate.val)

    monthly_df = get_monthly_sim_df(OOP, LOAN_AMOUNT, MONTHLY_PAYMENT, paydown_with_profit, extra_payments)
    yearly_df = get_yearly_agg_df(monthly_df, OOP, CLOSING_COSTS)

    mortgage_metrics = get_mortgage_metrics(yearly_df, OOP, LOAN_AMOUNT, CLOSING_COSTS)
    investment_metrics = get_investment_metrics(yearly_df, OOP)
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
    results = get_all_simulation_data()

    yearly_df = results["yearly_df"]

    (
        tab_exp,
        tab_exp_over_time, 
        tab_home_value,
        tab_extra_payment,
        tab_roi,
        tab_profits,
        tab_reinvest_analysis,
        tab_net_income,
        tab_rent_vs_own,
        tab_rent_vs_own_delta,
        #data_table,
        about
    ) = st.tabs([ 
        "Expenses First Year", 
        "Expenses Over Time", 
        "Home Value",
        "Extra Payment Analysis",
        "ROI",
        "Profit",
        "Reinvestment Analysis",
        "Net Income",
        "Rent vs Own",
        "Rent vs Own Delta",
        #"Data Table",
        "About"
    ])

    BLUE = "#1f77b4"
    ORANGE = "#ff7f0e"

    COLOR_MAP = {
        "interest_exp_mo":      "#0068C9",  # Blue
        "principal_exp_mo":     "#83C9FF",  # Light Blue
        "property_tax_exp_mo":  "#FF2A2B",  # Red
        "insurance_exp_mo":     "#FFABAB",  # Light Red
        "hoa_exp_mo":           "#2AB09D",  # Light Green
        "maintenance_exp_mo":   "#7EEFA1",  # Green
        "utility_exp_mo":       "#FF8700",  # Organe
        "management_exp_mo":    "#FFD16A",  # Light Orange
        "pmi_exp_mo":           "#9030A1",  # Purple
    }

    with tab_exp:
        col1, col2 = get_tab_columns()
        
        with col1:
            df = yearly_df.loc[0:0, list(COLOR_MAP.keys())]
            df = df.T.reset_index().rename(columns={"index": "name", 0: "value"})
            df = df.join(pd.DataFrame.from_dict(COLOR_MAP, orient='index', columns=["color"]), on="name")
            df['order'] = df['name'].apply(lambda x: list(COLOR_MAP.keys()).index(x))
            df = df.sort_values('order').drop('order', axis=1)
            df["formatted_value"] = df["value"].apply(lambda x: format_currency(x))
            df["name"] = df["name"].apply(lambda x: format_label_string(x))
            df = df[df["value"] > 0]

            total = format_currency(df["value"].sum())

            fig = go.Figure()

            fig.add_trace(go.Pie(
                values=df['value'].values, 
                labels=df['name'].values,
                marker_colors=df["color"].values,
                hole=0.6,
                direction ='clockwise', 
                sort=False,
                textposition='outside',
                text=df["formatted_value"], 
                textinfo='label+text',
                marker=dict(line=dict(color='#000000', width=2)),
                hoverinfo = 'none'
            ))
            

            fig.add_annotation(dict(
                text=f"Total: {total}", 
                x=0.5, y=0.5, font_size=30, showarrow=False
            ))

            fig.update_layout(
                title="Monthly Expenses in First Year",
                showlegend=False, 
                height=HEIGHT,
                width=WIDTH
            )

            fig_display(fig)

        with col2:
            dict_to_metrics(results["mortgage_metrics"])


    with tab_exp_over_time:
        col1, col2 = get_tab_columns()
        
        with col1:
                
            zero_sum_cols = [k for k in COLOR_MAP.keys() if yearly_df[k].sum() == 0]
            color_map_redux = {k: v for k, v in COLOR_MAP.items() if k not in zero_sum_cols}

            fig = go.Figure()

            for col, color in color_map_redux.items():
                fig.add_trace(go.Bar(
                    x=yearly_df.index + 1, 
                    y=yearly_df[col], 
                    name=format_label_string(col),
                    hoverinfo='y',
                    hovertemplate='$%{y:,.0f}',
                    marker_color=color
                ))

            if ss.mo_rent_income.val > 0:
                fig.add_trace(go.Scatter(
                    x=yearly_df.index + 1, 
                    y=yearly_df["adj_total_income_mo"], 
                    mode='markers',
                    name="Total Rental Income",
                    hoverinfo='y',
                    hovertemplate='$%{y:,.0f}',
                    # add a black boarder to the markers
                    marker=dict(size=12, color='white', line=dict(color='black', width=3)),
                ))
                
            fig.update_layout(
                title="Monthly Expenses Over Time",
                yaxis=dict(title='Dollars ($)', tickformat='$,.0f'),
                barmode='stack',
                height=HEIGHT,
                width=WIDTH,
                xaxis=dict(title='Year', tickmode='array', tickvals=np.arange(5, 31, 5)),
            )

            fig.update_xaxes(range=[0, 31])
            fig_display(fig)

        with col2:
            dict_to_metrics(results["mortgage_metrics"])


    with tab_home_value:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["home_value", "equity"]
            names= ["Home Value", "Equity"]
            colors = [BLUE, ORANGE]
            title = "Home Value   <i>&</i>   Equity"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val, percent=False)

        with col2:
            dict_to_metrics(results["mortgage_metrics"])

    with tab_extra_payment:
        extra_payment_inputs()

        # want to know if extra payments are worth it versus just putting that money in the stock market
        # but also want to know how much extra profit is made over time by putting in extra payments

        # regular results doesnt have extra payments but will add extra payment amount to portfolio
        yearly_df["profit_with_extra_payment_portfolio"] = yearly_df["profit"] + yearly_df["extra_payments_portfolio"]
        
        # get profit with extra payments
        alt_results = get_all_simulation_data(include_metrics=False, paydown_with_profit=False, extra_payments=True)
        alt_results["yearly_df"]["profit_with_extra_payment"] = alt_results["yearly_df"]["profit"]

        yearly_df = yearly_df.join(alt_results["yearly_df"][["profit_with_extra_payment"]], how="left")

        cols = ["profit_with_extra_payment_portfolio", "profit_with_extra_payment"]
        names= ["Profit with Extra Payments Portfolio", "Profit With Extra Payments"]
        colors = ['#1f77b4', '#ff7f0e']
        title = "Extra Payments Analysis"
        plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)


    with tab_net_income:
        col1, col2 = get_tab_columns()
        
        # add monthly vs yearly toggle?
        with col1:
            cols = ["noi_mo", "niaf_mo"]
            names= ["Monthly NOI", "Monthly NIAF"]
            colors = ['#1f77b4', '#ff7f0e']
            title = "Monthly Net Income"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
        with col2:
            dict_to_metrics(results["investment_metrics"])

    with tab_roi:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["roi", "coc_roi"]
            names= ["ROI", "Cash on Cash ROI"]
            colors = [BLUE, ORANGE]
            title = "Return on Investment (ROI)"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=True)

        with col2:
            dict_to_metrics(results["investment_metrics"])


    with tab_profits:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["profit", "cum_niaf"]
            names= ["Total Profit (With Equity)", "Total Cash"]
            colors = [BLUE, ORANGE]
            title = "Investment Profit/Loss"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
        with col2:
            dict_to_metrics(results["investment_metrics"])



    with tab_reinvest_analysis:
        # need total profit for reinvestmenr
        # need total profit and reinvest stock value for

        # TODO Need to run it again with reinvestment and plot total profit
        alt_results = get_all_simulation_data(include_metrics=False, paydown_with_profit=True)

        paydown_with_profit = alt_results["yearly_df"].rename(columns={"profit": "profit_with_paydown"})
        paydown_with_profit = paydown_with_profit[["profit_with_paydown"]]
        
        # join paydown with profit to yearly_df on the df index
        yearly_df = yearly_df.join(paydown_with_profit, how="left")

        # get difference between regular profit and other options
        yearly_df["profit_reinvest_delta"] = yearly_df["profit_reinvest"] - yearly_df["profit"]
        yearly_df["profit_with_paydown_delta"] = yearly_df["profit_with_paydown"] - yearly_df["profit"]

        col1, col2 = get_tab_columns()
        
        with col1:
            pass
            cols = ["profit_reinvest_delta", "profit_with_paydown_delta"]
            names= ["Invest Cash in Stock Market", "Use Cash to Pay Down Loan"]
            colors = [BLUE, ORANGE, "green", "purple", "red"]
            title = "Extra Profit from Cash Flow Reinvestment"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
        with col2:
            dict_to_metrics(results["investment_metrics"]) 


    with tab_rent_vs_own:
        with st.expander("Rent vs Own", expanded=True):
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
            cols = ["profit", "renting_profit"]
            names= ["Own", "Rent"]
            colors = [BLUE, ORANGE]
            title = "Rent vs Own Profit/Loss"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)

        with col2:
            dict_to_metrics(results["rental_comparison_metrics"])
            st.container(height=20, border=False)
            st.write(":red[Additional Options]")
            rent_vs_own_inputs()


    with tab_rent_vs_own_delta:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["ownership_upside"]
            names= ["Ownership Upside"]
            colors = [BLUE]
            title = "Home Ownership Upside Over Renting"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
        with col2:
            dict_to_metrics(results["rental_comparison_metrics"])


    # with data_table:
    #         default_cols = [
    #             "interest_exp",
    #             "principal_exp",
    #             "op_exp",
    #             "total_exp",
    #             "adj_total_income",
    #             "niaf",
    #             "rent_exp",
    #             "stock_contrib",
    #             "home_value",
    #             "loan_balance",
    #             "stock_value",
    #             "cum_niaf",
    #             "cum_stock_contrib",
    #             "equity",
    #             "total_return",
    #             "coc_roi",
    #             "roi",
    #             "total_return_rent",
    #         ]
    #         selected_columns = st.multiselect('Select columns to display:', yearly_df.columns, default=default_cols)
    #         round_columns = [x for x in selected_columns if "roi" not in x]
    #         filtered_df = yearly_df[selected_columns]
    #         filtered_df.loc[: ,round_columns] = filtered_df.loc[: ,round_columns].round()
    #         st.dataframe(filtered_df, use_container_width=True)

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