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


# CONSTANTS
CLOSING_COSTS = ss.home_price.val * ss.closing_costs_rate.val
EFFECTIVE_DOWN_PAYMENT = max(ss.down_payment.val - CLOSING_COSTS, 0)
LOAN_AMOUNT = ss.home_price.val - EFFECTIVE_DOWN_PAYMENT
MONTHLY_PAYMENT = get_monthly_payment_amount(LOAN_AMOUNT, ss.interest_rate.val)
REALTOR_RATE = 0.06


def mortgage_inputs():
    st.markdown("### Mortgage")
    populate_columns([
        lambda: dollar_input("Home Price", ss.home_price.key,
            help="The price of the home you are considering purchasing."
        ),
    ], 2)
    populate_columns([
        lambda: dollar_input("Down Payment", ss.down_payment.key, 
            help="""The amount of cash you have to put towards the upfront costs of buying a home. 
            Closing costs will be subtracted from this value and the remainder is the effective 
            down payment."""
        ),
        lambda: rate_input("Interest", ss.interest_rate.key, 
            help="""The interest rate on your mortgage. Each month, this percentage is multiplied 
            by the remaining loan balance to calculate the interest payment."""
        ),
    ], 2)
    populate_columns([
        lambda: rate_input("Home Value Growth", ss.yr_home_appreciation.key, asterisk=False, 
            help="""The yearly increase in the value of your home. As your home increases in value, 
            you'll have to pay more in property taxes and insurance. This value is updated whenever
            you select a new region and corresponds to the median yearly home value increase over 
            the past 10 years in that region"""
        ),
        lambda: rate_input("Property Tax", ss.yr_property_tax_rate.key, asterisk=False, 
            help="""This is the tax rate on your property. Property tax rates are set by the state 
            government. This rate is multiplied by the value of the home to get the total taxes paid 
            each year. This value is updated whenever you select a new region and corresponds to the 
            median property tax rate in the state in which this region is located."""
        ),
    ], 2)
    populate_columns([
        lambda: dollar_input("HOA Fees", ss.mo_hoa_fees.key,
            help="""If your home is part of a homeowners association, you will have to pay monthly
            HOA fees. This value is updated each year based on the inflation rate."""
        ),
            lambda: rate_input("Insurance Rate", ss.yr_insurance_rate.key,
            help="""This is the yearly cost of homeowners insurance. This rate is multiplied by the
            value of the home to get the total insurance paid each year. Insurance rates can vary
            based on the location of the home and the type of insurance coverage.""",
        ),
    ], 2)


def other_inputs():
    with st.expander("Mortgage+", expanded=False):
        st.write("The defaults here will probably work for most people")
        populate_columns([
            lambda: rate_input("Closing Costs", ss.closing_costs_rate.key, 
                help="""These are the additional upfront cost of buying a home through a lender. 
                Its often calculated as a percentage of the purchase price of the home. The closing costs
                will be subracted from your down payment to calculate the effective down payment."""
                ),
            lambda: rate_input("PMI Rate", ss.pmi_rate.key, 
                help="""PMI is an additional monthly cost that is required if your down payment is less
                than 20% of the purchase price of the home. This rate is multiplied by the value of the
                home to get the total PMI paid each year. PMI can be cancelled once you have 20% equity in the home
                which can occur from paying down the principle or from the value of the home increasing."""
                ),
        ], 2)
        populate_columns([
            lambda: rate_input("Inflation Rate", ss.yr_inflation_rate.key,
                help="""This is the yearly inflation rate which measure how the cost of goods goes 
                up. This rate is used to update the value of your monthly maintenance and HOA fees 
                each year."""
            ),
            lambda: dollar_input("Monthly Maintenance", ss.mo_maintenance.key,
                help="""Owning a home requires maintenance and upkeep. This is the monthly cost of
                maintaining your home. This value is updated each year based on the inflation rate."""
            ),     
        ], 2)


def extra_mortgage_payment_inputs():
    with st.expander("Extra Payments", expanded=False):
        st.write("Extra payments can help you pay off your loan faster and reduce the total amount of interest you pay over the life of the loan.")
        populate_columns([
            lambda: dollar_input("Extra Monthly Payments", ss.mo_extra_payment.key,
            help="""This is the amount of extra money you will pay towards the principle of your loan
            each month. This can help you pay off your loan faster and reduce the total amount of
            interest you pay over the life of the loan."""                     
            ),
            lambda: st.number_input("Number of Payments", min_value=0, max_value=int(1e4), key=ss.num_extra_payments.key,
            help="""This is the number of months you will pay extra payments towards the principle of
            your loan. After this number of months, you will stop paying extra payments and only pay
            the normal monthly payment."""
            ),
        ], 2)


def rent_income_inputs():
    with st.expander("Rental Income", expanded=False):
        st.write("You can rent out all or a portion of your home to offset the cost of homeownership or make some profit.")
        populate_columns([
            lambda: dollar_input("Monthly Rental Income", ss.mo_rent_income.key,
                help="""This is the monthly cost of renting a home. This value is updated each year
                based on the yearly rent increase rate."""      
            ),
            lambda: rate_input("Yearly Rent Increase", ss.yr_rent_increase.key,
                help="""This is the yearly increase in the cost of rent. This value is used to update
                the monthly rent each year."""
            ),
        ], 2)


def calculate():
    populate_columns([
        lambda: st.button("Reset Values", on_click=ss.clear, help="Reset all inputs to their default values."),
        lambda: st.button("Calculate", help="Run the simulation with the current inputs."),
    ], 2)


def hide_text_input():
    populate_columns([
        lambda: st.checkbox("Hide All Text Blobs", key=ss.hide_text.key),
    ], 2)



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
    hoa_exp = ss.mo_hoa_fees.val
    rent_income = ss.mo_rent_income.val

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    maintenance_exp = ss.mo_maintenance.val
    loan_balance = LOAN_AMOUNT
    home_value = ss.home_price.val
    pmi_required = pmi_price > 0


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
        opex = (
            property_tax_exp +
            insurance_exp +
            hoa_exp +
            maintenance_exp +
            pmi_exp
        )
        total_expense = opex + interest_exp + principal_exp


        # should additional cash flow pay down loan or flow into stock portfolio?
        niaf = rent_income - total_expense
        if niaf > 0:
            loan_balance -= niaf

        # update home value
        home_value = add_growth(home_value, ss.yr_home_appreciation.val, months=1)

        # update monthly maintenance costs
        maintenance_exp = add_growth(maintenance_exp, ss.yr_inflation_rate.val, months=1)

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ss.pmi_rate.val, ss.home_price.val)
        pmi_required = true_pmi > 0

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_exp = home_value * ss.yr_property_tax_rate.val / 12
            insurance_exp = home_value * ss.yr_insurance_rate.val / 12
            hoa_exp = add_growth(hoa_exp, ss.yr_inflation_rate.val, 12)
            pmi_price = true_pmi
            rent_income = add_growth(rent_income, ss.yr_rent_increase.val, 12)

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # costs, payments, revenue
            "interest_exp": interest_exp,
            "principal_exp": principal_exp,
            "property_tax_exp": property_tax_exp,
            "insurance_exp": insurance_exp,
            "hoa_exp": hoa_exp,
            "maintenance_exp": maintenance_exp,
            "pmi_exp": pmi_exp,
            "opex": opex,
            "total_expense": total_expense,
            "rent_income": rent_income,
            "niaf": niaf,
            "noi": rent_income - opex,
            # balances and values
            "loan_balance": loan_balance,
            "home_value": home_value,
        }
        data.append(month_data)
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
            "opex",
            "total_expense",
            "rent_income",
            "niaf",
            "noi",
    ]

    # Generate aggregation dictionary
    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}

    agg_dict.update(
        {
            "home_value": 'max',
            "loan_balance": 'min' # min will be at end of year
        }
    )

    # Group and aggregate
    year_df = sim_df.groupby("year").agg(agg_dict)

    # Renaming columns for clarity
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    # cumulative cols for principal, interest, total, misc
    cols_to_cumsum = [
        "total_expense_sum", 
        "rent_income_sum",
        "niaf_sum",
    ]

    for col in cols_to_cumsum:
        year_df[f'cum_{col}'] = year_df[col].cumsum()


    year_df["noi"] = year_df["rent_income_sum"] - year_df["opex_sum"]
    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_min"] - year_df["home_value_max"] * REALTOR_RATE
    year_df["total_return"] = year_df["equity"] + year_df["cum_niaf_sum"]
    year_df["roi"] = year_df["total_return"] / ss.down_payment.val

    return year_df


def get_key_metrics(firs_year_df):
    return {
        "GRM": firs_year_df["home_value_max"] / firs_year_df["rent_income_sum"],
        "Cap Rate": firs_year_df["noi_mean"] / ss.home_price.val,
        "Monthly NIAF": firs_year_df["niaf_mean"],
        "First Year ROI": firs_year_df["roi"],
    }
    

def run_calculator():
    local_css("./mortgage_calculator/style.css")

    st.title("Uncompromising Mortgage Calculator")

    yearly_df = post_process_sim_df(run_simulation())

    yearly_df = yearly_df[[
        "home_value_max",
        "loan_balance_min",
        "equity",
        "total_expense_sum",
        "opex_sum",
        "rent_income_sum",
        "total_return",
        "roi",
    ]]

    st.write(yearly_df)

    return None

    st.write(yearly_df)

    first_year_df = yearly_df.loc[0:0, :]

    st.write(first_year_df)

    key_metrics = get_key_metrics(first_year_df)

    st.write(key_metrics)

    with st.sidebar:
        calculate()
        mortgage_inputs()
        other_inputs()
        #extra_mortgage_payment_inputs()
        rent_income_inputs()
        #hide_text_input()

    return None

    tab_mp, tab_mpot, tab_metrics = st.tabs([ 
        "Monthly Payment", 
        "Payments Over Time", 
        "Key Metrics"
    ])

    COLOR_MAP = {
            "interest_mean":      "#0068C9",  # Blue
            "principal_mean":     "#83C9FF",  # Light Blue
            "property_tax_mean":  "#FF2A2B",  # Red
            "insurance_mean":     "#FFABAB",  # Light Red
            "maintenance_mean":   "#7EEFA1",  # Green
            "hoa_mean":           "#2AB09D",  # Light Green
            "pmi_mean":           "#FF8700",  # Organe
            "extra_payment_mean": "#FFD16A",  # Light Orange
    }


    ########################################################################
    #      Pie                                                             #
    ########################################################################

    with tab_mp:
        if not ss.hide_text.val:
            get_monthly_intro()

        # get first row from yearly df
        row = yearly_df.loc[0:0, COLOR_MAP.keys()].T.reset_index().rename(columns={"index": "name", 0: "value"})

        # join col color map to get colors on the df
        row = row.join(pd.DataFrame.from_dict(COLOR_MAP, orient='index', columns=["color"]), on="name")

        # order pie_df by temp_color_map keys
        row['order'] = row['name'].apply(lambda x: list(COLOR_MAP.keys()).index(x))
        row = row.sort_values('order').drop('order', axis=1)

        # format dollar values for display values
        row["formatted_value"] = row["value"].apply(lambda x: format_currency(x))
        row["name"] = row["name"].apply(lambda x: format_label_string(x))
        
        # remove rows with zero values
        row = row[row["value"] > 0]

        rental_income_mean = yearly_df.loc[0:0, "rent_income_mean"].values[0]
        total_sum = row["value"].sum()
        net_sum = total_sum-rental_income_mean
        formatted_total_sum = format_currency(total_sum)
        formatted_net_sum = format_currency(net_sum)

        inner_pie_values = [rental_income_mean, net_sum]
        if net_sum < 0:
            inner_pie_values = [1, 0]

        data = []
        
        if rental_income_mean > 0:
            data.append(go.Pie(
                values=inner_pie_values, 
                labels=["Rental Income", "Net Cost"],
                marker_colors=['white', 'rgba(0,0,0,0)'],
                hole=0.55,
                direction ='clockwise', 
                sort=False,
                marker=dict(line=dict(color='#000000', width=2)),
                hoverinfo = 'none'
                )
            )

        data.append(go.Pie(
            values=row['value'].values, 
            labels=row['name'].values,
            marker_colors=row["color"].values,
            hole=0.6,
            direction ='clockwise', 
            sort=False,
            textposition='outside',
            text=row["formatted_value"], 
            textinfo='label+text',
            marker=dict(line=dict(color='#000000', width=2)),
            hoverinfo = 'none'
            )
        )
        
        fig = go.Figure(data=data)

        rent_income_annotation = dict(
            text=f"Rental Income<br>{format_currency(rental_income_mean)}", 
            x=0.51, y=0.74, ax=0, ay=40,
            showarrow=False, arrowhead=0,
            arrowcolor="white",arrowwidth=1.5,
        )

        totals_text = f"Total: {formatted_total_sum}"
        if ss.mo_rent_income.val > 0:
            totals_text = f"<i>Total: {formatted_total_sum}</i><br>Remainder: {formatted_net_sum}"

        totals_annotation = dict(
            text=totals_text, x=0.5, y=0.5, font_size=30, showarrow=False
        )

        annotations = [totals_annotation]
        if ss.mo_rent_income.val > 0:
            annotations.append(rent_income_annotation)

        fig.update_layout(
            showlegend=False, height=700,
            annotations=annotations,
            title="Average Monthly Costs in First Year"
        )

        fig_display(fig)


    ########################################################################
    #      Stacked Bar                                                     #
    ########################################################################

    with tab_mpot:
        if not ss.hide_text.val:
            get_monthly_over_time_intro()

        zero_sum_cols = [k for k in COLOR_MAP.keys() if yearly_df[k].sum() == 0]
        COLOR_MAP = {k: v for k, v in COLOR_MAP.items() if k not in zero_sum_cols}

        fig = go.Figure()
        for col, color in COLOR_MAP.items():
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
                y=yearly_df["rent_income_mean"], 
                mode='markers',
                #mode='lines',
                name="Rental Income",
                hoverinfo='y',
                hovertemplate='$%{y:,.0f}',
                marker=dict(size=10, color='white'),
            ))

            fig.add_trace(go.Scatter(
                x=yearly_df.index + 1, 
                y=yearly_df["total_mean_hh"], 
                mode='lines',
                name="Total Cost after Rental Income",
                hoverinfo='y',
                hovertemplate='$%{y:,.0f}',
                line=dict(width=4, color='white'),
            ))

        yaxis_annotation = dict(
            text=f"Average Monthly Cost", 
            x=0.0, y=1, showarrow=False,
        )
            
        fig.update_layout(
            title="Average Monthly Costs Over Time",
            yaxis=dict(title='', tickformat='$,.0f'),
            barmode='stack',
            height=700,
            xaxis=dict(title='Year', tickmode='array', tickvals=np.arange(5, 31, 5)),
            xaxis_title_font=dict(size=15, color='white'),
            margin=dict(l=200, r=0, t=80, b=0),
        )

        fig.add_annotation(
            xref='paper', yref='paper',
            y=0.5, x=-0.23, # Position of the annotation
            text="Average<br>Monthly Cost", # Y-axis label text
            showarrow=False,
            font=dict(
                size=15,
                color="white"
            ),
            align="center"
        )

        fig.update_xaxes(range=[0, 31])
        fig_display(fig)


    ########################################################################
    #      Home Value                                                      #
    ########################################################################

    # with tab_hv:
    #     if not ss.hide_text.val:
    #         get_home_value_intro()
        
    #     # st.write(home_value_metrics)

    #     cols=["home_value_max", "equity", "equity_less_costs"]
    #     names=["Home Value", "Equity", "Profit"]
    #     colors = ['#1f77b4', '#ff7f0e', '#d62728']

    #     fig = go.Figure()

    #     for idx, (col, name) in enumerate(zip(cols, names)):
    #         fig.add_trace(go.Scatter(
    #             x=yearly_df.index + 1, 
    #             y=yearly_df[col], 
    #             mode='lines', 
    #             name=name,
    #             hoverinfo='y',
    #             hovertemplate='$%{y:,.0f}',
    #             line=dict(width=4, color=colors[idx]),
    #         ))

    #     if ss.mo_rent_income.val > 0:
    #         fig.add_trace(go.Scatter(
    #             x=yearly_df.index + 1, 
    #             y=yearly_df["equity_less_costs_hh"], 
    #             mode='lines', 
    #             name="Profit with Rental Income",
    #             hoverinfo='y',
    #             hovertemplate='$%{y:,.0f}',
    #             line=dict(width=4, color="#2ca02c"),
    #         ))

    #     fig.update_layout(
    #         title="Home Value and Equity Over Time",
    #         xaxis=dict(title='Year',),
    #         yaxis=dict(title='Value at End of Year', tickformat='$,.0f'),
    #         height=700,
    #         hovermode='x'
    #     )

    #     fig_display(fig)

    ########################################################################
    #      Summary                                                         #
    ########################################################################

    with tab_metrics:
        st.write(key_metrics)


run_calculator()