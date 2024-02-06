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

CLOSING_COSTS = ss.home_price.val * ss.closing_costs_rate.val
OOP = CLOSING_COSTS + ss.down_payment.val + ss.rehab.val
LOAN_AMOUNT = ss.home_price.val - ss.down_payment.val
MONTHLY_PAYMENT = get_amortization_payment(LOAN_AMOUNT, ss.interest_rate.val)

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
        populate_columns([
            lambda: st.checkbox("Paydown Loan with Profit", key=ss.paydown_with_profit.key),
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


def calculate_inputs():
    populate_columns([
        lambda: st.button("Reset Inputs", on_click=ss.clear),
        #lambda: st.button("Calculate"),
    ], 2)


def chart_inputs():
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
    
    loan_balance = LOAN_AMOUNT
    home_value = ss.home_price.val
    pmi_required = pmi_price > 0
    stock_value = OOP


    data = []
    for month in np.arange(12 * 30):

        interest_exp = loan_balance * ss.interest_rate.val / 12

        # if youre ahead on payments, you cant pay more principal than the loan balance
        principal_exp = MONTHLY_PAYMENT - interest_exp
        if principal_exp >= loan_balance:
            principal_exp = loan_balance

        loan_balance -= principal_exp

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

        # optionally use niaf to pay down loan
        if niaf > 0 and ss.paydown_with_profit.val:
            niaf *= (1 - ss.income_tax_rate.val)
            if niaf > loan_balance:
                loan_balance = 0
            else:
                loan_balance -= niaf

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = true_pmi > 0

        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)
        stock_value = add_growth(stock_value, ss.stock_growth_rate.val, months=1)
        stock_contrib = 0
        if total_exp > rent_exp:
            stock_value += total_exp - rent_exp
            stock_contrib = total_exp - rent_exp


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
            "stock_contrib": stock_contrib,
            # Balances and values. End of month.
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
            maintenance_exp = home_value * ss.yr_maintenance.val / 12
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
            "stock_contrib"
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
    ]

    for col in cumsum_cols:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    year_df["equity"] = year_df["home_value"] * (1 - ss.realtor_rate.val) - year_df["loan_balance"] 
    year_df["coc_roi"] = year_df["cum_niaf"] / OOP
    year_df["profit"] = year_df["cum_niaf"] + year_df["equity"] - ss.rehab.val - CLOSING_COSTS
    year_df["roi"] = year_df["profit"] / OOP
    year_df["renting_profit"] = year_df["stock_value"] * (1- ss.capital_gains_tax_rate.val) - year_df["cum_rent_exp"]
    year_df["ownership_upside"] = year_df["profit"] - year_df["renting_profit"]

    return year_df


def get_mortgage_metrics(df):
    return {
        #"Down Payment": format_currency(ss.down_payment.val),
        #"Rehab": format_currency(ss.rehab.val),
        #"Closing Costs": format_currency(CLOSING_COSTS),
        "Cash Outlay": format_currency(OOP),
        "Loan Amount": format_currency(LOAN_AMOUNT),
        "Total Interest Paid": format_currency(df["interest_exp"].sum()),
        "Total PMI Paid": format_currency(df["pmi_exp"].sum()),
        "Total Taxes Paid": format_currency(df["property_tax_exp"].sum()),
    }


def get_investment_metrics(df):
    # opr_metrics. Monthly income / OOP
    opr = df.loc[0, "rent_income_mo"] / OOP
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


def get_rental_comparison_metrics(df):
    return {
        "One Year Ownership Upside": format_currency(df.loc[0, "profit"] - df.loc[0, "renting_profit"]),
        "Ten Year Ownership Upside": format_currency(df.loc[9, "profit"] - df.loc[9, "renting_profit"]),
    }


def run_calculator():
    yearly_df = post_process_sim_df(run_simulation())

    (
        tab_exp, 
        tab_exp_over_time, 
        tab_home_value,
        tab_roi,
        tab_profits,
        #tab_net_income, 
        tab_rent_vs_own,
        tab_rent_vs_own_delta,
        #data_table,
        about
    ) = st.tabs([ 
        "Expenses First Year", 
        "Expenses Over Time", 
        "Home Value",
        "ROI",
        "Profit",
        #"Net Income",
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
            dict_to_metrics(get_mortgage_metrics(yearly_df))


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
            dict_to_metrics(get_mortgage_metrics(yearly_df))


    with tab_home_value:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["home_value", "equity"]
            names= ["Home Value", "Equity"]
            colors = [BLUE, ORANGE]
            title = "Home Value   <i>&</i>   Equity"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val, percent=False)

        with col2:
            dict_to_metrics(get_mortgage_metrics(yearly_df))

    # with tab_net_income:
    #     col1, col2 = get_tab_columns()
        
    #     # add monthly vs yearly toggle?
    #     with col1:
    #         cols = ["noi_mo", "niaf_mo"]
    #         names= ["Monthly NOI", "Monthly NIAF"]
    #         colors = ['#1f77b4', '#ff7f0e']
    #         title = "Monthly Net Income"
    #         plot_dots(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
    #     with col2:
    #         dict_to_metrics(get_investment_metrics(yearly_df), title="Investment Metrics")

    with tab_roi:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["roi", "coc_roi"]
            names= ["ROI", "Cash on Cash ROI"]
            colors = [BLUE, ORANGE]
            title = "Return on Investment (ROI)"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=True)

        with col2:
            dict_to_metrics(get_investment_metrics(yearly_df))


    with tab_profits:
        col1, col2 = get_tab_columns()
        
        with col1:
            cols = ["profit", "cum_niaf"]
            names= ["Total Profit (With Equity)", "Total Cash"]
            colors = [BLUE, ORANGE]
            title = "Investment Profit/Loss"
            plot_data(yearly_df, cols, names, colors, title, HEIGHT, WIDTH, ss.xlim.val, mode=ss.chart_mode.val,percent=False)
        with col2:
            dict_to_metrics(get_investment_metrics(yearly_df))

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
            dict_to_metrics(get_rental_comparison_metrics(yearly_df))
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
            dict_to_metrics(get_rental_comparison_metrics(yearly_df))


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



def display_inputs():
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
        calculate_inputs()
        st.markdown("### Input Fields")
        mortgage_inputs()
        expenses_inputs()
        economic_factors_inputs()
        rent_income_inputs()
        selling_inputs()
        chart_inputs()

    run_calculator()


display_inputs()