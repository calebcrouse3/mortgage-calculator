from math import *

import streamlit as st
import numpy as np
import pandas as pd
import plotly.graph_objs as go

from utils import *
from utils_finance import *
from st_text import *
from utils_inputs import *

from session_state_interface import SessionStateInterface


st.set_page_config(layout="wide")
ss = SessionStateInterface()

# TODO, cache yearly df for user?

CLOSING_COSTS = ss.home_price.val * ss.closing_costs_rate.val
OOP = CLOSING_COSTS + ss.down_payment.val + ss.rehab.val
LOAN_AMOUNT = ss.home_price.val - ss.down_payment.val
MONTHLY_PAYMENT = get_monthly_payment_amount(LOAN_AMOUNT, ss.interest_rate.val)
STOCK_GROWTH_RATE = 0.07
INCOME_TAX_RATE = 0.25
REALTOR_RATE = 0.06
STOCK_TAX_RATE = 0.15


def mortgage_inputs():
    with st.expander("Mortgage", expanded=True):
        populate_columns([
            lambda: dollar_input("Home Price", ss.home_price.key),
            lambda: dollar_input("Rehab", ss.rehab.key),
        ], 2)
        populate_columns([
            lambda: dollar_input("Down Payment", ss.down_payment.key),
            lambda: rate_input("Interest", ss.interest_rate.key),
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
            lambda: dollar_input("HOA Fees", ss.mo_hoa_fees.key),
            lambda: dollar_input("Utilities", ss.mo_utility.key),
        ], 2)
        populate_columns([
            lambda: dollar_input("Monthly Maintenance", ss.mo_maintenance.key),     
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
            lambda: dollar_input("Monthly Rental Income", ss.mo_rent_income.key),
            lambda: dollar_input("Monthly Misc Income", ss.mo_other_income.key),
        ], 2)
        populate_columns([
            lambda: rate_input("Vacancy Rate", ss.vacancy_rate.key),
            lambda: rate_input("Management Fee", ss.management_rate.key),
        ], 2)
        populate_columns([
            lambda: st.checkbox("Paydown Loan with Profit", key=ss.paydown_with_profit.key),
        ], 2)


def calculate_inputs():
    populate_columns([
        lambda: st.button("Reset Values", on_click=ss.clear),
        lambda: st.button("Calculate"),
    ], 2)


def hide_text_input():
    populate_columns([
        lambda: st.checkbox("Hide All Text Blobs", key=ss.hide_text.key),
    ], 2)


def selling_fees_inputs():
    populate_columns([
        lambda: st.checkbox("Include Selling taxes/fees", key=ss.include_selling_costs.key),
    ], 1)


def returns_inputs():
    populate_columns([
        lambda: st.checkbox("Gross Returns", key=ss.use_gross_returns.key),
    ], 1)


def rent_returns_inputs():
    populate_columns([
        lambda: st.checkbox("Gross Returns", key=ss.rent_use_gross_returns.key),
    ], 1)
    populate_columns([
        lambda: dollar_input("Renting Cost", ss.rent_exp.key),
    ], 1)


def run_simulation():
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.
    """

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_price = get_monthly_pmi(ss.home_price.val, LOAN_AMOUNT, ss.pmi_rate.val, ss.home_price.val)
    property_tax_exp = ss.home_price.val * ss.yr_property_tax_rate.val / 12
    insurance_exp = ss.home_price.val * ss.yr_insurance_rate.val / 12
    maintenance_exp = ss.mo_maintenance.val
    hoa_exp = ss.mo_hoa_fees.val
    utility_exp = ss.mo_utility.val
    rent_income = ss.mo_rent_income.val
    other_income = ss.mo_other_income.val
    management_exp = ss.management_rate.val * rent_income
    rent_exp = ss.rent_exp.val

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    loan_balance = LOAN_AMOUNT
    home_value = ss.home_price.val
    pmi_required = pmi_price > 0
    stock_value = OOP


    data = []
    for month in np.arange(12 * 30):

        interest_exp = loan_balance * ss.interest_rate.val / 12
        
        # if youre paying more principle than scheduled...
        # cant pay more principal than loan balance
        principal_exp = MONTHLY_PAYMENT - interest_exp
        if principal_exp >= loan_balance:
            principal_exp = loan_balance

        loan_balance -= principal_exp

        # pay pmi if required
        pmi_exp = 0
        if pmi_required:
            pmi_exp = pmi_price


        # if rent covers all cost, pay extra towards the principle
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


        # should additional cash flow pay down loan or flow into stock portfolio?
        noi = adj_total_income - op_exp
        niaf = adj_total_income - total_exp

        # This is the fraction of the principle you have to cover, if income doesnt cover principle.
        # This value should be subtracted from ROI because you are paying for it, not the tenant.
        # This is earned equity that isnt a return, its just a payment.
        principal_makeup = 0
        if adj_total_income < principal_exp:
            principal_makeup = principal_exp - adj_total_income

        if niaf > 0 and ss.include_selling_costs.val:
            niaf *= (1 - INCOME_TAX_RATE)

        # optionally use niaf to pay down loan
        if niaf > 0 and ss.paydown_with_profit.val:
            if niaf > loan_balance:
                loan_balance = 0
            else:
                loan_balance -= niaf

        # update home value
        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = true_pmi > 0

        # update stock portfolio
        stock_value = add_growth(stock_value, STOCK_GROWTH_RATE, months=1)
        stock_contrib = 0
        if total_exp > rent_exp:
            stock_value += total_exp - rent_exp
            stock_contrib = total_exp - rent_exp
            

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # costs, payments, revenue. Totals over the month
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
            "principal_makeup": principal_makeup, # need a different name?
            "adj_total_income": adj_total_income,
            "noi": noi,
            "niaf": niaf,
            "rent_exp": rent_exp,
            "stock_contrib": stock_contrib,
            # balances and values. End of month
            "loan_balance": loan_balance,
            "home_value": home_value,
            "stock_value": stock_value,
        }
        data.append(month_data)

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_exp = home_value * ss.yr_property_tax_rate.val / 12
            insurance_exp = home_value * ss.yr_insurance_rate.val / 12
            hoa_exp = add_growth(hoa_exp, ss.yr_inflation_rate.val, 12)
            utility_exp = add_growth(utility_exp, ss.yr_inflation_rate.val, 12)
            maintenance_exp = add_growth(maintenance_exp, ss.yr_inflation_rate.val, 12)
            pmi_price = true_pmi
            rent_income = add_growth(rent_income, ss.yr_rent_increase.val, 12)
            other_income = add_growth(other_income, ss.yr_rent_increase.val, 12)
            management_exp = ss.management_rate.val * rent_income
            rent_exp = add_growth(rent_exp, ss.yr_rent_increase.val, 12)

    return pd.DataFrame(data).set_index("index")


def post_process_sim_df(sim_df):
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
            "rent_exp",
            "stock_contrib",
            "principal_makeup"
    ]

    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}

    agg_dict.update({
        "home_value": 'max', # end of year is max
        "loan_balance": 'min', # end of year is min
        "stock_value": 'max'
    })

    year_df = sim_df.groupby("year").agg(agg_dict)
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    year_df.rename(columns={
        "home_value_max": "home_value",
        "loan_balance_min": "loan_balance",
        "stock_value_max": "stock_value"
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
    
    cumsum_cols = [
        "niaf",
        "rent_exp",
        "principal_exp",
        "stock_contrib",
        "principal_makeup"
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # TODO. Selling tax, realtor fees, other sellings fees are an optional addition?

    # calculating "effective" equity by factoring in the price of selling the home.
    # are there other exit strategies that should be considered?
    year_df["equity"] = year_df["home_value"] - year_df["loan_balance"] 
    
    if ss.include_selling_costs.val:
        year_df["equity"] = year_df["equity"] - (year_df["home_value"] * REALTOR_RATE)
    
    # total return exludes the down payment, and any makeup to cover the principle. These is not a 
    # gain because they are not paid by the tenant
    year_df["total_return"] = year_df["equity"] + year_df["cum_niaf"] - ss.down_payment.val - year_df["cum_principal_makeup"]
    year_df["coc_roi"] = year_df["cum_niaf"] / OOP
    year_df["roi"] = year_df["total_return"] / OOP
    # analogously, rent total return excludes the OOP and additional contributions.
    # i.e. these things are not a "gain" in the same way that the down payment is not a gain.
    # additionally, remove taxes paid when cashing out the stock portfolio.
    year_df["total_return_rent"] = (
        year_df["stock_value"]
        - year_df["cum_rent_exp"]
        - year_df["cum_stock_contrib"]
        - OOP
    )

    if ss.include_selling_costs.val:
        year_df["total_return_rent"] = year_df["total_return_rent"] - (year_df["stock_value"] * STOCK_TAX_RATE)
    
    year_df["roi_rent"] = year_df["total_return_rent"] / OOP

    # TODO show tooltip that gives the numbers going into the ROI for each bullet point
    return year_df


def dict_to_metrics(data_dict, title):
    keys = list(data_dict.keys())
    values = list(data_dict.values())

    cells = dict(
        values=[keys, values],
        #line_color='rgba(0,0,0,0)',
        fill_color='rgba(255,255,255,0)'
    )

    header = dict(
        line_color="rgba(0,0,0,0)",
        fill_color='rgba(255,255,255,0)',
        height=0
    )

    fig = go.Figure(data=[go.Table(
        header=header,
        cells=cells,
    )])

    fig.update_layout(
        margin=dict(l=0, r=0, t=0, b=0),
        height=300,
        width=300,
    )

    st.container(height=20, border=False)
    st.write(title)
    st.plotly_chart(fig)
    #fig_display(fig)


def get_mortgage_metrics(df):
    return {
        "Down Payment": format_currency(ss.down_payment.val),
        "Rehab": format_currency(ss.rehab.val),
        "Closing Costs": format_currency(CLOSING_COSTS),
        "Total": format_currency(OOP),
        "Loan Amount": format_currency(LOAN_AMOUNT),
        "Total Interest Paid": format_currency(df["interest_exp"].sum()),
        "Total PMI Paid": format_currency(df["pmi_exp"].sum()),
        "Total Taxes Paid": format_currency(df["property_tax_exp"].sum()),
    }


def get_investment_metrics(df):
    # opr_metrics. Monthly gross income / OOP
    opr = df.loc[0, "rent_income_mo"] / OOP
    formatted_opr = format_percent(opr)
    return  {
        "GRM": round(df.loc[0, "home_value"] / df.loc[0, "rent_income"]),
        "Cap Rate": format_percent(df.loc[0, "noi"] / ss.home_price.val),
        "Mo Cash Flow (NIAF)": format_currency(df.loc[0, "niaf_mo"]),
        "Year One ROI": format_percent(df.loc[0, "roi"]),
        "Year Ten ROI": format_percent(df.loc[9, "roi"]),
        "1% Rule": f"Yes {formatted_opr}" if opr >= 0.01 else f"No {formatted_opr}",
    }


def get_tab_columns():
    col1, _, col2 =  st.columns([2, .5, 5])
    return col2, col1


def run_calculator():
    local_css("./mortgage_calculator/style.css")

    st.title("Uncompromising Mortgage Calculator")

    if not ss.hide_text.val:
        with st.expander("Introduction", expanded=True):
            st.write("""
                    \tThis is more than a mortgage calculator. Its a mortgage and real estate investment 
                    simulator that runs a month over month simluation accounts for all factors and the 
                    interplay between them. It accounts for all expenses, rental income, reinvestment, 
                    economic factors, taxes and fees, house hacking scenarios, and includes a novel rent vs 
                    own comparison accounting for opprtunity costs and house hacking income. Newbies and 
                    real estate investors alike can use this tool to make informed decisions.""")
            st.header("Use Cases")
            st.write("""
                    - What are all the short and long term costs of owning a home?
                    - Should I continue to rent or buy a home?
                    - Whats the impact of economic factors like interest rates, home appreciation, and 
                    inflation?
                    - How good are the returns on this rental property?
                    - How much of my costs can I offset by house hacking?
                    - How do my mortgage payments change if I pay down the loan with rental income?
                    """)
            st.header("Getting Started")
            st.write("""
                    Fill out the field in sidebar and click calculate. Input fields are organized into 
                    logical groups. Many inputs are filled with reasonable defaults. Look at field tooltips 
                    for more information about this field and the impact on the simlulation. For in depth 
                    details on how this simulator runs, term definitions, formulas, and for more tips, navigate to the 'About' tab in 
                    the main screen.
                    """)
            st.header("Tips")
            st.write("""
                    All text blocks and explanations can be removed by clicking the 'Hide All Text Blobs' in 
                    the side bar. Hover over charts to see exact values, or click and drag to zoom in on a 
                    particular area. You can collapse the sidebar by clicking the x in the top right corner 
                    of the sidebar. 
                    """)

    
    with st.sidebar:
        #calculate_inputs()
        st.markdown("### Input Fields")
        mortgage_inputs()
        expenses_inputs()
        economic_factors_inputs()
        rent_income_inputs()
        selling_fees_inputs()
        hide_text_input()

    yearly_df = post_process_sim_df(run_simulation())

    (
        tab_exp, 
        tab_exp_over_time, 
        tab_home_value,
        tab_returns,
        tab_net_income, 
        tab_rent_vs_own,
        #data_table,
        about
    ) = st.tabs([ 
        "Expenses First Year", 
        "Expenses Over Time", 
        "Home Value",
        "Returns",
        "Net Income",
        "Rent vs Own",
        #"Data Table",
        "About"
    ])

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
                showlegend=False, height=700,
            )

            fig_display(fig)

        with col2:
            dict_to_metrics(get_mortgage_metrics(yearly_df), title="Mortgage Metrics")


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
                height=700,
                xaxis=dict(title='Year', tickmode='array', tickvals=np.arange(5, 31, 5)),
            )

            fig.update_xaxes(range=[0, 31])
            fig_display(fig)

        with col2:
            dict_to_metrics(get_mortgage_metrics(yearly_df), title="Mortgage Metrics")


    with tab_home_value:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["home_value", "equity"]
            names= ["Home Value", "Equity"]
            colors = ['#1f77b4', '#ff7f0e', '#d62728']
            title = "Home Value   <i>&</i>   Equity"
            plot_dots(yearly_df, cols, names, colors, title, percent=False)

        with col2:
            dict_to_metrics(get_mortgage_metrics(yearly_df), title="Mortgage Metrics")

    with tab_net_income:
        col1, col2 = get_tab_columns()
        
        # add monthly vs yearly toggle?
        with col1:
            cols = ["noi_mo", "niaf_mo"]
            names= ["Monthly NOI", "Monthly NIAF"]
            colors = ['#1f77b4', '#ff7f0e']
            title = "Monthly Net Income"
            plot_dots(yearly_df, cols, names, colors, title, percent=False)
        with col2:
            dict_to_metrics(get_investment_metrics(yearly_df), title="Investment Metrics")

    with tab_returns:        
        col1, col2 = get_tab_columns()
        
        with col1:
            if ss.use_gross_returns.val:
                cols = ["total_return", "cum_niaf"]
                names= ["Total Return", "Total Cash Flow"]
                colors = ['#d62728', "#ff7f0e"]
                title = "Total Return (Gross)"
                plot_dots(yearly_df, cols, names, colors, title, percent=False)
            else:
                cols = ["roi", "coc_roi"]
                names= ["ROI", "COC ROI"]
                colors = ['#1f77b4', '#ff7f0e']
                title = "Total Return (ROI)"
                plot_dots(yearly_df, cols, names, colors, title, percent=True)

        with col2:
            dict_to_metrics(get_investment_metrics(yearly_df), title="Investment Metrics")
            returns_inputs()

    with tab_rent_vs_own:
        col1, col2 = get_tab_columns()

        with col1:
            if ss.rent_use_gross_returns.val:
                cols = ["total_return", "total_return_rent"]
                names= ["Own (Gross)", "Rent (Gross)"]
                colors = ['#d62728', '#ff7f0e']
                title = "Rent vs Own Total Return (Gross)"
                plot_dots(yearly_df, cols, names, colors, title, percent=False)
            else:
                cols = ["roi", "roi_rent"]
                names= ["Own (ROI)", "Rent (ROI)"]
                colors = ['#1f77b4', '#ff7f0e']
                title = "Rent vs Own Total Return (ROI)"
                plot_dots(yearly_df, cols, names, colors, title, percent=True)
        with col2:
            dict_to_metrics({"TODO": "TODO"}, title="Investment Metrics")
            rent_returns_inputs()

    # with data_table:
    #         # default_cols = [
    #         #     "interest_exp",
    #         #     "principal_exp",
    #         #     "op_exp",
    #         #     "total_exp",
    #         #     "adj_total_income",
    #         #     "niaf",
    #         #     "rent_exp",
    #         #     "stock_contrib",
    #         #     "principal_makeup",
    #         #     "home_value",
    #         #     "loan_balance",
    #         #     "stock_value",
    #         #     "cum_niaf",
    #         #     "cum_principal_exp",
    #         #     "cum_stock_contrib",
    #         #     "cum_principal_makeup",
    #         #     "equity",
    #         #     "total_return",
    #         #     "coc_roi",
    #         #     "roi",
    #         #     "total_return_rent",
    #         # ]

    #         # TODO differentiate principle_exp and principal_makeup

    #         column_groups = {
    #             'monthly_expenses': [
    #                 "interest_exp_mo", "principal_exp_mo", "property_tax_exp_mo",
    #                 "insurance_exp_mo", "hoa_exp_mo", "maintenance_exp_mo",
    #                 "pmi_exp_mo", "utility_exp_mo", "management_exp_mo",
    #                 "op_exp_mo", "total_exp_mo",
    #             ],
    #             'yearly_expenses': [
    #                 "interest_exp", "principal_exp", "property_tax_exp",
    #                 "insurance_exp", "hoa_exp", "maintenance_exp",
    #                 "pmi_exp", "utility_exp", "management_exp",
    #                 "op_exp", "total_exp",
    #             ],
    #             'monthly_income': [
    #                 "rent_income_mo", "other_income_mo", "total_income_mo",
    #                 "adj_total_income_mo",
    #             ],
    #             'yearly_income': [
    #                 "rent_income", "other_income", "total_income",
    #                 "adj_total_income",
    #             ],
    #             'rental_comparison': [
    #                 "rent_exp", "rent_exp_mo", "stock_contrib",
    #                 "stock_contrib_mo", "stock_value", "total_return_rent",
    #                 "roi_rent",
    #             ],
    #             'net_income_monthly': [
    #                 "noi_mo", "niaf_mo",
    #             ],
    #             'net_income_yearly': [
    #                 "noi", "niaf",
    #             ],
    #             'home_returns': [
    #                 "home_value", "loan_balance", "equity",
    #                 "total_return", "coc_roi", "roi",
    #             ],
    #             'other_expenses': [
    #                 "principal_makeup", "principal_makeup_mo",
    #             ],
    #             'cumulative': [
    #                 "cum_niaf", "cum_rent_exp", "cum_principal_exp",
    #                 "cum_stock_contrib", "cum_principal_makeup",
    #             ]
    #         }

    #         #tuples = [(category, column) for category, columns in column_groups.items() for column in columns]
    #         #new_column_order = [column for _, column in tuples if column in df.columns]

    #         categories = list(column_groups.keys())

    #         #selected_columns = st.multiselect('Select columns to display:', yearly_df.columns, default=default_cols)
    #         selected_categories = st.multiselect('Select columns to display:', categories, default=categories)
            
    #         selected_columns = [column for category in selected_categories for column in column_groups[category]]
            
    #         round_columns = [x for x in selected_columns if "roi" not in x]
    #         filtered_df = yearly_df[selected_columns]
    #         filtered_df.loc[: ,round_columns] = filtered_df.loc[: ,round_columns].round()
    #         st.dataframe(filtered_df, use_container_width=True)

    with about:
        st.write("More to come!")

run_calculator()
