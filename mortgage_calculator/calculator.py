from math import *
from dataclasses import dataclass
from time import sleep

import streamlit as st
from streamlit import components
from streamlit import session_state as ssts
import numpy as np
import pandas as pd
import plotly.graph_objs as go
import plotly.express as px

from utils import *
from utils_finance import *
from st_text import *
from session_state_keys import Key
from utils_inputs import *


st.set_page_config(layout="wide")

@st.cache_data
def load_housing_data():
    return pd.read_csv('./mortgage_calculator/data/city_housing_data.csv')

housing_db = load_housing_data()

@st.cache_data
def get_region_options():
    return housing_db["region"].unique()

region_options = get_region_options()


@dataclass
class HousingDataLookup:
    med_price: float
    med_ppsf: float
    med_price_cagr: float
    med_ppsf_cagr: float
    tax_rate: float


def get_associated_data(region):
    row = housing_db[housing_db["region"] == region]
    return HousingDataLookup(
        row["median_sale_price"].values[0], 
        row["median_ppsf"].values[0],
        row["median_sale_price_cagr"].values[0],
        row["median_ppsf_cagr"].values[0],
        row["property_tax_rate"].values[0],
    )


def update_region():
    """Unique function for updating region because it has to change other values."""
    housing_data = get_associated_data(ssts[Key.region])
    #ssts[Key.init_home_value] = housing_data.med_price
    ssts[Key.yearly_home_value_growth] = housing_data.med_price_cagr * 100
    ssts[Key.property_tax_rate] = housing_data.tax_rate


def mortgage_inputs():
    st.markdown("### Mortgage Inputs")
    populate_columns([
        lambda: st.selectbox("Region", key=Key.region, options=region_options, on_change=update_region, 
            help="""Select a metro area, city, or zip code to lookup data for this region. Inputs 
            marked with a double asterisk (**) will be updated based on this selection."""
        ),
        lambda: dollar_input("Home Price", Key.init_home_value, 
            help="The price of the home you are considering purchasing."
        ),
    ], 2)
    populate_columns([
        lambda: dollar_input("Down Payment", Key.down_payment, 
            help="""The amount of cash you have to put towards the upfront costs of buying a home. 
            Closing costs will be subtracted from this value and the remainder is the effective 
            down payment."""
        ),
        lambda: rate_input("Interest", Key.interest_rate, 
            help="""The interest rate on your mortgage. Each month, this percentage is multiplied 
            by the remaining loan balance to calculate the interest payment."""
        ),
    ], 2)
    populate_columns([
        lambda: rate_input("Home Value Growth", Key.yearly_home_value_growth, asterisk=True, 
            help="""The yearly increase in the value of your home. As your home increases in value, 
            you'll have to pay more in property taxes and insurance. This value is updated whenever
            you select a new region and corresponds to the median yearly home value increase over 
            the past 10 years in that region"""
        ),
        lambda: rate_input("Property Tax", Key.property_tax_rate, asterisk=True, 
            help="""This is the tax rate on your property. Property tax rates are set by the state 
            government. This rate is multiplied by the value of the home to get the total taxes paid 
            each year. This value is updated whenever you select a new region and corresponds to the 
            median property tax rate in the state in which this region is located."""
        ),
    ], 2)


def other_inputs():
    with st.expander("Additional Mortgage Inputs", expanded=False):
        populate_columns([
            lambda: rate_input("Closing Costs", Key.closing_costs_rate, 
                help="""These are the additional upfront cost of buying a home through a lender. 
                Its often calculated as a percentage of the purchase price of the home. The closing costs
                will be subracted from your down payment to calculate the effective down payment."""
                ),
            lambda: rate_input("PMI Rate", Key.pmi_rate, 
                help="""PMI is an additional monthly cost that is required if your down payment is less
                than 20% of the purchase price of the home. This rate is multiplied by the value of the
                home to get the total PMI paid each year. PMI can be cancelled once you have 20% equity in the home
                which can occur from paying down the principle or from the value of the home increasing."""
                ),
        ], 2)
        populate_columns([
             lambda: rate_input("Insurance Rate", Key.insurance_rate,
                help="""This is the yearly cost of homeowners insurance. This rate is multiplied by the
                value of the home to get the total insurance paid each year. Insurance rates can vary
                based on the location of the home and the type of insurance coverage.""",
            ),  
            lambda: dollar_input("Monthly Maintenance", Key.init_monthly_maintenance,
                help="""Owning a home requires maintenance and upkeep. This is the monthly cost of
                maintaining your home. This value is updated each year based on the inflation rate."""
            ),     
        ], 2)
        populate_columns([
            lambda: dollar_input("HOA Fees", Key.init_hoa_fees,
                help="""If your home is part of a homeowners association, you will have to pay monthly
                HOA fees. This value is updated each year based on the inflation rate."""
            ),
            lambda: rate_input("Inflation Rate", Key.inflation_rate,
                help="""This is the yearly inflation rate which measure how the cost of goods goes 
                up. This rate is used to update the value of your monthly maintenance and HOA fees 
                each year."""
            )
        ], 2)


def extra_mortgage_payment_inputs():
    with st.expander("Extra Monthly Principal Payments", expanded=False):
        populate_columns([
            lambda: dollar_input("Extra Monthly Payments", Key.extra_monthly_payments,
            help="""This is the amount of extra money you will pay towards the principle of your loan
            each month. This can help you pay off your loan faster and reduce the total amount of
            interest you pay over the life of the loan."""                     
            ),
            lambda: st.number_input("Number of Payments", min_value=0, max_value=int(1e4), key=Key.number_of_payments,
            help="""This is the number of months you will pay extra payments towards the principle of
            your loan. After this number of months, you will stop paying extra payments and only pay
            the normal monthly payment."""
            ),
        ], 2)


def renting_comparison_inputs():
    with st.expander("Renting Comparison Inputs", expanded=False):
        populate_columns([
            lambda: dollar_input("Monthly Rent", Key.rent,
                help="""This is the monthly cost of renting a home. This value is updated each year
                based on the yearly rent increase rate."""      
            ),
            lambda: rate_input("Yearly Rent Increase", Key.rent_increase,
                help="""This is the yearly increase in the cost of rent. This value is used to update
                the monthly rent each year."""
            ),
        ], 2)
        populate_columns([
            lambda: rate_input("Stock Return Rate", Key.stock_growth_rate,
                help="""This is the yearly return rate of the stock market. This value is used to
                calculate the growth of your portfolio over time."""       
            )
        ], 2)


def rent_income_inputs():
    with st.expander("Rental Income / House Hacking Inputs", expanded=False):
        populate_columns([
            lambda: dollar_input("Monthly Rental Income", Key.rent_income,
                help="""This is the monthly cost of renting a home. This value is updated each year
                based on the yearly rent increase rate."""      
            ),
            lambda: rate_input("Yearly Rent Increase", Key.rent_income_growth,
                help="""This is the yearly increase in the cost of rent. This value is used to update
                the monthly rent each year."""
            ),
        ], 2)



def ssts_rate(key):
    return ssts[key] / 100


def initialize_session_state():
    if 'initialized' not in ssts:
        # app management
        ssts['initialized'] = True

        # user data
        ssts[Key.region] = region_options[0]
        housing_data = get_associated_data(region_options[0])

        #ssts[Key.init_home_value] = int(housing_data.med_price)
        ssts[Key.init_home_value] = 300000
        ssts[Key.down_payment] = 50000
        ssts[Key.interest_rate] = 7.0
        ssts[Key.yearly_home_value_growth] = housing_data.med_price_cagr * 100
        ssts[Key.property_tax_rate] = housing_data.tax_rate

        ssts[Key.closing_costs_rate] = 3.0
        ssts[Key.pmi_rate] = 0.5
        ssts[Key.insurance_rate] = 0.35
        ssts[Key.init_hoa_fees] = 0
        ssts[Key.init_monthly_maintenance] = 100
        ssts[Key.inflation_rate] = 3.0
        ssts[Key.extra_monthly_payments] = 0
        ssts[Key.number_of_payments] = 0

        ssts[Key.rent] = 1600
        ssts[Key.rent_increase] = 6.0
        ssts[Key.stock_growth_rate] = 8.0
        ssts[Key.stock_tax_rate] = 15.0

        ssts[Key.rent_income] = 500
        ssts[Key.rent_income_growth] = 3.0


def run_simulation():
    """
    Simulation iterates over months. Each row corresponds to the total costs paid for a particular
    expenses over the month, or the value of an asset at the end of the month. Row 0 corresponds to
    the end of the first month since closing.
    """

    ########################################################################
    #      set once, these dont change throughout the simulation           #
    ########################################################################

    # TODO, these should be saved at state initialization. Maybe. 
    # State is closely tied to inputs, not derived values, so maybe not.
    CLOSING_COSTS = ssts[Key.init_home_value] * ssts_rate(Key.closing_costs_rate)
    EFFECTIVE_DOWN_PAYMENT = max(ssts[Key.down_payment] - CLOSING_COSTS, 0)
    LOAN_AMOUNT = ssts[Key.init_home_value] - EFFECTIVE_DOWN_PAYMENT
    MONTHLY_PAYMENT = get_monthly_payment_amount(LOAN_AMOUNT, ssts_rate(Key.interest_rate))

    ########################################################################
    #      initialize, updated yearly                                      #
    ########################################################################
    
    pmi_cost = get_monthly_pmi(ssts[Key.init_home_value], LOAN_AMOUNT, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
    property_tax_cost = ssts[Key.init_home_value] * ssts_rate(Key.property_tax_rate) / 12
    insurance_cost = ssts[Key.init_home_value] * ssts_rate(Key.insurance_rate) / 12
    hoa_cost = ssts[Key.init_hoa_fees]
    rent_cost = ssts[Key.rent]
    portfolio_value = ssts[Key.down_payment]
    rent_income = ssts[Key.rent_income]

    ########################################################################
    #      initialize, updated monthly                                     #
    ########################################################################
    
    maintenance_cost = ssts[Key.init_monthly_maintenance]
    loan_balance = LOAN_AMOUNT
    home_value = ssts[Key.init_home_value]
    pmi_required = pmi_cost > 0
    extra_payment = ssts[Key.extra_monthly_payments]


    data = []
    for month in np.arange(12 * 30):

        interest_paid = loan_balance * ssts_rate(Key.interest_rate) / 12
        
        # cant pay more principal than loan balance
        principal_paid = MONTHLY_PAYMENT - interest_paid
        if principal_paid >= loan_balance:
            principal_paid = loan_balance

        loan_balance -= principal_paid

        # stop paying extra payments after allotted number of payments
        # cant pay more extra payments than loan balance
        if month > ssts[Key.number_of_payments] - 1:
            extra_payment = 0
        elif extra_payment >= loan_balance:
                extra_payment = loan_balance

        loan_balance -= extra_payment

        # pay pmi if required
        pmi_paid = 0
        if pmi_required:
            pmi_paid = pmi_cost

        # update portfolio value
        contribution = (
            interest_paid +
            principal_paid +
            extra_payment +
            property_tax_cost +
            insurance_cost +
            hoa_cost +
            maintenance_cost +
            pmi_paid
        ) - rent_cost

        contribution = max(contribution, 0)
        portfolio_value = add_growth(
            portfolio_value, 
            ssts_rate(Key.stock_growth_rate), 
            months=1, 
            monthly_contribution=contribution
        )

        # update home value
        home_value = add_growth(home_value, ssts_rate(Key.yearly_home_value_growth), months=1)

        # update monthly maintenance costs
        maintenance_cost = add_growth(maintenance_cost, ssts_rate(Key.inflation_rate), months=1)

        # update pmi_required, but dont update pmi cost unless its end of year
        true_pmi = get_monthly_pmi(home_value, loan_balance, ssts_rate(Key.pmi_rate), ssts[Key.init_home_value])
        pmi_required = true_pmi > 0

        # update yearly values at end of last month in each year
        if (month + 1) % 12 == 0 and month > 0:
            property_tax_cost = home_value * ssts_rate(Key.property_tax_rate) / 12
            insurance_cost = home_value * ssts_rate(Key.insurance_rate) / 12
            hoa_cost = add_growth(hoa_cost, ssts_rate(Key.inflation_rate), 12)
            rent_cost = add_growth(rent_cost, ssts_rate(Key.rent_increase), 12)
            pmi_cost = true_pmi
            rent_income = add_growth(rent_income, ssts_rate(Key.rent_income_growth), 12)

        month_data = {
            "index": month,
            "year": month // 12,
            "month": month % 12,
            # costs and payments
            "interest": interest_paid,
            "principal": principal_paid,
            "extra_payment": extra_payment,
            "property_tax": property_tax_cost,
            "insurance": insurance_cost,
            "hoa": hoa_cost,
            "maintenance": maintenance_cost,
            "pmi": pmi_paid,
            "rent": rent_cost,
            # balances and values
            "loan_balance": loan_balance,
            "home_value": home_value,
            "portfolio_value": portfolio_value,
            # house hacking / rental income
            "rent_income": rent_income,
        }
        data.append(month_data)
    return pd.DataFrame(data).set_index("index")


def post_process_sim_df(sim_df):
    """
    After running the simulation, we want to aggregate the data to a yearly level for easier
    analysis and visualization. This function also calculates some derived metrics related to 
    renting comparisons and rental income.
    """

    # add total and misc columns
    sim_df["total"] = sim_df[[
        "interest", "principal", "pmi", "insurance", 
        "property_tax", "hoa", "maintenance", "extra_payment"
    ]].sum(axis=1)

    sim_df["misc"] = sim_df[[
        "pmi", "insurance", "property_tax", 
        "hoa", "maintenance"
    ]].sum(axis=1)

    # List of columns for sum and mean aggregations
    sum_mean_cols = [
        "pmi", "insurance", "property_tax", "hoa", 
        "maintenance", "interest", "principal", 
        "misc", "total", "rent", "extra_payment",
        "rent_income"
    ]

    # Columns for max aggregation
    max_cols = ["home_value", "loan_balance", "portfolio_value"]

    # Generate aggregation dictionary
    agg_dict = {col: ['sum', 'mean'] for col in sum_mean_cols}
    agg_dict.update({col: 'max' for col in max_cols})

    # Group and aggregate
    year_df = sim_df.groupby("year").agg(agg_dict)

    # Renaming columns for clarity
    year_df.columns = [f"{col}_{func}" for col, func in year_df.columns]

    # total minus rental income
    year_df["total_mean_hh"] = year_df["total_mean"] - year_df["rent_income_mean"]

    # cumulative cols for principal, interest, total, misc
    cols_to_cumsum = ["total_sum", "interest_sum", "principal_sum", "extra_payment_sum", "misc_sum", "rent_sum", "rent_income_sum"]

    for col in cols_to_cumsum:
        year_df[f'cum_{col}'] = year_df[col].cumsum()

    # Define rates and costs upfront for clarity
    closing_costs = ssts_rate(Key.closing_costs_rate) * ssts[Key.init_home_value]

    # Calculate equity
    year_df["equity"] = year_df["home_value_max"] - year_df["loan_balance_max"]

    # money you pay that doesnt go towards equity
    year_df["home_costs"] = closing_costs + year_df["cum_interest_sum"] + year_df["cum_misc_sum"]
    year_df["equity_less_costs"] = year_df["equity"] - year_df["home_costs"]
    year_df["equity_less_costs_hh"] = year_df["equity"] - year_df["home_costs"] +  year_df["cum_rent_income_sum"]
    year_df["stocks_less_renting"] = year_df["portfolio_value_max"] - year_df["cum_rent_sum"]

    return year_df



def get_metrics(yearly_df):

    closing_costs = ssts[Key.init_home_value] * ssts_rate(Key.closing_costs_rate)
    effective_down_payment = max(ssts[Key.down_payment] - closing_costs, 0)
    loan_amount = ssts[Key.init_home_value] - effective_down_payment

    # total amount of interest paid with no extra payments
    default_interest_paid = get_total_interest_paid(loan_amount, ssts_rate(Key.interest_rate))
    actual_interest_paid = sum(yearly_df['interest_sum'])
    

    # find first year where equity minus costs is higher than previous year
    def year_of_uptrend(values):
        for i in range(len(values) - 1):
            if values[i + 1] > values[i]:
                return i + 1
        return 30
            

    def min_crossover(x, y):
        """Function that tells you at what index x is greater than y"""
        for i in range(len(x)):
            if x[i] > y[i]:
                return i
        return 30
    

    def format_values(metrics, exclude_keys=[]):
        for key in metrics:
            if key not in exclude_keys:
                metrics[key] = format_currency(metrics[key])

    home_value_tab_metrics = {
        "Years until Equity Increase > Costs": int(year_of_uptrend(yearly_df["equity_less_costs"])),
        "Increased Equity 5 Years": yearly_df["equity"].iloc[5] -  yearly_df["equity"].iloc[0],
        "Increased Equity 30 Years": yearly_df["equity"].iloc[-1] - yearly_df["equity"].iloc[0],
    }

    renting_tab_metrics = {
        "Years until Homeownership is Cheaper": min_crossover(yearly_df["equity_less_costs"], yearly_df["stocks_less_renting"]) + 1,
        "Homeownership upside 5 Years": yearly_df["equity_less_costs"].iloc[4] - yearly_df["stocks_less_renting"].iloc[4],
        "Homeownership upside 10 Years": yearly_df["equity_less_costs"].iloc[9] - yearly_df["stocks_less_renting"].iloc[9],
    }

    summary_metrics = {
        "Loan Amount": loan_amount,
        "Closing Costs": closing_costs,
        "Effective Down Payments": effective_down_payment,
        "Total Paid": sum(yearly_df['total_sum']),
        "Principal Paid": sum(yearly_df['principal_sum']),
        "Interest Paid": actual_interest_paid,
        "Taxes Paid": sum(yearly_df['property_tax_sum']),
        "Other Expenses Paid": sum(yearly_df['misc_sum']),
        "PMI Paid": sum(yearly_df['pmi_sum']),
        "Extra Payments": sum(yearly_df['extra_payment_sum']),
        "Interest Saved": max(0, default_interest_paid - actual_interest_paid),
    }

    format_values(summary_metrics)
    format_values(home_value_tab_metrics, ["Years until Equity Increase > Costs"])
    format_values(renting_tab_metrics, ["Years until Homeownership is Cheaper"])

    return summary_metrics, home_value_tab_metrics, renting_tab_metrics



def run_calculator():
    local_css("./mortgage_calculator/style.css")
    initialize_session_state()

    yearly_df = post_process_sim_df(run_simulation())

    summary_metrics, home_value_tab_metrics, renting_tab_metrics = get_metrics(yearly_df)

    with st.sidebar:
        mortgage_inputs()
        other_inputs()
        extra_mortgage_payment_inputs()
        renting_comparison_inputs()
        rent_income_inputs()

    tab_mp, tab_mpot, tab_hv, tab_rent, summary = st.tabs([ 
        "Monthly Payments", 
        "Monthly Payments Over Time", 
        "Home Value",
        "Rent Comparison",
        "Summary"
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

        col1, col2 = st.columns([4, 1])

        with col2:
            st.container(height=100, border=False)
            with st.container(height=110):
                st.metric(label="Average Monthly Total", value=formatted_total_sum, delta="")
            with st.container(height=110):
                st.metric(label="Adjusted for Rent Income", value=formatted_net_sum, delta="")

        with col1:

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
                marker=dict(line=dict(color='#000000', width=2))
                )
            )
            
            fig = go.Figure(data=data)

            if rental_income_mean > 0:
                fig.update_layout(
                    annotations=[dict(text=f"""Rental Income<br>{format_currency(rental_income_mean)}""", 
                                x=0.51, 
                                y=0.74,
                                ax=0,
                                ay=40,
                                showarrow=True, 
                                arrowhead=0,
                                arrowcolor="white",
                                arrowwidth=1.5,
                                )],
                )

            fig.update_layout(
                showlegend=False, height=700,
                #annotations=[dict(text=f"""Total: {formatted_total_sum}<br>Net: {formatted_net_sum}""", x=0.5, y=0.5, font_size=30, showarrow=False)],
                title="Average Monthly Costs in First Year"
            )

            fig_display(fig)


    ########################################################################
    #      Stacked Bar                                                     #
    ########################################################################

    with tab_mpot:
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
            
        if ssts[Key.rent_income] > 0:
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

        fig.update_layout(
            title="Average Monthly Costs Over Time",
            yaxis=dict(title='Average Monthly Cost', tickformat='$,.0f'),
            barmode='stack',
            height=700,
            xaxis=dict(title='Year', tickmode='array', tickvals=np.arange(5, 31, 5)),
        )

        fig.update_xaxes(range=[0, 31])
        fig_display(fig)


    ########################################################################
    #      Home Value                                                      #
    ########################################################################

    with tab_hv:
        get_home_value_intro()
        display_metrics_in_row(home_value_tab_metrics, 3)

        cols=["home_value_max", "equity", "equity_less_costs", "equity_less_costs_hh"]
        names=["Home Value", "Equity", "Equity minus Costs", "Equity minus Costs (House Hacking)"]
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']

        fig = go.Figure()

        for idx, (col, name) in enumerate(zip(cols, names)):
            fig.add_trace(go.Scatter(
                x=yearly_df.index + 1, 
                y=yearly_df[col], 
                mode='lines', 
                name=name,
                hoverinfo='y',
                hovertemplate='$%{y:,.0f}',
                line=dict(width=4, color=colors[idx]),
            ))

        fig.update_layout(
            title="Home Value and Equity Over Time",
            xaxis=dict(title='Year',),
            yaxis=dict(title='Value at End of Year', tickformat='$,.0f'),
            height=700,
            hovermode='x'
        )

        fig_display(fig)


    ########################################################################
    #      Renting                                                         #
    ########################################################################

    with tab_rent:
        get_rental_comparison_intro()
        display_metrics_in_row(renting_tab_metrics, 3)

        cols=["equity_less_costs", "stocks_less_renting"]
        names=["Equity minus Costs", "Stocks minus Renting"]
        colors = ['#2ca02c', 'red']

        fig = go.Figure()

        for idx, (col, name) in enumerate(zip(cols, names)):
            fig.add_trace(go.Scatter(
                x=yearly_df.index + 1, 
                y=yearly_df[col], 
                mode='lines', 
                name=name,
                hoverinfo='y',
                hovertemplate='$%{y:,.0f}',
                line=dict(width=4, color=colors[idx]),  # Use the color corresponding to the current index
            ))

        # Update layout
        fig.update_layout(
            title="Renting vs. Homeownership",
            xaxis=dict(
                title='Year',
            ),
            yaxis=dict(
                title='Value at End of Year',
                tickformat='$,.0f'
            ),
            height=700,
            hovermode='x'
        )

        # Display the figure
        fig_display(fig)


    ########################################################################
    #      Summary                                                         #
    ########################################################################

    with summary:
        st.write(pd.DataFrame(summary_metrics, index=[0]).T.rename(columns={0: "Amount"}))

run_calculator()